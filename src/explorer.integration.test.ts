import { describe, expect, it } from 'vitest';
import { exploreTarget } from './explorer.js';
import { loadManifest } from './manifest.js';

describe('coverage-guided restart exploration', () => {
  it('discovers a hidden multi-step route from saved state prefixes', async () => {
    const manifest = await loadManifest('fixtures/hidden-route.json');
    const result = await exploreTarget(manifest, { episodes: 10, maxActionsPerEpisode: 3, seed: 7 });
    expect(result.reports.some(report => report.terminalText.includes('SECRET SPEEDRUN DOOR'))).toBe(true);
    expect(result.corpus.entries.some(entry => entry.actions.map(action => action.key).join('') === 'aab')).toBe(true);
  }, 20_000);
});
