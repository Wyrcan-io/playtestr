#!/usr/bin/env node

import { access, readFile } from 'node:fs/promises';
import { actionDiversityPolicy } from './agents.js';
import { writeArtifactBundle, writeRunArtifacts } from './artifacts.js';
import { benchmarkStrategies } from './benchmark.js';
import { ActionCorpus, loadCorpus } from './corpus.js';
import { exploreTarget } from './explorer.js';
import { minimizeFindingReplay } from './finding-minimize.js';
import { loadManifest } from './manifest.js';
import { parseReplay } from './replay.js';
import { reproduceFinding } from './reproduce.js';
import { PlaytestRunner } from './runner.js';
import type { OracleKind } from './types.js';

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
  playtestr verify --manifest game.json --replay replay.json --signature <sha256>
                   [--attempts 3] [--required-matches 3] --trust-target
  playtestr explore --manifest game.json [--episodes 25] [--max-actions 12]
                    [--corpus artifacts/corpus.json] [--artifacts artifacts/explore] --trust-target
  playtestr benchmark --manifest game.json [--episodes 25] [--max-actions 12]
                      [--seed 42] [--artifacts artifacts/benchmark] --trust-target

--trust-target acknowledges that local targets run with your user permissions and are not sandboxed.
`);
}

async function main(signal: AbortSignal): Promise<number> {
const args = process.argv.slice(2);
const command = args[0];
if (!['run', 'minimize', 'verify', 'explore', 'benchmark'].includes(command ?? '')) {
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
    signal,
  });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await writeRunArtifacts(report, artifactRoot, { maxBytes: manifest.maxArtifactBytes });
  }
  console.log(`${report.status.toUpperCase()} ${report.targetId} (${report.actionCount} actions, ${report.elapsedMs}ms)`);
  console.log(`states=${report.uniqueStates} novelTransitions=${report.novelTransitions} corpus=${report.corpusSize}`);
  for (const finding of report.findings) console.log(`- ${finding.severity}: ${finding.kind}: ${finding.message}`);
  return report.status === 'cancelled' ? 130 : report.status === 'passed' ? 0 : 1;
} else if (command === 'minimize') {
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
  const initialReport = await runner.run(manifest, {
    seed: replay.seed,
    actions: replay.actions,
    maxActions: replay.actions.length,
    maxElapsedMs: manifest.episodeTimeoutMs,
    signal,
  });
  const signature = valueAfter(args, '--signature') ?? initialReport.findings.find(finding => finding.kind === kind)?.signature;
  if (!signature) throw new Error(`Replay does not produce a finding of kind: ${kind}`);
  const candidateAttempts = integerAfter(args, '--candidate-attempts') ?? 2;
  const finalAttempts = integerAfter(args, '--attempts') ?? 3;
  const minimized = await minimizeFindingReplay(runner, manifest, replay, signature, {
    maxAttempts: integerAfter(args, '--max-attempts'),
    maxElapsedMs: integerAfter(args, '--max-ms') ?? 60_000,
    candidateAttempts,
    candidateRequiredMatches: integerAfter(args, '--candidate-required') ?? candidateAttempts,
    finalAttempts,
    finalRequiredMatches: integerAfter(args, '--required-matches') ?? finalAttempts,
    signal,
  });
  const report = await runner.run(manifest, {
    seed: replay.seed,
    actions: minimized.replay.actions,
    maxActions: minimized.replay.actions.length,
    maxElapsedMs: manifest.episodeTimeoutMs,
    signal,
  });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await writeRunArtifacts(report, artifactRoot, { maxBytes: manifest.maxArtifactBytes, report: { ...report, minimization: minimized } });
  }
  console.log(`MINIMIZED ${report.targetId}: ${replay.actions.length} -> ${minimized.replay.actions.length} actions (${minimized.minimization.attempts} candidates)`);
  console.log(`signature=${signature} evidence=${minimized.finalReproduction.classification}`);
  return report.status === 'cancelled' ? 130 : report.findings.some(finding => finding.signature === signature) ? 0 : 1;
} else if (command === 'verify') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  const replayPath = valueAfter(args, '--replay');
  const signature = valueAfter(args, '--signature');
  if (!manifestPath || !replayPath || !signature) throw new Error('verify requires --manifest, --replay, and --signature');
  const manifest = await loadManifest(manifestPath);
  const replay = parseReplay(JSON.parse(await readFile(replayPath, 'utf8')));
  if (replay.targetId !== manifest.id) throw new Error(`Replay target ${replay.targetId} does not match manifest target ${manifest.id}`);
  const attempts = integerAfter(args, '--attempts') ?? 3;
  const result = await reproduceFinding(new PlaytestRunner(), manifest, replay, signature, {
    attempts,
    requiredMatches: integerAfter(args, '--required-matches') ?? attempts,
    maxElapsedMs: integerAfter(args, '--max-ms') ?? 30_000,
    signal,
  });
  console.log(`${result.classification.toUpperCase()} signature=${signature} matches=${result.matches}/${result.completedAttempts} quorum=${result.quorumMet}`);
  return result.classification === 'cancelled' ? 130 : result.quorumMet ? 0 : 1;
} else if (command === 'explore') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('explore requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const corpusPath = valueAfter(args, '--corpus');
  let corpus = new ActionCorpus();
  if (corpusPath) {
    try { await access(corpusPath); corpus = await loadCorpus(corpusPath, manifest); } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
  }
  const result = await exploreTarget(manifest, {
    episodes: integerAfter(args, '--episodes'),
    maxActionsPerEpisode: integerAfter(args, '--max-actions'),
    maxElapsedMsPerEpisode: integerAfter(args, '--max-ms'),
    seed: integerAfter(args, '--seed', Number.MIN_SAFE_INTEGER),
    corpus,
    corpusPath,
    signal,
  });
  const last = result.reports.at(-1);
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot && last) await writeRunArtifacts(last, artifactRoot, { maxBytes: manifest.maxArtifactBytes, report: { exploration: { ...result, corpus: result.corpus.entries }, lastReport: last } });
  console.log(`EXPLORED ${manifest.id}: episodes=${result.episodes} actions=${result.actionCount} states=${result.uniqueStates} stop=${result.stopReason}`);
  return result.stopReason === 'cancelled' ? 130 : 0;
} else {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('benchmark requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const result = await benchmarkStrategies(manifest, {
    episodes: integerAfter(args, '--episodes'),
    maxActionsPerEpisode: integerAfter(args, '--max-actions'),
    seed: integerAfter(args, '--seed', Number.MIN_SAFE_INTEGER),
    signal,
  });
  for (const strategy of result.strategies) {
    console.log(`${strategy.strategy}: actions=${strategy.actionCount} episodes=${strategy.episodes} states=${strategy.uniqueStates} hidden=${strategy.hiddenFound}`);
  }
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await writeArtifactBundle(artifactRoot, { 'benchmark.json': `${JSON.stringify(result, null, 2)}\n` }, manifest.maxArtifactBytes);
  }
  return signal.aborted ? 130 : 0;
}
}

try {
  const controller = new AbortController();
  let interrupts = 0;
  const onInterrupt = (): void => {
    interrupts += 1;
    if (interrupts === 1) {
      console.error('Cancelling current playtest; press Ctrl+C again to force exit.');
      controller.abort();
    } else {
      process.exit(130);
    }
  };
  process.on('SIGINT', onInterrupt);
  try {
    process.exitCode = await main(controller.signal);
  } finally {
    process.off('SIGINT', onInterrupt);
  }
} catch (error) {
  console.error(`ERROR: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}
