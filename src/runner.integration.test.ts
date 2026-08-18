import { describe, expect, it } from 'vitest';
import { resolve } from 'node:path';
import { loadManifest } from './manifest.js';
import { PlaytestRunner } from './runner.js';
import type { TargetManifest } from './types.js';

describe('PTY runner', () => {
  it('captures a real terminal fixture and emits actions', async () => {
    const manifest: TargetManifest = {
      schemaVersion: 1,
      id: 'turn-counter-test',
      command: 'node',
      args: [resolve('fixtures/turn-counter.mjs')],
      startupTimeoutMs: 1000,
      stepTimeoutMs: 20,
      episodeTimeoutMs: 2000,
    };
    const report = await new PlaytestRunner().run(manifest, { maxActions: 3, maxElapsedMs: 2000 });
    expect(report.status, JSON.stringify({ termination: report.termination, findings: report.findings, terminalText: report.terminalText })).toBe('passed');
    expect(report.actionCount).toBe(3);
    expect(report.terminalText).toContain('TERMINAL QUEST');
    expect(report.uniqueStates).toBeGreaterThan(0);
    expect(report.corpusSize).toBe(report.uniqueStates);
    expect(report.newCorpusEntries).toBe(report.uniqueStates);
    expect(report.schemaVersion).toBe(1);
    expect(report.termination.kind).toBe('action-budget');
    expect(report.replay.version).toBe(1);
  });

  it('reports a startup failure when a target never renders', async () => {
    const manifest = await loadManifest('fixtures/no-output.json');
    const report = await new PlaytestRunner().run(manifest, { maxActions: 1, maxElapsedMs: 1000 });
    expect(report.status).toBe('failed');
    expect(report.termination.kind).toBe('startup-failure');
    expect(report.findings.some(finding => finding.kind === 'startup-failure')).toBe(true);
  });

  it('enforces output limits and reports the primary cause', async () => {
    const manifest = await loadManifest('fixtures/output-flood.json');
    const report = await new PlaytestRunner().run(manifest, { maxActions: 1, maxElapsedMs: 1000 });
    expect(report.status).toBe('failed');
    expect(report.termination.kind).toBe('output-limit');
    expect(report.findings.filter(finding => finding.kind === 'output-limit')).toHaveLength(1);
    expect(report.findings.some(finding => finding.kind === 'crash')).toBe(false);
  });

  it('stops sending actions as soon as a crashed process is gone', async () => {
    const manifest = await loadManifest('fixtures/crash-sequence.json');
    const report = await new PlaytestRunner().run(manifest, {
      actions: [{ key: 'a' }, { key: 'b' }, { key: 'x' }, { key: 'q' }],
      maxActions: 4,
      maxElapsedMs: 4000,
    });
    expect(report.status).toBe('crashed');
    expect(report.actionCount).toBe(3);
    expect(report.termination).toMatchObject({ kind: 'target-exit', exitCode: 2 });
  });
});
