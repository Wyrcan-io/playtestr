#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { actionDiversityPolicy } from './agents.js';
import { loadManifest } from './manifest.js';
import { minimizeSequence } from './minimize.js';
import { parseReplay, replayJson } from './replay.js';
import { PlaytestRunner } from './runner.js';
import type { OracleKind, ReplayV1 } from './types.js';

function valueAfter(args: string[], name: string): string | undefined {
  const index = args.indexOf(name);
  if (index < 0) return undefined;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error(`${name} requires a value`);
  return value;
}

function integerAfter(args: string[], name: string, minimum = 1): number | undefined {
  const value = valueAfter(args, name);
  if (value === undefined) return undefined;
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum) {
    throw new Error(`${name} must be a safe integer greater than or equal to ${minimum}`);
  }
  return parsed;
}

function help(): void {
  console.log(`Playtestr - evidence-first terminal-game playtesting

Usage:
  playtestr run --manifest game.json [--profile baseline|explore] [--seed 42] [--max-actions 100]
                [--max-ms 30000] [--artifacts artifacts/run] --trust-target
  playtestr minimize --manifest game.json --replay replay.json --kind crash
                     [--max-attempts 100] [--artifacts artifacts/minimized] --trust-target

--trust-target acknowledges that local targets run with your user permissions and are not sandboxed.
`);
}

async function main(): Promise<number> {
const args = process.argv.slice(2);
const command = args[0];
if (command !== 'run' && command !== 'minimize') {
  help();
  return args.length ? 1 : 0;
} else if (command === 'run') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('run requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const profile = valueAfter(args, '--profile') ?? 'baseline';
  if (profile !== 'baseline' && profile !== 'explore') throw new Error(`Unknown profile: ${profile}`);
  const runner = new PlaytestRunner({ policy: profile === 'explore' ? actionDiversityPolicy(manifest.allowedKeys) : undefined });
  const report = await runner.run(manifest, {
    seed: integerAfter(args, '--seed', Number.MIN_SAFE_INTEGER),
    maxActions: integerAfter(args, '--max-actions'),
    maxElapsedMs: integerAfter(args, '--max-ms'),
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
  return report.status === 'passed' ? 0 : 1;
} else {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  const replayPath = valueAfter(args, '--replay');
  if (!manifestPath || !replayPath) throw new Error('minimize requires --manifest <file> and --replay <file>');
  const manifest = await loadManifest(manifestPath);
  const replay = parseReplay(JSON.parse(await readFile(replayPath, 'utf8')));
  if (replay.targetId !== manifest.id) throw new Error(`Replay target ${replay.targetId} does not match manifest target ${manifest.id}`);
  const kind = valueAfter(args, '--kind') ?? 'crash';
  const oracleKinds = new Set<OracleKind>(['crash', 'timeout', 'stall', 'output-limit', 'startup-failure', 'runner-error']);
  if (!oracleKinds.has(kind as OracleKind)) throw new Error(`Unknown finding kind: ${kind}`);
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
    maxAttempts: integerAfter(args, '--max-attempts'),
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
  return report.findings.some(finding => finding.kind === kind) ? 0 : 1;
}
}

try {
  process.exitCode = await main();
} catch (error) {
  console.error(`ERROR: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}
