import { describe, expect, it } from 'vitest';
import { reproduceFinding, type ReplayRunner } from './reproduce.js';
import type { ReplayV1, RunReport, TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'fixture', command: 'node' };
const replay: ReplayV1 = { version: 1, targetId: 'fixture', command: 'node', args: [], terminal: { cols: 80, rows: 24 }, actions: [] };

function runner(sequence: boolean[]): ReplayRunner {
  let index = 0;
  return {
    async run() {
      const matched = sequence[index++] ?? false;
      return {
        status: matched ? 'crashed' : 'passed',
        findings: matched ? [{ signature: 'wanted' }] : [{ signature: 'different' }],
      } as RunReport;
    },
  };
}

describe('finding reproduction', () => {
  it('classifies an all-match quorum as stable', async () => {
    const result = await reproduceFinding(runner([true, true, true]), manifest, replay, 'wanted');
    expect(result).toMatchObject({ matches: 3, quorumMet: true, classification: 'stable', evidenceLevel: 'reproduced' });
  });

  it('classifies mixed evidence as flaky', async () => {
    const result = await reproduceFinding(runner([true, false, true]), manifest, replay, 'wanted', { requiredMatches: 2 });
    expect(result).toMatchObject({ matches: 2, quorumMet: true, classification: 'flaky' });
  });

  it('stops once quorum becomes mathematically impossible', async () => {
    const result = await reproduceFinding(runner([false, false, true]), manifest, replay, 'wanted', { requiredMatches: 2 });
    expect(result).toMatchObject({ completedAttempts: 2, matches: 0, quorumMet: false, classification: 'not-reproduced' });
  });
});
