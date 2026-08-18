import type { InputAction, ReplayV1, RunReport, TargetManifest } from './types.js';

export function createReplay(manifest: TargetManifest, seed: number | undefined, viewport: { cols: number; rows: number }, actions: readonly InputAction[]): ReplayV1 {
  return {
    version: 1,
    targetId: manifest.id,
    command: manifest.command,
    args: [...(manifest.args ?? [])],
    seed,
    terminal: viewport,
    actions: [...actions],
  };
}

export function replayJson(report: RunReport): string {
  return JSON.stringify(report.replay, null, 2);
}
