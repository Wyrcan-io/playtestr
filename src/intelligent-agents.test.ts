import { describe, expect, it } from 'vitest';
import { defaultAutonomousAgents } from './intelligent-agents.js';
import type { AgentContext } from './autonomy-types.js';

const context: AgentContext = {
  manifest: { schemaVersion: 1, id: 'fixture', command: 'node', allowedKeys: ['a', 'Enter', 'Escape'] },
  world: {
    version: 2,
    targetId: 'fixture',
    episodes: 1,
    states: [{ id: 'state', visits: 1, firstSeenEpisode: 1, shortestPrefix: [], semanticSignature: 'semantic', tags: ['menu'], actionHints: ['a'], milestones: [], terminal: false, completion: false, hidden: false, failure: false, recoverable: false }],
    transitions: [], mechanics: [], milestones: [], objectives: [], completionPrefixes: [], hiddenPrefixes: [],
    actionVocabulary: ['a', 'Enter', 'Escape'], actionOutcomes: [], frontiers: [], prerequisites: [],
  },
  allowedActions: ['a', 'Enter', 'Escape'],
  maxActionsPerEpisode: 4,
  seed: 1,
};

describe('specialized autonomous agents', () => {
  it('implement one deterministic bounded proposal protocol', async () => {
    const agents = defaultAutonomousAgents();
    expect(agents.map(agent => agent.role)).toEqual(['mechanic-mapper', 'edge-case', 'secret-hunter', 'speedrunner', 'completionist', 'recovery']);
    for (const agent of agents) {
      const first = await agent.propose(context);
      expect(first).toEqual(await agent.propose(context));
      expect(first.every(candidate => candidate.actions.length <= context.maxActionsPerEpisode)).toBe(true);
    }
    expect((await agents[0]!.propose(context)).length).toBeGreaterThan(0);
  });
});
