import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { ArtifactQuotaError, writeRunArtifacts } from './artifacts.js';
import type { RunReport } from './types.js';

const roots: string[] = [];

function report(): RunReport {
  return {
    schemaVersion: 1,
    targetId: 'fixture',
    status: 'passed',
    outcome: 'terminated',
    termination: { kind: 'target-exit', atAction: 0, exitCode: 0 },
    runtime: {
      backend: 'fake',
      capabilities: { isolation: 'none', processTreeCleanup: true, resize: true, signals: true, rawTerminalEvents: false },
      platform: process.platform,
      arch: process.arch,
      node: process.version,
    },
    actionCount: 0,
    elapsedMs: 1,
    actions: [],
    observations: [],
    findings: [],
    uniqueStates: 1,
    novelTransitions: 0,
    newCorpusEntries: 1,
    corpusSize: 1,
    terminalText: 'ready',
    replay: { version: 1, targetId: 'fixture', command: 'node', args: [], terminal: { cols: 80, rows: 24 }, actions: [] },
    cleanup: { attempted: true, graceful: true, forced: false, mechanism: 'none', elapsedMs: 1, confirmedExited: true },
  };
}

afterEach(async () => {
  await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true })));
});

describe('writeRunArtifacts', () => {
  it('publishes a complete bundle', async () => {
    const parent = await mkdtemp(join(tmpdir(), 'playtestr-artifacts-'));
    roots.push(parent);
    const root = join(parent, 'run');
    const result = await writeRunArtifacts(report(), root);
    expect(result.files).toEqual(['report.json', 'replay.json', 'last-screen.txt']);
    expect(JSON.parse(await readFile(join(root, 'report.json'), 'utf8')).targetId).toBe('fixture');
  });

  it('rejects the entire bundle before creating its destination when over quota', async () => {
    const parent = await mkdtemp(join(tmpdir(), 'playtestr-artifacts-'));
    roots.push(parent);
    const root = join(parent, 'run');
    await expect(writeRunArtifacts(report(), root, { maxBytes: 1 })).rejects.toBeInstanceOf(ArtifactQuotaError);
    await expect(readFile(join(root, 'report.json'))).rejects.toThrow();
  });
});
