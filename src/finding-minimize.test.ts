import { describe, expect, it } from 'vitest';
import { minimizeFindingReplay } from './finding-minimize.js';
import type { ReplayRunner } from './reproduce.js';
import type { ReplayV1, RunOptions, RunReport, TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'fixture', command: 'node' };
const replay: ReplayV1 = {
  version: 1,
  targetId: 'fixture',
  command: 'node',
  args: [],
  terminal: { cols: 80, rows: 24 },
  actions: [{ key: 'noise' }, { key: 'essential' }],
};

const runner: ReplayRunner = {
  async run(_manifest: TargetManifest, options?: RunOptions) {
    const exact = options?.actions?.some(action => action.key === 'essential');
    return {
      status: 'crashed',
      findings: [{ signature: exact ? 'exact-crash' : 'different-crash', kind: 'crash' }],
    } as RunReport;
  },
};

describe('exact finding minimization', () => {
  it('rejects same-kind findings with a different signature', async () => {
    const result = await minimizeFindingReplay(runner, manifest, replay, 'exact-crash', {
      candidateAttempts: 1,
      finalAttempts: 1,
      maxAttempts: 10,
    });
    expect(result.replay.actions).toEqual([{ key: 'essential' }]);
    expect(result.finalReproduction.classification).toBe('stable');
  });
});
