import { describe, expect, it } from 'vitest';
import { runEvaluationSuite } from './evaluation.js';
import { loadManifest } from './manifest.js';
import type { TargetAdapter } from './adapter.js';

const includes = (text: string, value: string): boolean => text.includes(value);

describe('diverse terminal autonomy evaluation suite', () => {
  it('covers menu/resource, text-command, and timing game shapes', async () => {
    const resource = await loadManifest('fixtures/resource-market.json');
    const textQuest = await loadManifest('fixtures/text-quest.json');
    const timing = await loadManifest('fixtures/timing-gate.json');
    const resourceAdapter: TargetAdapter = {
      version: 1, id: 'resource-market-eval', targetId: resource.id,
      objectives: [{ id: 'purchase', kind: 'completion', description: 'Purchase the beacon', priority: 100 }],
      analyze({ observation }) {
        const text = observation.text;
        return {
          mechanics: [
            ...(includes(text, 'HELP / CONTROLS') ? ['help-system'] : []),
            ...(includes(text, 'MINING COMPLETE') ? ['mining'] : []),
            ...(includes(text, 'INVENTORY') ? ['inventory'] : []),
            ...(includes(text, 'LOCKED: NEED') ? ['purchase-requirement'] : []),
            ...(includes(text, 'INVALID MARKET ACTION') ? ['invalid-input'] : []),
            ...(includes(text, 'BEACON PURCHASED') ? ['purchase'] : []),
          ],
          milestones: [
            ...(includes(text, 'MINING COMPLETE') ? ['ore-collected'] : []),
            ...(includes(text, 'BEACON PURCHASED') ? ['beacon-purchased'] : []),
          ],
          completion: includes(text, 'MARKET MISSION COMPLETE'),
          recoverable: includes(text, 'HELP / CONTROLS') || includes(text, 'INVENTORY'),
        };
      },
    };
    const textAdapter: TargetAdapter = {
      version: 1, id: 'text-quest-eval', targetId: textQuest.id,
      objectives: [{ id: 'door-opened', kind: 'completion', description: 'Open the locked door', priority: 100 }],
      analyze({ observation }) {
        const text = observation.text;
        return {
          mechanics: [
            ...(includes(text, 'ROOM: ARCHIVE') ? ['inspection'] : []),
            ...(includes(text, 'ITEM ACQUIRED') ? ['item-acquisition'] : []),
            ...(includes(text, 'INVENTORY:') ? ['inventory-command'] : []),
            ...(includes(text, 'LOCKED:') ? ['locked-door'] : []),
            ...(includes(text, 'DOOR OPEN') ? ['door-navigation'] : []),
            ...(includes(text, 'UNKNOWN COMMAND') ? ['unknown-command'] : []),
          ],
          milestones: [
            ...(includes(text, 'ITEM ACQUIRED') ? ['key-acquired'] : []),
            ...(includes(text, 'DOOR OPEN') ? ['door-opened'] : []),
          ],
          completion: includes(text, 'TEXT QUEST COMPLETE'),
        };
      },
    };
    const timingAdapter: TargetAdapter = {
      version: 1, id: 'timing-gate-eval', targetId: timing.id,
      objectives: [{ id: 'timing-window', kind: 'completion', description: 'Fire within the timing window', priority: 100 }],
      analyze({ observation }) {
        const text = observation.text;
        return {
          mechanics: [
            ...(includes(text, 'CHARGING:') ? ['charge'] : []),
            ...(includes(text, 'TOO EARLY') ? ['premature-fire'] : []),
            ...(includes(text, 'RESET COMPLETE') ? ['reset'] : []),
            ...(includes(text, 'PERFECT TIMING') ? ['timing-window'] : []),
          ],
          milestones: includes(text, 'GATE TRIAL COMPLETE') ? ['gate-opened'] : [],
          completion: includes(text, 'GATE TRIAL COMPLETE'),
          recoverable: includes(text, 'TOO EARLY') || includes(text, 'ERROR: CHARGE FIRST'),
        };
      },
    };
    const suite = await runEvaluationSuite([
      {
        scenario: { id: 'resource-shape', targetId: resource.id, expectedMechanics: ['help-system', 'mining', 'inventory', 'purchase-requirement', 'invalid-input', 'purchase'], expectedMilestones: ['ore-collected', 'beacon-purchased'], expectedTags: ['help', 'inventory', 'resource', 'error', 'completion'], requireCompletion: true },
        manifest: resource, adapter: resourceAdapter, autonomy: { episodes: 36, maxActionsPerEpisode: 4, maxElapsedMs: 55_000, seed: 11 },
      },
      {
        scenario: { id: 'text-shape', targetId: textQuest.id, expectedMechanics: ['inspection', 'item-acquisition', 'inventory-command', 'locked-door', 'door-navigation', 'unknown-command'], expectedMilestones: ['key-acquired', 'door-opened'], expectedTags: ['text-entry', 'inventory', 'navigation', 'error', 'completion'], requireCompletion: true },
        manifest: textQuest, adapter: textAdapter, autonomy: { episodes: 32, maxActionsPerEpisode: 3, maxElapsedMs: 55_000, seed: 12 },
      },
      {
        scenario: { id: 'timing-shape', targetId: timing.id, expectedMechanics: ['charge', 'premature-fire', 'reset', 'timing-window'], expectedMilestones: ['gate-opened'], expectedTags: ['timing', 'error', 'completion'], requireCompletion: true },
        manifest: timing, adapter: timingAdapter, autonomy: { episodes: 20, maxActionsPerEpisode: 5, maxElapsedMs: 35_000, seed: 13 },
      },
    ]);
    expect(suite.evaluations, JSON.stringify(suite.evaluations, null, 2)).toHaveLength(3);
    expect(suite.passed, JSON.stringify(suite.evaluations, null, 2)).toBe(true);
    expect(suite.evaluations.every(evaluation => evaluation.cleanupFailures === 0)).toBe(true);
    expect(suite.evaluations.every(evaluation => evaluation.contributingAgents.length >= 2)).toBe(true);
  }, 130_000);
});
