import { describe, expect, it } from 'vitest';
import { evaluateAdvantageGate } from './advantage.js';
import type { GauntletResult } from './gauntlet.js';

function fixture(intelligent: number, coverage: number): GauntletResult {
  const strategy = (name: 'intelligent-autonomy' | 'coverage-guided' | 'round-robin' | 'seeded-random', evidenceScore: number) => ({
    strategy: name, actionCount: 10, actionBudget: 10, budgetUtilization: 1, episodes: 2, uniqueStates: 2, uniqueTransitions: 1,
    hiddenFound: false, completionFound: true, reportedNovelTransitions: 1, cleanupFailures: 0, findingSignatures: [], mechanicRecall: 1, milestoneRecall: 1, tagRecall: 1, evidenceScore,
  });
  return { suiteId: 'suite', passed: true, scenarioCount: 1, discoveryCount: 1, robustnessCount: 0, lifecycleCount: 0, scenarios: [{
    id: 'game', kind: 'discovery', passed: true, runs: [], missingFindingKinds: [], cleanupFailures: 0,
    benchmarks: [{ targetId: 'game', actionBudget: 10, seed: 1, comparison: 'dominant', strategies: [strategy('intelligent-autonomy', intelligent), strategy('coverage-guided', coverage), strategy('round-robin', 0.2), strategy('seeded-random', 0.2)] }],
  }] };
}

describe('Agent Advantage gate', () => {
  it('unlocks downstream work only for deterministic fixed-budget dominance', () => {
    const result = fixture(1, 0.5);
    expect(evaluateAdvantageGate(result, fixture(1, 0.5)).passed).toBe(true);
    expect(evaluateAdvantageGate(result, fixture(0.9, 0.9)).passed).toBe(false);
    expect(evaluateAdvantageGate(result).passed).toBe(false);
  });
});
