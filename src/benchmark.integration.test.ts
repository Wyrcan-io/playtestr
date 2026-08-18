import { describe, expect, it } from 'vitest';
import { benchmarkStrategies } from './benchmark.js';
import { loadManifest } from './manifest.js';

describe('strategy benchmark', () => {
  it('finds the hidden route where equal-budget baselines do not', async () => {
    const manifest = await loadManifest('fixtures/hidden-route.json');
    const result = await benchmarkStrategies(manifest, { episodes: 10, maxActionsPerEpisode: 3, seed: 1 });
    const coverage = result.strategies.find(strategy => strategy.strategy === 'coverage-guided')!;
    const roundRobin = result.strategies.find(strategy => strategy.strategy === 'round-robin')!;
    const random = result.strategies.find(strategy => strategy.strategy === 'seeded-random')!;
    expect(coverage.hiddenFound).toBe(true);
    expect(roundRobin.hiddenFound).toBe(false);
    expect(random.hiddenFound).toBe(false);
    expect(roundRobin.actionCount).toBe(result.actionBudget);
    expect(random.actionCount).toBe(result.actionBudget);
    expect(roundRobin.episodes).toBe(coverage.episodes);
    expect(random.episodes).toBe(coverage.episodes);
    expect(result.strategies.every(strategy => strategy.cleanupFailures === 0)).toBe(true);
  }, 45_000);
});
