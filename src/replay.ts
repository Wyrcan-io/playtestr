import { createHash } from 'node:crypto';
import { readFileSync, statSync } from 'node:fs';
import { isAbsolute, resolve } from 'node:path';
import type { ExecutionBackendCapabilities, InputAction, ReplayBackendIdentity, ReplayV2, RunReport, TargetManifest } from './types.js';

const sha256 = (value: unknown): string => createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
const defaultCapabilities: ExecutionBackendCapabilities = { isolation: 'none', processTreeCleanup: true, resize: true, signals: true, rawTerminalEvents: false };

export function targetManifestHash(manifest: Pick<TargetManifest, 'id' | 'command' | 'args' | 'cwd' | 'terminal' | 'allowedKeys' | 'observation' | 'seed'>): string {
  return sha256({ id: manifest.id, command: manifest.command, args: manifest.args ?? [], cwd: manifest.cwd, terminal: manifest.terminal, allowedKeys: manifest.allowedKeys, observation: manifest.observation, seed: manifest.seed });
}

export function targetArtifactHash(manifest: TargetManifest): string {
  const root = manifest.cwd ?? process.cwd();
  const candidates = [manifest.command, ...(manifest.args ?? [])]
    .filter(value => isAbsolute(value) || !value.startsWith('-'))
    .map(value => isAbsolute(value) ? value : resolve(root, value));
  const artifacts: Array<[string, string]> = [];
  for (const file of [...new Set(candidates)].sort()) {
    try {
      const stat = statSync(file);
      if (!stat.isFile() || stat.size > 50_000_000) continue;
      artifacts.push([file, createHash('sha256').update(readFileSync(file)).digest('hex')]);
    } catch { /* command names and literal arguments are represented by the manifest hash */ }
  }
  return sha256({ manifest: targetManifestHash(manifest), artifacts });
}

export function createReplay(manifest: TargetManifest, seed: number | undefined, viewport: { cols: number; rows: number }, actions: readonly InputAction[], backend: ReplayBackendIdentity = { id: 'local-pty', capabilities: defaultCapabilities }): ReplayV2 {
  return {
    version: 2, targetId: manifest.id, command: manifest.command, args: [...(manifest.args ?? [])],
    ...(manifest.cwd === undefined ? {} : { cwd: manifest.cwd }), seed, terminal: { ...viewport }, actions: actions.map(action => ({ ...action })),
    backend: { ...backend, capabilities: { ...backend.capabilities } }, targetManifestHash: targetManifestHash(manifest), targetArtifactHash: targetArtifactHash(manifest),
  };
}

export function replayJson(report: RunReport): string { return JSON.stringify(report.replay, null, 2); }

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function parseActions(value: unknown): InputAction[] {
  if (!Array.isArray(value)) throw new Error('Replay actions must be an array');
  return value.map((item, index) => {
    const action = object(item, `Replay action ${index}`);
    if (typeof action.key !== 'string' || !action.key) throw new Error(`Replay action ${index}.key must be a non-empty string`);
    for (const field of ['holdMs', 'waitMs'] as const) if (action[field] !== undefined && (!Number.isSafeInteger(action[field]) || (action[field] as number) < 0)) throw new Error(`Replay action ${index}.${field} must be a non-negative safe integer`);
    if (action.label !== undefined && typeof action.label !== 'string') throw new Error(`Replay action ${index}.label must be a string`);
    return { key: action.key, ...(action.holdMs === undefined ? {} : { holdMs: action.holdMs as number }), ...(action.waitMs === undefined ? {} : { waitMs: action.waitMs as number }), ...(action.label === undefined ? {} : { label: action.label as string }) };
  });
}

function parseCapabilities(value: unknown): ExecutionBackendCapabilities {
  const raw = object(value, 'Replay backend capabilities');
  if (!['none', 'process', 'container', 'browser-context'].includes(raw.isolation as string)) throw new Error('Replay backend isolation is invalid');
  for (const field of ['processTreeCleanup', 'resize', 'signals', 'rawTerminalEvents'] as const) if (typeof raw[field] !== 'boolean') throw new Error(`Replay backend ${field} must be boolean`);
  return raw as unknown as ExecutionBackendCapabilities;
}

/** Parse Replay V2 or deterministically migrate Replay V1 to V2. */
export function parseReplay(value: unknown): ReplayV2 {
  const replay = object(value, 'Replay');
  if (replay.version !== 1 && replay.version !== 2) throw new Error(`Unsupported replay version: ${String(replay.version)}`);
  if (typeof replay.targetId !== 'string' || !replay.targetId) throw new Error('Replay targetId must be a non-empty string');
  if (typeof replay.command !== 'string' || !replay.command) throw new Error('Replay command must be a non-empty string');
  if (!Array.isArray(replay.args) || replay.args.some(item => typeof item !== 'string')) throw new Error('Replay args must be strings');
  if (replay.cwd !== undefined && typeof replay.cwd !== 'string') throw new Error('Replay cwd must be a string');
  if (replay.seed !== undefined && !Number.isSafeInteger(replay.seed)) throw new Error('Replay seed must be a safe integer');
  const terminal = object(replay.terminal, 'Replay terminal');
  if (!Number.isSafeInteger(terminal.cols) || (terminal.cols as number) <= 0 || !Number.isSafeInteger(terminal.rows) || (terminal.rows as number) <= 0) throw new Error('Replay terminal dimensions must be positive safe integers');
  const actions = parseActions(replay.actions);
  const common = { version: 2 as const, targetId: replay.targetId, command: replay.command, args: [...replay.args] as string[], ...(replay.cwd === undefined ? {} : { cwd: replay.cwd as string }), ...(replay.seed === undefined ? {} : { seed: replay.seed as number }), terminal: { cols: terminal.cols as number, rows: terminal.rows as number }, actions };
  if (replay.version === 1) {
    const legacyHash = sha256({ targetId: common.targetId, command: common.command, args: common.args, cwd: common.cwd, terminal: common.terminal });
    return { ...common, backend: { id: 'legacy-local-pty', capabilities: { ...defaultCapabilities } }, targetManifestHash: legacyHash, targetArtifactHash: legacyHash };
  }
  const backend = object(replay.backend, 'Replay backend');
  if (typeof backend.id !== 'string' || !backend.id) throw new Error('Replay backend id must be a non-empty string');
  if (typeof replay.targetManifestHash !== 'string' || !/^[a-f0-9]{64}$/u.test(replay.targetManifestHash)) throw new Error('Replay targetManifestHash must be a SHA-256 digest');
  if (typeof replay.targetArtifactHash !== 'string' || !/^[a-f0-9]{64}$/u.test(replay.targetArtifactHash)) throw new Error('Replay targetArtifactHash must be a SHA-256 digest');
  for (const field of ['runtime', 'runtimeVersion', 'image', 'imageDigest'] as const) if (backend[field] !== undefined && typeof backend[field] !== 'string') throw new Error(`Replay backend ${field} must be a string`);
  return {
    ...common,
    backend: { id: backend.id, capabilities: parseCapabilities(backend.capabilities), ...(backend.runtime === undefined ? {} : { runtime: backend.runtime as string }), ...(backend.runtimeVersion === undefined ? {} : { runtimeVersion: backend.runtimeVersion as string }), ...(backend.image === undefined ? {} : { image: backend.image as string }), ...(backend.imageDigest === undefined ? {} : { imageDigest: backend.imageDigest as string }) },
    targetManifestHash: replay.targetManifestHash,
    targetArtifactHash: replay.targetArtifactHash,
  };
}
