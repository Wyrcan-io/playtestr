import { describe, expect, it } from 'vitest';
import { minimizeVerifiedRoute, verifyRoute, type RouteRunner } from './route-evidence.js';
import type { RunReport, TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'route', command: 'node', episodeTimeoutMs: 1000 };
const runner: RouteRunner = {
  async run(_manifest, options) {
    const keys = options.actions.map(action => action.key).join('');
    const text = keys.includes('ab') ? 'QUEST COMPLETE' : 'ROOM';
    return {
      targetId: 'route', actions: options.actions.map(action => ({ ...action })), actionCount: options.actions.length,
      observations: [{ at: 0, cols: 80, rows: 24, text, lines: [text], cursor: { x: 0, y: 0 }, alternateBuffer: false, changed: true, processAlive: true }],
      cleanup: { requested: true, confirmedExited: true, forced: false, elapsedMs: 0 }, findings: [],
    } as unknown as RunReport;
  },
};

describe('semantic route evidence', () => {
  it('verifies and removes irrelevant actions while preserving completion', async () => {
    const result = await minimizeVerifiedRoute(runner, manifest, 'completion', [{ key: 'x' }, { key: 'a' }, { key: 'b' }, { key: 'y' }], { candidateAttempts: 1, finalAttempts: 2 });
    expect(result.record.status).toBe('verified');
    expect(result.record.actions.map(action => action.key)).toEqual(['a', 'b']);
    expect(result.record.originalLength).toBe(4);
  });

  it('does not verify a route when the outcome is absent', async () => {
    expect((await verifyRoute(runner, manifest, 'hidden', [{ key: 'a' }, { key: 'b' }], { attempts: 2 })).verified).toBe(false);
  });
});
