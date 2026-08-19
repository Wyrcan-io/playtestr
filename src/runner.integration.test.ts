import { describe, expect, it } from 'vitest';
import { resolve } from 'node:path';
import { loadManifest } from './manifest.js';
import { PlaytestRunner } from './runner.js';
import { probePid } from './process-tree.js';
import { PtyTerminalSession } from './terminal.js';
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
    expect(report.replay.version).toBe(2);
    expect(report.replay.backend.id).toBe('local-pty');
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

  it('round-trips Unicode through the PTY', async () => {
    const manifest = await loadManifest('fixtures/unicode.json');
    const report = await new PlaytestRunner().run(manifest, {
      actions: [{ key: 'λ' }, { key: 'q' }],
      maxActions: 2,
      maxElapsedMs: 4000,
    });
    expect(report.terminalText).toContain('UNICODE ACCEPTED: λ');
    expect(report.cleanup.confirmedExited).toBe(true);
  });

  it('propagates terminal resizes to the target and emulator', async () => {
    const manifest = await loadManifest('fixtures/resize.json');
    const session = await PtyTerminalSession.start({ manifest, viewport: { cols: 80, rows: 24 } });
    try {
      await session.resize(100, 30);
      await session.send({ key: 'r', waitMs: 100 });
      expect(session.observe().text).toContain('SIZE 100x30');
    } finally {
      const cleanup = await session.stop('completed');
      expect(cleanup.confirmedExited).toBe(true);
    }
  });

  it('classifies a hung action by the episode deadline', async () => {
    const manifest = await loadManifest('fixtures/hang.json');
    const report = await new PlaytestRunner().run(manifest, {
      actions: [{ key: 'x', waitMs: 1000 }],
      maxActions: 1,
      maxElapsedMs: 200,
    });
    expect(report.status).toBe('timed-out');
    expect(report.termination.kind).toBe('time-budget');
    expect(report.cleanup.confirmedExited).toBe(true);
  });

  it('reports deterministic abnormal exits as crashes', async () => {
    const manifest = await loadManifest('fixtures/signal.json');
    const report = await new PlaytestRunner().run(manifest, {
      actions: [],
      maxActions: 0,
      maxElapsedMs: 4000,
    });
    expect(report.status).toBe('crashed');
    expect(report.findings.some(finding => finding.kind === 'crash' && finding.signatureVersion === 1)).toBe(true);
  });

  it('cancels an in-flight action and confirms cleanup', async () => {
    const manifest = await loadManifest('fixtures/hang.json');
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 100);
    const report = await new PlaytestRunner().run(manifest, {
      actions: [{ key: 'x', waitMs: 10_000 }],
      maxActions: 1,
      maxElapsedMs: 20_000,
      signal: controller.signal,
    });
    expect(report.status).toBe('cancelled');
    expect(report.termination.kind).toBe('cancelled');
    expect(report.elapsedMs).toBeLessThan(5000);
    expect(report.cleanup.confirmedExited).toBe(true);
  });

  it('terminates descendants when a target owns a child process', async () => {
    const manifest = await loadManifest('fixtures/child-tree.json');
    const report = await new PlaytestRunner().run(manifest, { maxActions: 0, maxElapsedMs: 1000 });
    const childPid = Number(/CHILD_PID (\d+)/u.exec(report.terminalText)?.[1]);
    expect(Number.isSafeInteger(childPid)).toBe(true);
    expect(report.cleanup.forced).toBe(true);
    expect(report.cleanup.confirmedExited).toBe(true);
    expect(probePid(childPid)).toBe(false);
  });
});
