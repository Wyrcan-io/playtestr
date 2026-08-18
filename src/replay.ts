import type { InputAction, ReplayV1, RunReport, TargetManifest } from './types.js';

export function createReplay(manifest: TargetManifest, seed: number | undefined, viewport: { cols: number; rows: number }, actions: readonly InputAction[]): ReplayV1 {
  return {
    version: 1,
    targetId: manifest.id,
    command: manifest.command,
    args: [...(manifest.args ?? [])],
    ...(manifest.cwd === undefined ? {} : { cwd: manifest.cwd }),
    seed,
    terminal: viewport,
    actions: [...actions],
  };
}

export function replayJson(report: RunReport): string {
  return JSON.stringify(report.replay, null, 2);
}

export function parseReplay(value: unknown): ReplayV1 {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Replay must be an object');
  const replay = value as Record<string, unknown>;
  if (replay.version !== 1) throw new Error(`Unsupported replay version: ${String(replay.version)}`);
  if (typeof replay.targetId !== 'string' || !replay.targetId) throw new Error('Replay targetId must be a non-empty string');
  if (typeof replay.command !== 'string' || !replay.command) throw new Error('Replay command must be a non-empty string');
  if (!Array.isArray(replay.args) || replay.args.some(item => typeof item !== 'string')) throw new Error('Replay args must be strings');
  if (replay.cwd !== undefined && typeof replay.cwd !== 'string') throw new Error('Replay cwd must be a string');
  if (replay.seed !== undefined && (!Number.isSafeInteger(replay.seed))) throw new Error('Replay seed must be a safe integer');
  if (!replay.terminal || typeof replay.terminal !== 'object' || Array.isArray(replay.terminal)) throw new Error('Replay terminal must be an object');
  const terminal = replay.terminal as Record<string, unknown>;
  if (!Number.isSafeInteger(terminal.cols) || (terminal.cols as number) <= 0 ||
      !Number.isSafeInteger(terminal.rows) || (terminal.rows as number) <= 0) {
    throw new Error('Replay terminal dimensions must be positive safe integers');
  }
  if (!Array.isArray(replay.actions)) throw new Error('Replay actions must be an array');
  const actions = replay.actions.map((item, index) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) throw new Error(`Replay action ${index} must be an object`);
    const action = item as Record<string, unknown>;
    if (typeof action.key !== 'string' || !action.key) throw new Error(`Replay action ${index}.key must be a non-empty string`);
    for (const field of ['holdMs', 'waitMs'] as const) {
      if (action[field] !== undefined && (!Number.isSafeInteger(action[field]) || (action[field] as number) < 0)) {
        throw new Error(`Replay action ${index}.${field} must be a non-negative safe integer`);
      }
    }
    if (action.label !== undefined && typeof action.label !== 'string') throw new Error(`Replay action ${index}.label must be a string`);
    return {
      key: action.key as string,
      ...(action.holdMs === undefined ? {} : { holdMs: action.holdMs as number }),
      ...(action.waitMs === undefined ? {} : { waitMs: action.waitMs as number }),
      ...(action.label === undefined ? {} : { label: action.label as string }),
    };
  });
  return {
    version: 1,
    targetId: replay.targetId,
    command: replay.command,
    args: [...replay.args] as string[],
    ...(replay.cwd === undefined ? {} : { cwd: replay.cwd as string }),
    ...(replay.seed === undefined ? {} : { seed: replay.seed as number }),
    terminal: { cols: terminal.cols as number, rows: terminal.rows as number },
    actions,
  };
}
