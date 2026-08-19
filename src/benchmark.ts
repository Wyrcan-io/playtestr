import { baselinePolicy, seededRandomPolicy } from './agents.js';
import type { TargetAdapter } from './adapter.js';
import { ActionCorpus } from './corpus.js';
import { exploreTarget } from './explorer.js';
import { autonomousPlaytest } from './orchestrator.js';
import { PlaytestRunner } from './runner.js';
import { WorldModel, type WorldModelSnapshot } from './world-model.js';
import type { ActionPolicy, RunReport, TargetManifest } from './types.js';

export interface BenchmarkExpectations {
  mechanics?: string[];
  milestones?: string[];
  tags?: string[];
  completion?: boolean;
  hidden?: boolean;
}

export interface BenchmarkOptions {
  episodes?: number;
  maxActionsPerEpisode?: number;
  seed?: number;
  signal?: AbortSignal;
  hiddenPattern?: RegExp;
  adapter?: TargetAdapter;
  expectations?: BenchmarkExpectations;
}

export interface StrategyBenchmark {
  strategy: 'intelligent-autonomy' | 'coverage-guided' | 'round-robin' | 'seeded-random';
  actionCount: number;
  actionBudget: number;
  budgetUtilization: number;
  episodes: number;
  uniqueStates: number;
  uniqueTransitions: number;
  hiddenFound: boolean;
  completionFound: boolean;
  firstDiscoveryEpisode?: number;
  firstDiscoveryAction?: number;
  reportedNovelTransitions: number;
  cleanupFailures: number;
  findingSignatures: string[];
  mechanicRecall: number;
  milestoneRecall: number;
  tagRecall: number;
  evidenceScore: number;
}

export interface BenchmarkResult {
  targetId: string;
  actionBudget: number;
  seed: number;
  strategies: StrategyBenchmark[];
  comparison: 'dominant' | 'competitive' | 'behind';
}

const ratio = (observed: ReadonlySet<string>, expected: readonly string[]): number => expected.length === 0
  ? 1
  : Number((expected.filter(value => observed.has(value)).length / expected.length).toFixed(3));

function evidence(snapshot: WorldModelSnapshot, expectations: BenchmarkExpectations = {}): Pick<StrategyBenchmark, 'mechanicRecall' | 'milestoneRecall' | 'tagRecall' | 'completionFound' | 'hiddenFound' | 'evidenceScore'> {
  const expectedMechanics = [...new Set(expectations.mechanics ?? [])];
  const expectedMilestones = [...new Set(expectations.milestones ?? [])];
  const expectedTags = [...new Set(expectations.tags ?? [])];
  const mechanicRecall = ratio(new Set(snapshot.mechanics.map(mechanic => mechanic.id)), expectedMechanics);
  const milestoneRecall = ratio(new Set(snapshot.milestones), expectedMilestones);
  const tagRecall = ratio(new Set(snapshot.states.flatMap(state => state.tags)), expectedTags);
  const completionFound = snapshot.completionPrefixes.length > 0;
  const hiddenFound = snapshot.hiddenPrefixes.length > 0;
  const scored = [
    ...(expectedMechanics.length ? [mechanicRecall] : []),
    ...(expectedMilestones.length ? [milestoneRecall] : []),
    ...(expectedTags.length ? [tagRecall] : []),
    ...(expectations.completion ? [completionFound ? 1 : 0] : []),
    ...(expectations.hidden ? [hiddenFound ? 1 : 0] : []),
  ];
  return {
    mechanicRecall,
    milestoneRecall,
    tagRecall,
    completionFound,
    hiddenFound,
    evidenceScore: scored.length ? Number((scored.reduce((total, value) => total + value, 0) / scored.length).toFixed(3)) : 0,
  };
}

async function worldFromReports(manifest: TargetManifest, reports: readonly RunReport[], adapter?: TargetAdapter): Promise<WorldModelSnapshot> {
  const world = new WorldModel(manifest.id, adapter);
  for (const report of reports) await world.ingest(report, manifest, adapter);
  return world.snapshot();
}

async function summarize(
  strategy: StrategyBenchmark['strategy'],
  reports: readonly RunReport[],
  corpus: ActionCorpus,
  hiddenPattern: RegExp,
  manifest: TargetManifest,
  actionBudget: number,
  expectations?: BenchmarkExpectations,
  adapter?: TargetAdapter,
  knownWorld?: WorldModelSnapshot,
): Promise<StrategyBenchmark> {
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
  const actionCount = reports.reduce((total, report) => total + report.actionCount, 0);
  const world = knownWorld ?? await worldFromReports(manifest, reports, adapter);
  const measured = evidence(world, expectations);
  return {
    strategy,
    actionCount,
    actionBudget,
    budgetUtilization: actionBudget === 0 ? 1 : Number((actionCount / actionBudget).toFixed(3)),
    episodes: reports.length,
    uniqueStates: Math.max(corpus.size, world.states.length),
    uniqueTransitions: world.transitions.length,
    hiddenFound: measured.hiddenFound || firstDiscoveryEpisode !== undefined,
    completionFound: measured.completionFound,
    ...(firstDiscoveryEpisode === undefined ? {} : { firstDiscoveryEpisode, firstDiscoveryAction }),
    reportedNovelTransitions: reports.reduce((total, report) => total + report.novelTransitions, 0),
    cleanupFailures: reports.filter(report => !report.cleanup.confirmedExited || report.cleanup.error).length,
    findingSignatures: [...new Set(reports.flatMap(report => report.findings.map(finding => finding.signature)))],
    mechanicRecall: measured.mechanicRecall,
    milestoneRecall: measured.milestoneRecall,
    tagRecall: measured.tagRecall,
    evidenceScore: measured.evidenceScore,
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
  const autonomy = await autonomousPlaytest(manifest, {
    episodes: Math.max(1, coverage.reports.length),
    maxActionsPerEpisode,
    maxTotalActions: actionBudget,
    seed,
    adapter: options.adapter,
    signal: options.signal,
  });
  const strategies = await Promise.all([
    summarize('intelligent-autonomy', autonomy.episodeRecords.map(record => record.report), new ActionCorpus(autonomy.world.states.map(state => ({ fingerprint: state.id, actions: state.shortestPrefix, firstSeenAtAction: state.shortestPrefix.length }))), hiddenPattern, manifest, actionBudget, options.expectations, options.adapter, autonomy.world),
    summarize('coverage-guided', coverage.reports, coverage.corpus, hiddenPattern, manifest, actionBudget, options.expectations, options.adapter),
    summarize('round-robin', roundRobin.reports, roundRobin.corpus, hiddenPattern, manifest, actionBudget, options.expectations, options.adapter),
    summarize('seeded-random', random.reports, random.corpus, hiddenPattern, manifest, actionBudget, options.expectations, options.adapter),
  ]);
  const intelligent = strategies[0]!;
  const baselines = strategies.slice(1);
  const bestBaselineScore = Math.max(0, ...baselines.map(strategy => strategy.evidenceScore));
  const lifecycleRegression = intelligent.cleanupFailures > Math.min(...baselines.map(strategy => strategy.cleanupFailures));
  const comparison: BenchmarkResult['comparison'] = lifecycleRegression || intelligent.evidenceScore + 0.05 < bestBaselineScore
    ? 'behind'
    : intelligent.evidenceScore > bestBaselineScore && baselines.every(strategy => intelligent.evidenceScore >= strategy.evidenceScore)
      ? 'dominant'
      : 'competitive';
  return {
    targetId: manifest.id,
    actionBudget,
    seed,
    strategies,
    comparison,
  };
}
