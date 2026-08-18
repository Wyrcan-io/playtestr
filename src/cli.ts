#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { explorationPolicy } from './agents.js';
import { loadManifest } from './manifest.js';
import { minimizeSequence } from './minimize.js';
import { replayJson } from './replay.js';
import { PlaytestRunner } from './runner.js';
import type { ReplayV1 } from './types.js';

function valueAfter(args: string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
}

function numberAfter(args: string[], name: string): number | undefined {
  const value = valueAfter(args, name);
  return value === undefined ? undefined : Number(value);
}

function help(): void {
  console.log(`Playtestr — autonomous terminal-game playtesting

Usage:
  playtestr run --manifest game.json [--profile baseline|explore] [--seed 42] [--max-actions 100]
                [--max-ms 30000] [--artifacts artifacts/run]
  playtestr minimize --manifest game.json --replay replay.json --kind crash
                     [--max-attempts 100] [--artifacts artifacts/minimized]
`);
}

const args = process.argv.slice(2);
const command = args[0];
if (command !== 'run' && command !== 'minimize') {
  help();
  process.exitCode = args.length ? 1 : 0;
} else if (command === 'run') {
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('run requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const profile = valueAfter(args, '--profile') ?? 'baseline';
  if (profile !== 'baseline' && profile !== 'explore') throw new Error(`Unknown profile: ${profile}`);
  const runner = new PlaytestRunner({ policy: profile === 'explore' ? explorationPolicy(manifest.allowedKeys) : undefined });
  const report = await runner.run(manifest, {
    seed: numberAfter(args, '--seed'),
    maxActions: numberAfter(args, '--max-actions'),
    maxElapsedMs: numberAfter(args, '--max-ms'),
  });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await mkdir(artifactRoot, { recursive: true });
    await writeFile(`${artifactRoot}/report.json`, JSON.stringify(report, null, 2));
    await writeFile(`${artifactRoot}/replay.json`, replayJson(report));
    await writeFile(`${artifactRoot}/last-screen.txt`, report.terminalText);
  }
  console.log(`${report.status.toUpperCase()} ${report.targetId} (${report.actionCount} actions, ${report.elapsedMs}ms)`);
  console.log(`states=${report.uniqueStates} novelTransitions=${report.novelTransitions} corpus=${report.corpusSize}`);
  for (const finding of report.findings) console.log(`- ${finding.severity}: ${finding.kind}: ${finding.message}`);
  process.exit(report.status === 'passed' ? 0 : 1);
} else {
  const manifestPath = valueAfter(args, '--manifest');
  const replayPath = valueAfter(args, '--replay');
  if (!manifestPath || !replayPath) throw new Error('minimize requires --manifest <file> and --replay <file>');
  const manifest = await loadManifest(manifestPath);
  const replay = JSON.parse(await readFile(replayPath, 'utf8')) as ReplayV1;
  const kind = valueAfter(args, '--kind') ?? 'crash';
  const runner = new PlaytestRunner();
  const reproduces = async (actions: readonly ReplayV1['actions'][number][]): Promise<boolean> => {
    const report = await runner.run(manifest, {
      seed: replay.seed,
      actions: [...actions],
      maxActions: actions.length,
      maxElapsedMs: manifest.episodeTimeoutMs,
    });
    return report.findings.some(finding => finding.kind === kind);
  };
  if (!(await reproduces(replay.actions))) throw new Error(`Replay does not reproduce finding kind: ${kind}`);
  const minimized = await minimizeSequence(replay.actions, reproduces, {
    maxAttempts: numberAfter(args, '--max-attempts'),
  });
  const report = await runner.run(manifest, {
    seed: replay.seed,
    actions: minimized.items,
    maxActions: minimized.items.length,
    maxElapsedMs: manifest.episodeTimeoutMs,
  });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await mkdir(artifactRoot, { recursive: true });
    await writeFile(`${artifactRoot}/report.json`, JSON.stringify({ ...report, minimization: minimized }, null, 2));
    await writeFile(`${artifactRoot}/replay.json`, replayJson(report));
    await writeFile(`${artifactRoot}/last-screen.txt`, report.terminalText);
  }
  console.log(`MINIMIZED ${report.targetId}: ${replay.actions.length} -> ${minimized.items.length} actions (${minimized.attempts} attempts)`);
  process.exit(report.findings.some(finding => finding.kind === kind) ? 0 : 1);
}
