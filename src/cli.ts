#!/usr/bin/env node

import { mkdir, writeFile } from 'node:fs/promises';
import { loadManifest } from './manifest.js';
import { replayJson } from './replay.js';
import { PlaytestRunner } from './runner.js';

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
  playtestr run --manifest game.json [--seed 42] [--max-actions 100]
                [--max-ms 30000] [--artifacts artifacts/run]
`);
}

const args = process.argv.slice(2);
if (args[0] !== 'run') {
  help();
  process.exitCode = args.length ? 1 : 0;
} else {
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('run requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const report = await new PlaytestRunner().run(manifest, {
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
  for (const finding of report.findings) console.log(`- ${finding.severity}: ${finding.kind}: ${finding.message}`);
  if (report.status !== 'passed') process.exitCode = 1;
}
