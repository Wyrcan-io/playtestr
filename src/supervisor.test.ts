import { describe, expect, it } from 'vitest';
import { ProviderSupervisedAgent, type SupervisorProvider } from './supervisor.js';
import { WorldModel } from './world-model.js';
import type { AgentContext } from './autonomy-types.js';

const context: AgentContext = {
  manifest: { schemaVersion: 1, id: 'game', command: 'node' },
  world: new WorldModel('game').snapshot(),
  allowedActions: ['a', 'b'],
  maxActionsPerEpisode: 2,
  seed: 1,
};

describe('provider-supervised agent', () => {
  it('accepts bounded allowed proposals and rejects executable policy violations', async () => {
    const provider: SupervisorProvider = {
      id: 'fixture',
      version: '1',
      propose: () => [
        { objectiveId: 'explore', actions: [{ key: 'a' }], score: 50, reasons: ['unseen'] },
        { objectiveId: 'escape', actions: [{ key: 'shell:rm' }], score: 100 },
      ],
    };
    const proposals = await new ProviderSupervisedAgent(provider).propose(context);
    expect(proposals).toHaveLength(1);
    expect(proposals[0]).toMatchObject({ agentId: 'supervisor:fixture', actions: [{ key: 'a' }] });
  });

  it('degrades to no proposals on provider failure', async () => {
    const provider: SupervisorProvider = { id: 'broken', version: '1', propose() { throw new Error('offline'); } };
    await expect(new ProviderSupervisedAgent(provider).propose(context)).resolves.toEqual([]);
  });
});
