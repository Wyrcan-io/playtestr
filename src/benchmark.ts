import { baselinePolicy, seededRandomPolicy } from './agents.js';
import { ActionCorpus } from './corpus.js';
import { exploreTarget } from './explorer.js';
import { PlaytestRunner } from './runner.js';
import type { ActionPolicy, RunReport, TargetManifest } from './types.js';

export interface BenchmarkOptions {
  episodes?: number;
  maxActionsPerEpisode?: number;
  seed?: number;
  signal?: AbortSignal;
  hiddenPattern?: RegExp;
}

export interface StrategyBenchmark {
  strategy: 'coverage-guided' | 'round-robin' | 'seeded-random';
  actionCount: number;
  episodes: number;
  uniqueStates: number;
  hiddenFound: boolean;
  firstDiscoveryEpisode?: number;
  firstDiscoveryAction?: number;
  reportedNovelTransitions: number;
  cleanupFailures: number;
  findingSignatures: string[];
}

export interface BenchmarkResult {
  targetId: string;
  actionBudget: number;
  seed: number;
  strategies: StrategyBenchmark[];
}

function summarize(
  strategy: StrategyBenchmark['strategy'],
  reports: readonly RunReport[],
  corpus: ActionCorpus,
  hiddenPattern: RegExp,
): StrategyBenchmark {
  let cumulativeActions = 0;
  let firstDiscoveryEpisode: number | undefined;
  let firstDiscoveryAction: number | undefined;
  reports.forEach((report, index) => {
    cumulativeActions += report.actionCount;
    hiddenPattern.lastIndex = 0;
    if (firstDiscoveryEpisode === undefined && hiddenPattern.test(report.terminalText)) {
      firstDiscoveryEpisode = index + 1;
      firstDiscoveryAction = cumulativeActions;
    }
  });
  return {
    strategy,
    actionCount: reports.reduce((total, report) => total + report.actionCount, 0),
    episodes: reports.length,
    uniqueStates: corpus.size,
    hiddenFound: firstDiscoveryEpisode !== undefined,
    ...(firstDiscoveryEpisode === undefined ? {} : { firstDiscoveryEpisode, firstDiscoveryAction }),
    reportedNovelTransitions: reports.reduce((total, report) => total + report.novelTransitions, 0),
    cleanupFailures: reports.filter(report => !report.cleanup.confirmedExited || report.cleanup.error).length,
    findingSignatures: [...new Set(reports.flatMap(report => report.findings.map(finding => finding.signature)))],
  };
}

async function runBaseline(
  manifest: TargetManifest,
  episodeActionBudgets: readonly number[],
  policyForEpisode: (episode: number) => ActionPolicy,
  seed: number,
  signal?: AbortSignal,
): Promise<{ reports: RunReport[]; corpus: ActionCorpus }> {
  const corpus = new ActionCorpus();
  const reports: RunReport[] = [];
  for (const episodeActions of episodeActionBudgets) {
    if (signal?.aborted) break;
    const report = await new PlaytestRunner({ corpus, policy: policyForEpisode(reports.length) }).run(manifest, {
      maxActions: episodeActions,
      maxElapsedMs: manifest.episodeTimeoutMs,
      seed,
      signal,
    });
    reports.push(report);
  }
  return { reports, corpus };
}

export async function benchmarkStrategies(manifest: TargetManifest, options: BenchmarkOptions = {}): Promise<BenchmarkResult> {
  const seed = options.seed ?? 0;
  const maxActionsPerEpisode = options.maxActionsPerEpisode ?? 12;
  const hiddenPattern = options.hiddenPattern ?? /\b(?:SECRET|HIDDEN|BONUS)\b/iu;
  const coverage = await exploreTarget(manifest, {
    episodes: options.episodes ?? 25,
    maxActionsPerEpisode,
    seed,
    signal: options.signal,
  });
  const actionBudget = coverage.actionCount;
  const episodeActionBudgets = coverage.reports.map(report => report.actionCount);
  const roundRobin = await runBaseline(manifest, episodeActionBudgets, () => baselinePolicy(manifest.allowedKeys), seed, options.signal);
  const random = await runBaseline(manifest, episodeActionBudgets, episode => seededRandomPolicy(manifest.allowedKeys, seed + episode), seed, options.signal);
  return {
    targetId: manifest.id,
    actionBudget,
    seed,
    strategies: [
      summarize('coverage-guided', coverage.reports, coverage.corpus, hiddenPattern),
      summarize('round-robin', roundRobin.reports, roundRobin.corpus, hiddenPattern),
      summarize('seeded-random', random.reports, random.corpus, hiddenPattern),
    ],
  };
}
