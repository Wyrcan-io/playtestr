#!/usr/bin/env node

import { access, readFile } from 'node:fs/promises';
import { actionDiversityPolicy } from './agents.js';
import { writeArtifactBundle, writeRunArtifacts } from './artifacts.js';
import { benchmarkStrategies } from './benchmark.js';
import { createCampaign, loadCampaign, runCampaign, saveCampaign } from './campaign.js';
import { ActionCorpus, loadCorpus } from './corpus.js';
import { createDockerExecutionPlan, probeDocker } from './docker.js';
import { exploreTarget } from './explorer.js';
import { minimizeFindingReplay } from './finding-minimize.js';
import { runGauntlet } from './gauntlet.js';
import { loadManifest } from './manifest.js';
import { autonomousPlaytest } from './orchestrator.js';
import { createProfessionalReport, writeProfessionalReport } from './professional-report.js';
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
  playtestr autonomy --manifest game.json [--episodes 30] [--max-actions 12]
                     [--total-actions 360] [--stop-on-completion] [--stop-on-hidden]
                     [--artifacts artifacts/autonomy] --trust-target
  playtestr campaign --manifest game.json --state artifacts/game.campaign.json
                     [--episodes 30] [--total-actions 360] [--verify-findings]
                     [--report artifacts/game-report] [--fresh] --trust-target
  playtestr gauntlet --suite fixtures/gauntlet.v1.json
                     [--artifacts artifacts/gauntlet] --trust-target
  playtestr docker-plan --manifest game.json --image registry/game@sha256:...
                        [--network none|bridge --allow-network]
                        [--pull never|missing --allow-pull] [--artifacts artifacts/docker-plan]

--trust-target acknowledges that local targets run with your user permissions and are not sandboxed.
`);
}

async function main(signal: AbortSignal): Promise<number> {
const args = process.argv.slice(2);
const command = args[0];
if (!['run', 'minimize', 'verify', 'explore', 'benchmark', 'autonomy', 'campaign', 'gauntlet', 'docker-plan'].includes(command ?? '')) {
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
} else if (command === 'benchmark') {
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
    console.log(`${strategy.strategy}: actions=${strategy.actionCount}/${strategy.actionBudget} episodes=${strategy.episodes} states=${strategy.uniqueStates} evidence=${strategy.evidenceScore} hidden=${strategy.hiddenFound}`);
  }
  console.log(`comparison=${result.comparison}`);
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await writeArtifactBundle(artifactRoot, { 'benchmark.json': `${JSON.stringify(result, null, 2)}\n` }, manifest.maxArtifactBytes);
  }
  return signal.aborted ? 130 : 0;
} else if (command === 'autonomy') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  if (!manifestPath) throw new Error('autonomy requires --manifest <file>');
  const manifest = await loadManifest(manifestPath);
  const result = await autonomousPlaytest(manifest, {
    episodes: integerAfter(args, '--episodes'),
    maxActionsPerEpisode: integerAfter(args, '--max-actions'),
    maxTotalActions: integerAfter(args, '--total-actions'),
    maxElapsedMs: integerAfter(args, '--max-ms'),
    seed: integerAfter(args, '--seed', Number.MIN_SAFE_INTEGER),
    stopOnCompletion: args.includes('--stop-on-completion'),
    stopOnHidden: args.includes('--stop-on-hidden'),
    signal,
  });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) {
    await writeArtifactBundle(artifactRoot, { 'autonomy.json': `${JSON.stringify(result, null, 2)}\n` }, manifest.maxArtifactBytes);
  }
  console.log(`AUTONOMY ${manifest.id}: episodes=${result.episodes} actions=${result.actionCount} states=${result.world.states.length} mechanics=${result.world.mechanics.length} milestones=${result.world.milestones.length} stop=${result.stopReason}`);
  for (const contribution of result.contributions.filter(item => item.selectedEpisodes > 0)) {
    console.log(`${contribution.role}: episodes=${contribution.selectedEpisodes} states=${contribution.newStates} mechanics=${contribution.newMechanics} milestones=${contribution.newMilestones}`);
  }
  return result.stopReason === 'cancelled' ? 130 : result.stopReason === 'runner-error' ? 1 : 0;
} else if (command === 'campaign') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const manifestPath = valueAfter(args, '--manifest');
  const statePath = valueAfter(args, '--state');
  if (!manifestPath || !statePath) throw new Error('campaign requires --manifest <file> and --state <file>');
  const manifest = await loadManifest(manifestPath);
  let campaign;
  let stateExists = false;
  try { await access(statePath); stateExists = true; } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
  }
  if (args.includes('--fresh') && stateExists) throw new Error('--fresh refuses to overwrite an existing campaign state');
  campaign = stateExists ? await loadCampaign(statePath, manifest) : createCampaign(manifest, valueAfter(args, '--campaign-id'));
  const expectedRevision = campaign.revision;
  const result = await runCampaign(manifest, campaign, {
    episodes: integerAfter(args, '--episodes'),
    maxActionsPerEpisode: integerAfter(args, '--max-actions'),
    maxTotalActions: integerAfter(args, '--total-actions'),
    maxElapsedMs: integerAfter(args, '--max-ms'),
    seed: integerAfter(args, '--seed', Number.MIN_SAFE_INTEGER),
    stopOnCompletion: args.includes('--stop-on-completion'),
    stopOnHidden: args.includes('--stop-on-hidden'),
    verifyFindings: args.includes('--verify-findings'),
    verificationAttempts: integerAfter(args, '--verification-attempts'),
    verificationRequiredMatches: integerAfter(args, '--verification-required'),
    verificationMaxElapsedMs: integerAfter(args, '--verification-max-ms'),
    signal,
  });
  const persisted = await saveCampaign(result.campaign, manifest, statePath, { expectedRevision });
  const reportRoot = valueAfter(args, '--report');
  if (reportRoot) await writeProfessionalReport(createProfessionalReport(manifest, persisted, { autonomy: result.autonomy }), reportRoot, manifest.maxArtifactBytes);
  console.log(`CAMPAIGN ${manifest.id}: revision=${persisted.revision} sessions=${persisted.totals.sessions} episodes=${persisted.totals.episodes} actions=${persisted.totals.actions} states=${persisted.world.states.length} findings=${persisted.findings.length}`);
  return result.autonomy.stopReason === 'cancelled' ? 130 : result.autonomy.stopReason === 'runner-error' ? 1 : 0;
} else if (command === 'gauntlet') {
  if (!args.includes('--trust-target')) throw new Error('Local execution requires --trust-target; the PTY backend is not a sandbox');
  const suitePath = valueAfter(args, '--suite');
  if (!suitePath) throw new Error('gauntlet requires --suite <file>');
  const result = await runGauntlet(suitePath, { signal });
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) await writeArtifactBundle(artifactRoot, { 'gauntlet.json': `${JSON.stringify(result, null, 2)}\n` }, integerAfter(args, '--max-artifact-bytes') ?? 50_000_000);
  for (const scenario of result.scenarios) console.log(`${scenario.passed ? 'PASS' : 'FAIL'} ${scenario.kind}/${scenario.id} cleanupFailures=${scenario.cleanupFailures}`);
  console.log(`GAUNTLET ${result.suiteId}: ${result.scenarios.filter(scenario => scenario.passed).length}/${result.scenarioCount} passed`);
  return signal.aborted ? 130 : result.passed ? 0 : 1;
} else {
  const manifestPath = valueAfter(args, '--manifest');
  const image = valueAfter(args, '--image');
  if (!manifestPath || !image) throw new Error('docker-plan requires --manifest <file> and --image <reference>');
  const manifest = await loadManifest(manifestPath);
  const network = valueAfter(args, '--network') ?? 'none';
  const pull = valueAfter(args, '--pull') ?? 'never';
  if (network !== 'none' && network !== 'bridge') throw new Error('--network must be none or bridge');
  if (pull !== 'never' && pull !== 'missing') throw new Error('--pull must be never or missing');
  const plan = createDockerExecutionPlan(manifest, {
    version: 1,
    image,
    network,
    pull,
    allowNetwork: args.includes('--allow-network'),
    allowPull: args.includes('--allow-pull'),
    containerWorkdir: valueAfter(args, '--container-workdir'),
    user: valueAfter(args, '--user'),
  });
  const capability = await probeDocker(valueAfter(args, '--docker-command') ?? 'docker');
  const output = { capability, plan };
  const artifactRoot = valueAfter(args, '--artifacts');
  if (artifactRoot) await writeArtifactBundle(artifactRoot, { 'docker-plan.json': `${JSON.stringify(output, null, 2)}\n` }, 1_000_000);
  console.log(`DOCKER PLAN ${manifest.id}: daemon=${capability.daemonReachable ? 'reachable' : 'unavailable'} network=${network} pull=${pull} restrictions=${plan.restrictions.length}`);
  if (!capability.daemonReachable && capability.error) console.log(`probe=${capability.error}`);
  console.log('Plan created only; Replay V1 does not execute Docker targets yet.');
  return 0;
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
