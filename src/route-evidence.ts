import { createHash } from 'node:crypto';
import type { TargetAdapter } from './adapter.js';
import { minimizeSequence, type MinimizeResult } from './minimize.js';
import { analyzeTerminalObservation } from './semantics.js';
import type { InputAction, RunReport, TargetManifest } from './types.js';

export type RouteKind = 'completion' | 'hidden';

export interface RouteRunner {
  run(manifest: TargetManifest, options: { actions: readonly InputAction[]; maxActions: number; maxElapsedMs?: number; signal?: AbortSignal }): Promise<RunReport>;
}

export interface RouteVerificationAttempt {
  attempt: number;
  matched: boolean;
  cleanupConfirmed: boolean;
  observationSignature: string;
}

export interface RouteVerification {
  kind: RouteKind;
  verified: boolean;
  attempts: number;
  requiredMatches: number;
  matches: number;
  actions: InputAction[];
  observationSignatures: string[];
  records: RouteVerificationAttempt[];
}

export interface VerifiedRouteRecord {
  id: string;
  kind: RouteKind;
  status: 'verified' | 'unverified';
  actions: InputAction[];
  originalLength: number;
  verificationAttempts: number;
  verificationMatches: number;
  observationSignatures: string[];
  minimizationAttempts: number;
  observedAt: string;
}

export interface VerifyRouteOptions {
  attempts?: number;
  requiredMatches?: number;
  maxElapsedMs?: number;
  signal?: AbortSignal;
  adapter?: TargetAdapter;
}

export interface MinimizeRouteOptions extends VerifyRouteOptions {
  candidateAttempts?: number;
  candidateRequiredMatches?: number;
  finalAttempts?: number;
  finalRequiredMatches?: number;
  maxMinimizationAttempts?: number;
}

const digest = (value: unknown): string => createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');

async function routeOutcome(report: RunReport, manifest: TargetManifest, kind: RouteKind, adapter?: TargetAdapter): Promise<{ matched: boolean; signature: string }> {
  const signatures: string[] = [];
  let matched = false;
  for (let index = 0; index < report.observations.length; index += 1) {
    const observation = report.observations[index]!;
    const semantic = analyzeTerminalObservation(observation);
    const actions = report.actions.slice(0, Math.min(index, report.actions.length));
    const evidence = adapter ? await adapter.analyze({ manifest, observation, semantic, observationIndex: index, actions }) : {};
    const tags = new Set([...semantic.tags, ...(evidence.tags ?? [])]);
    if (kind === 'completion' ? Boolean(evidence.completion || tags.has('completion')) : Boolean(evidence.hidden || tags.has('secret'))) matched = true;
    signatures.push(semantic.signature);
  }
  return { matched, signature: digest(signatures) };
}

export async function verifyRoute(runner: RouteRunner, manifest: TargetManifest, kind: RouteKind, actions: readonly InputAction[], options: VerifyRouteOptions = {}): Promise<RouteVerification> {
  const attempts = options.attempts ?? 3;
  const requiredMatches = options.requiredMatches ?? attempts;
  if (!Number.isSafeInteger(attempts) || attempts <= 0 || !Number.isSafeInteger(requiredMatches) || requiredMatches <= 0 || requiredMatches > attempts) throw new Error('Route verification quorum is invalid');
  if (options.adapter && options.adapter.targetId !== manifest.id) throw new Error('Route adapter target mismatch');
  const records: RouteVerificationAttempt[] = [];
  for (let attempt = 1; attempt <= attempts && !options.signal?.aborted; attempt += 1) {
    const report = await runner.run(manifest, { actions, maxActions: actions.length, maxElapsedMs: options.maxElapsedMs ?? manifest.episodeTimeoutMs, signal: options.signal });
    const outcome = await routeOutcome(report, manifest, kind, options.adapter);
    const cleanupConfirmed = report.cleanup.confirmedExited && !report.cleanup.error;
    records.push({ attempt, matched: outcome.matched && cleanupConfirmed, cleanupConfirmed, observationSignature: outcome.signature });
  }
  const matches = records.filter(record => record.matched).length;
  return {
    kind, verified: records.length === attempts && matches >= requiredMatches, attempts: records.length, requiredMatches, matches,
    actions: actions.map(action => ({ ...action })),
    observationSignatures: [...new Set(records.filter(record => record.matched).map(record => record.observationSignature))].sort(),
    records,
  };
}

export async function minimizeVerifiedRoute(runner: RouteRunner, manifest: TargetManifest, kind: RouteKind, actions: readonly InputAction[], options: MinimizeRouteOptions = {}): Promise<{ record: VerifiedRouteRecord; initial: RouteVerification; final: RouteVerification; minimization: MinimizeResult<InputAction> }> {
  const initial = await verifyRoute(runner, manifest, kind, actions, { ...options, attempts: options.candidateAttempts ?? 2, requiredMatches: options.candidateRequiredMatches ?? options.candidateAttempts ?? 2 });
  if (!initial.verified) throw new Error(`${kind} route did not satisfy the initial verification quorum`);
  const minimization = await minimizeSequence(actions, async candidate => (await verifyRoute(runner, manifest, kind, candidate, {
    ...options, attempts: options.candidateAttempts ?? 2, requiredMatches: options.candidateRequiredMatches ?? options.candidateAttempts ?? 2,
  })).verified, { maxAttempts: options.maxMinimizationAttempts ?? 50, maxElapsedMs: options.maxElapsedMs ?? 60_000, signal: options.signal });
  const final = await verifyRoute(runner, manifest, kind, minimization.items, {
    ...options, attempts: options.finalAttempts ?? 3, requiredMatches: options.finalRequiredMatches ?? options.finalAttempts ?? 3,
  });
  const routeKey = JSON.stringify(minimization.items.map(action => [action.key, action.holdMs ?? 0, action.waitMs ?? 0]));
  return {
    initial, final, minimization,
    record: {
      id: digest([manifest.id, kind, routeKey]), kind, status: final.verified ? 'verified' : 'unverified',
      actions: minimization.items.map(action => ({ ...action })), originalLength: actions.length,
      verificationAttempts: final.attempts, verificationMatches: final.matches,
      observationSignatures: [...final.observationSignatures], minimizationAttempts: minimization.attempts,
      observedAt: new Date().toISOString(),
    },
  };
}
