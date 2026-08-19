import type { EvidenceLevel, Replay, RunOptions, RunReport, TargetManifest } from './types.js';

export interface ReplayRunner {
  run(manifest: TargetManifest, options?: RunOptions): Promise<RunReport>;
}

export interface ReproductionOptions {
  attempts?: number;
  requiredMatches?: number;
  maxElapsedMs?: number;
  runOptions?: Omit<RunOptions, 'actions' | 'seed' | 'signal'>;
  signal?: AbortSignal;
}

export type ReproductionClassification = 'stable' | 'flaky' | 'not-reproduced' | 'cancelled' | 'budget-exhausted';

export interface ReproductionAttempt {
  attempt: number;
  matched: boolean;
  status: RunReport['status'];
  observedSignatures: string[];
}

export interface ReproductionResult {
  signature: string;
  requestedAttempts: number;
  completedAttempts: number;
  requiredMatches: number;
  matches: number;
  quorumMet: boolean;
  classification: ReproductionClassification;
  evidenceLevel: EvidenceLevel;
  elapsedMs: number;
  attempts: ReproductionAttempt[];
}

export async function reproduceFinding(
  runner: ReplayRunner,
  manifest: TargetManifest,
  replay: Replay,
  signature: string,
  options: ReproductionOptions = {},
): Promise<ReproductionResult> {
  const requestedAttempts = options.attempts ?? 3;
  const requiredMatches = options.requiredMatches ?? requestedAttempts;
  const maxElapsedMs = options.maxElapsedMs ?? 30_000;
  if (!Number.isSafeInteger(requestedAttempts) || requestedAttempts <= 0) throw new Error('Reproduction attempts must be a positive safe integer');
  if (!Number.isSafeInteger(requiredMatches) || requiredMatches <= 0 || requiredMatches > requestedAttempts) {
    throw new Error('Required matches must be between 1 and the requested attempt count');
  }
  if (!Number.isSafeInteger(maxElapsedMs) || maxElapsedMs <= 0) throw new Error('Reproduction time budget must be a positive safe integer');

  const startedAt = Date.now();
  const attempts: ReproductionAttempt[] = [];
  let matches = 0;
  let stopped: 'complete' | 'cancelled' | 'budget-exhausted' | 'quorum-impossible' = 'complete';
  for (let index = 0; index < requestedAttempts; index += 1) {
    if (options.signal?.aborted) {
      stopped = 'cancelled';
      break;
    }
    const remainingMs = maxElapsedMs - (Date.now() - startedAt);
    if (remainingMs <= 0) {
      stopped = 'budget-exhausted';
      break;
    }
    const report = await runner.run(manifest, {
      ...options.runOptions,
      seed: replay.seed,
      actions: replay.actions,
      maxActions: replay.actions.length,
      maxElapsedMs: Math.min(options.runOptions?.maxElapsedMs ?? remainingMs, remainingMs),
      signal: options.signal,
    });
    const observedSignatures = [...new Set(report.findings.map(finding => finding.signature))];
    const matched = observedSignatures.includes(signature);
    if (matched) matches += 1;
    attempts.push({ attempt: index + 1, matched, status: report.status, observedSignatures });
    if (report.status === 'cancelled') {
      stopped = 'cancelled';
      break;
    }
    const remainingAttempts = requestedAttempts - attempts.length;
    if (matches + remainingAttempts < requiredMatches) {
      stopped = 'quorum-impossible';
      break;
    }
  }

  const quorumMet = matches >= requiredMatches;
  let classification: ReproductionClassification;
  if (stopped === 'cancelled') classification = 'cancelled';
  else if (stopped === 'budget-exhausted') classification = 'budget-exhausted';
  else if (attempts.length === requestedAttempts && matches === requestedAttempts) classification = 'stable';
  else if (matches === 0) classification = 'not-reproduced';
  else classification = 'flaky';
  return {
    signature,
    requestedAttempts,
    completedAttempts: attempts.length,
    requiredMatches,
    matches,
    quorumMet,
    classification,
    evidenceLevel: quorumMet ? 'reproduced' : 'observed',
    elapsedMs: Date.now() - startedAt,
    attempts,
  };
}
