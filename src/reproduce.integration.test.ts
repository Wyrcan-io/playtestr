import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { loadManifest } from './manifest.js';
import { reproduceFinding } from './reproduce.js';
import { PlaytestRunner } from './runner.js';

describe('real finding reproduction', () => {
  it('classifies alternating target behavior as flaky', async () => {
    const root = await mkdtemp(join(tmpdir(), 'playtestr-flaky-'));
    try {
      const manifest = await loadManifest('fixtures/flaky.json');
      manifest.env = { ...manifest.env, PLAYTESTR_FLAKY_FILE: join(root, 'counter.txt') };
      const runner = new PlaytestRunner();
      const initial = await runner.run(manifest, { actions: [], maxActions: 0, maxElapsedMs: 4000 });
      const signature = initial.findings.find(finding => finding.kind === 'crash')?.signature;
      expect(signature).toBeTruthy();
      const result = await reproduceFinding(runner, manifest, initial.replay, signature!, {
        attempts: 3,
        requiredMatches: 1,
        maxElapsedMs: 12_000,
      });
      expect(result).toMatchObject({ matches: 1, quorumMet: true, classification: 'flaky' });
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  }, 15_000);
});
