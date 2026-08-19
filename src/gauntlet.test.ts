import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { loadGauntlet } from './gauntlet.js';

describe('gauntlet suite', () => {
  it('loads the committed classified fixture matrix', async () => {
    const { suite } = await loadGauntlet('fixtures/gauntlet.v1.json');
    expect(suite.scenarios.length).toBeGreaterThanOrEqual(10);
    expect(new Set(suite.scenarios.map(scenario => scenario.kind))).toEqual(new Set(['discovery', 'robustness', 'lifecycle']));
  });

  it('loads the frozen Agent Advantage validation suite', async () => {
    const { suite } = await loadGauntlet('fixtures/held-out/agent-advantage.v1.json');
    expect(suite.id).toBe('playtestr-agent-advantage-held-out-v1');
    expect(suite.scenarios).toHaveLength(5);
    expect(suite.scenarios.every(scenario => scenario.kind === 'discovery')).toBe(true);
    expect(suite.scenarios.flatMap(scenario => scenario.seeds)).toHaveLength(10);
  });

  it('rejects manifests that escape the suite directory', async () => {
    const root = await mkdtemp(join(tmpdir(), 'playtestr-gauntlet-'));
    try {
      const file = join(root, 'suite.json');
      await writeFile(file, JSON.stringify({ version: 1, id: 'unsafe', scenarios: [{ id: 'bad', kind: 'discovery', manifest: '../game.json', seeds: [0], episodes: 1, maxActionsPerEpisode: 1 }] }));
      await expect(loadGauntlet(file)).rejects.toThrow('escapes');
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
