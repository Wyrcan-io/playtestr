import { describe, expect, it } from 'vitest';
import { WorldModel } from './world-model.js';
import type { TargetAdapter } from './adapter.js';
import type { RunReport, TargetManifest, TerminalObservation } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'world-fixture', command: 'node', allowedKeys: ['m'] };
const observation = (text: string, alive = true): TerminalObservation => ({ at: 0, cols: 80, rows: 24, text, lines: text.split('\n'), cursor: { x: 0, y: 0 }, alternateBuffer: false, changed: true, processAlive: alive });
const adapter: TargetAdapter = {
  version: 1,
  id: 'fixture-adapter',
  targetId: manifest.id,
  objectives: [{ id: 'mining', kind: 'mechanic', description: 'Mine ore' }, { id: 'finish', kind: 'completion', description: 'Finish' }],
  analyze({ observation: current }) {
    return {
      mechanics: current.text.includes('Ore: 1') ? ['mining'] : [],
      milestones: current.text.includes('Ore: 1') ? ['ore-collected'] : [],
      completion: current.text.includes('VICTORY'),
    };
  },
};

describe('shared world model', () => {
  it('learns states, transitions, mechanics, counters, milestones, and completion prefixes', async () => {
    const report = {
      targetId: manifest.id,
      actions: [{ key: 'm' }],
      observations: [observation('MINE\nOre: 0'), observation('VICTORY\nOre: 1', false)],
    } as RunReport;
    const world = new WorldModel(manifest.id, adapter);
    const delta = await world.ingest(report, manifest, adapter);
    const snapshot = world.snapshot();
    expect(delta.newStates).toHaveLength(2);
    expect(snapshot.transitions).toHaveLength(1);
    expect(snapshot.mechanics.map(mechanic => mechanic.id)).toEqual(expect.arrayContaining(['mining', 'action:m', 'counter:ore']));
    expect(snapshot.milestones).toContain('ore-collected');
    expect(snapshot.completionPrefixes[0]).toEqual([{ key: 'm' }]);
    expect(snapshot.objectives.every(objective => objective.status === 'complete')).toBe(true);
  });
});
