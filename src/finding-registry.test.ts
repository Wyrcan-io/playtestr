import { describe, expect, it } from 'vitest';
import { FindingRegistry, verifyFindingRecords } from './finding-registry.js';
import type { ReplayRunner } from './reproduce.js';
import type { OracleResult, ReplayV1, RunReport, TargetManifest } from './types.js';

const signature = 'a'.repeat(64);
const replay: ReplayV1 = { version: 1, targetId: 'game', command: 'node', args: [], terminal: { cols: 80, rows: 24 }, actions: [{ key: 'x' }] };
const finding: OracleResult = { signatureVersion: 1, signature, kind: 'crash', severity: 'error', evidenceLevel: 'observed', message: 'crashed', atAction: 1 };

function report(actions = 1): RunReport {
  return { targetId: 'game', status: 'crashed', seed: 4, findings: [finding], replay: { ...replay, actions: replay.actions.slice(0, actions) } } as RunReport;
}

describe('finding registry', () => {
  it('deduplicates exact signatures and retains the shortest replay', () => {
    const registry = new FindingRegistry();
    expect(registry.recordRun(report(), 1)).toEqual([signature]);
    expect(registry.recordRun(report(0), 2)).toEqual([]);
    expect(registry.records[0]).toMatchObject({ occurrenceCount: 2, firstSession: 1, lastSession: 2, seeds: [4] });
    expect(registry.records[0]!.replay.actions).toHaveLength(0);
  });

  it('promotes evidence only after an exact-signature quorum', async () => {
    const registry = new FindingRegistry();
    registry.recordRun(report(), 1);
    const runner: ReplayRunner = { async run() { return report(); } };
    const manifest: TargetManifest = { schemaVersion: 1, id: 'game', command: 'node' };
    const [result] = await verifyFindingRecords(registry, runner, manifest, [signature], { attempts: 2, requiredMatches: 2 });
    expect(result?.quorumMet).toBe(true);
    expect(registry.records[0]?.evidenceLevel).toBe('reproduced');
  });
});
