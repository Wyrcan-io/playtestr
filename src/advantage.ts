import { createHash } from 'node:crypto';
import { runGauntlet, type GauntletResult, type RunGauntletOptions } from './gauntlet.js';

export interface AdvantagePolicy {
  minimumCoverageMargin: number;
  minimumSimpleBaselineMargin: number;
  minimumWinRate: number;
  maximumLossRate: number;
  requireRepeatDeterminism: boolean;
}

export interface AdvantageGateResult {
  version: 1;
  suiteId: string;
  passed: boolean;
  unlocked: Array<'replay-v2' | 'docker-execution'>;
  policy: AdvantagePolicy;
  trialCount: number;
  intelligentMeanEvidence: number;
  coverageMeanEvidence: number;
  roundRobinMeanEvidence: number;
  seededRandomMeanEvidence: number;
  coverageMargin: number;
  roundRobinMargin: number;
  seededRandomMargin: number;
  wins: number;
  ties: number;
  losses: number;
  winRate: number;
  lossRate: number;
  cleanupFailures: number;
  budgetParity: boolean;
  scenarioThresholdsPassed: boolean;
  deterministic: boolean;
  decisionReasons: string[];
  primary: GauntletResult;
  repeat?: GauntletResult;
}

export const defaultAdvantagePolicy: AdvantagePolicy = {
  minimumCoverageMargin: 0.10,
  minimumSimpleBaselineMargin: 0.15,
  minimumWinRate: 0.60,
  maximumLossRate: 0.20,
  requireRepeatDeterminism: true,
};

const mean = (values: readonly number[]): number => values.length ? Number((values.reduce((total, value) => total + value, 0) / values.length).toFixed(4)) : 0;
const digest = (value: unknown): string => createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');

function deterministicProjection(result: GauntletResult): unknown {
  return result.scenarios.map(scenario => ({
    id: scenario.id, passed: scenario.passed, cleanupFailures: scenario.cleanupFailures,
    benchmarks: scenario.benchmarks.map(benchmark => ({
      seed: benchmark.seed, actionBudget: benchmark.actionBudget, comparison: benchmark.comparison,
      strategies: benchmark.strategies.map(strategy => ({
        strategy: strategy.strategy, actionCount: strategy.actionCount, uniqueStates: strategy.uniqueStates,
        uniqueTransitions: strategy.uniqueTransitions, completionFound: strategy.completionFound,
        hiddenFound: strategy.hiddenFound, evidenceScore: strategy.evidenceScore, cleanupFailures: strategy.cleanupFailures,
      })),
    })),
  }));
}

export function evaluateAdvantageGate(primary: GauntletResult, repeat?: GauntletResult, policy: AdvantagePolicy = defaultAdvantagePolicy): AdvantageGateResult {
  const trials = primary.scenarios.flatMap(scenario => scenario.benchmarks);
  const strategy = (name: string) => trials.map(trial => trial.strategies.find(candidate => candidate.strategy === name)).filter(Boolean) as NonNullable<ReturnType<typeof trials[number]['strategies']['find']>>[];
  const intelligent = strategy('intelligent-autonomy');
  const coverage = strategy('coverage-guided');
  const roundRobin = strategy('round-robin');
  const random = strategy('seeded-random');
  const intelligentMeanEvidence = mean(intelligent.map(item => item.evidenceScore));
  const coverageMeanEvidence = mean(coverage.map(item => item.evidenceScore));
  const roundRobinMeanEvidence = mean(roundRobin.map(item => item.evidenceScore));
  const seededRandomMeanEvidence = mean(random.map(item => item.evidenceScore));
  const comparisons = intelligent.map((item, index) => Math.sign(item.evidenceScore - (coverage[index]?.evidenceScore ?? 0)));
  const wins = comparisons.filter(value => value > 0).length;
  const ties = comparisons.filter(value => value === 0).length;
  const losses = comparisons.filter(value => value < 0).length;
  const winRate = trials.length ? Number((wins / trials.length).toFixed(3)) : 0;
  const lossRate = trials.length ? Number((losses / trials.length).toFixed(3)) : 0;
  const cleanupFailures = primary.scenarios.reduce((total, scenario) => total + scenario.cleanupFailures, 0);
  const budgetParity = trials.every(trial => trial.strategies.every(item => item.actionCount === trial.actionBudget));
  const scenarioThresholdsPassed = primary.scenarios.length > 0 && primary.scenarios.every(scenario => scenario.passed);
  const deterministic = Boolean(repeat && repeat.suiteId === primary.suiteId && digest(deterministicProjection(repeat)) === digest(deterministicProjection(primary)));
  const coverageMargin = Number((intelligentMeanEvidence - coverageMeanEvidence).toFixed(4));
  const roundRobinMargin = Number((intelligentMeanEvidence - roundRobinMeanEvidence).toFixed(4));
  const seededRandomMargin = Number((intelligentMeanEvidence - seededRandomMeanEvidence).toFixed(4));
  const checks: Array<[boolean, string]> = [
    [trials.length > 0, 'no discovery trials were evaluated'],
    [cleanupFailures === 0, `${cleanupFailures} lifecycle cleanup failures occurred`],
    [budgetParity, 'one or more strategies did not consume the equal action budget'],
    [scenarioThresholdsPassed, 'one or more frozen scenario evidence thresholds failed'],
    [coverageMargin >= policy.minimumCoverageMargin, `coverage margin ${coverageMargin} is below ${policy.minimumCoverageMargin}`],
    [roundRobinMargin >= policy.minimumSimpleBaselineMargin, `round-robin margin ${roundRobinMargin} is below ${policy.minimumSimpleBaselineMargin}`],
    [seededRandomMargin >= policy.minimumSimpleBaselineMargin, `seeded-random margin ${seededRandomMargin} is below ${policy.minimumSimpleBaselineMargin}`],
    [winRate >= policy.minimumWinRate, `coverage win rate ${winRate} is below ${policy.minimumWinRate}`],
    [lossRate <= policy.maximumLossRate, `coverage loss rate ${lossRate} exceeds ${policy.maximumLossRate}`],
    [!policy.requireRepeatDeterminism || deterministic, 'repeat evaluation was absent or semantically different'],
  ];
  const decisionReasons = checks.filter(([passed]) => !passed).map(([, reason]) => reason);
  const passed = decisionReasons.length === 0;
  return {
    version: 1, suiteId: primary.suiteId, passed, unlocked: passed ? ['replay-v2', 'docker-execution'] : [], policy,
    trialCount: trials.length, intelligentMeanEvidence, coverageMeanEvidence, roundRobinMeanEvidence, seededRandomMeanEvidence,
    coverageMargin, roundRobinMargin, seededRandomMargin, wins, ties, losses, winRate, lossRate, cleanupFailures,
    budgetParity, scenarioThresholdsPassed, deterministic, decisionReasons, primary, ...(repeat ? { repeat } : {}),
  };
}

export async function runAdvantageGate(file: string, options: RunGauntletOptions = {}, policy: AdvantagePolicy = defaultAdvantagePolicy): Promise<AdvantageGateResult> {
  const primary = await runGauntlet(file, options);
  const repeat = options.signal?.aborted ? undefined : await runGauntlet(file, options);
  return evaluateAdvantageGate(primary, repeat, policy);
}
