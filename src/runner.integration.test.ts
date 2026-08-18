import { describe, expect, it } from 'vitest';
import { resolve } from 'node:path';
import { PlaytestRunner } from './runner.js';
import type { TargetManifest } from './types.js';

describe('PTY runner', () => {
  it('captures a real terminal fixture and emits actions', async () => {
    const manifest: TargetManifest = {
      id: 'turn-counter-test',
      command: 'node',
      args: [resolve('fixtures/turn-counter.mjs')],
      startupTimeoutMs: 1000,
      stepTimeoutMs: 20,
      episodeTimeoutMs: 2000,
    };
    const report = await new PlaytestRunner().run(manifest, { maxActions: 3, maxElapsedMs: 2000 });
    expect(report.status).toBe('passed');
    expect(report.actionCount).toBe(3);
    expect(report.terminalText).toContain('TERMINAL QUEST');
    expect(report.uniqueStates).toBeGreaterThan(0);
    expect(report.corpusSize).toBe(report.uniqueStates);
    expect(report.replay.version).toBe(1);
  });
});
