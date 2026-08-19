import { describe, expect, it } from 'vitest';
import { planWorldFrontiers } from './planner.js';
import type { AgentContext } from './autonomy-types.js';

describe('world frontier planner', () => {
  it('prefers a screen hint and returns through the shortest known prefix', () => {
    const context = {
      manifest: { schemaVersion: 1, id: 'fixture', command: 'node', allowedKeys: ['a', 'z'] },
      allowedActions: ['a', 'z'], maxActionsPerEpisode: 3, seed: 1,
      world: {
        version: 2, targetId: 'fixture', episodes: 2,
        states: [{ id: 'state', visits: 1, firstSeenEpisode: 2, shortestPrefix: [{ key: 'a' }], semanticSignature: 's', tags: [], actionHints: ['z'], options: [{ key: 'z', label: 'Open vault' }], milestones: [], terminal: false, completion: false, hidden: false, failure: false, recoverable: false }],
        transitions: [], mechanics: [], milestones: [], objectives: [], completionPrefixes: [], hiddenPrefixes: [], actionVocabulary: ['a', 'z'], actionOutcomes: [], prerequisites: [],
        frontiers: [
          { id: 'state:a', stateId: 'state', action: { key: 'a' }, attempts: 0, status: 'untried', noveltyYield: 1, expectedReward: 0, priority: 40 },
          { id: 'state:z', stateId: 'state', action: { key: 'z' }, attempts: 0, status: 'untried', noveltyYield: 1, expectedReward: 0, priority: 40 },
        ],
      },
    } satisfies AgentContext;
    const plans = planWorldFrontiers(context);
    expect(plans[0]!.actions.map(action => action.key)).toEqual(['a', 'z']);
    expect(plans[0]!.reasons).toContain('screen-action-hint');
    expect(planWorldFrontiers(context)).toEqual(plans);
  });
});
