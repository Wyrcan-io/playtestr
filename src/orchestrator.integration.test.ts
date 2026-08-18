import { describe, expect, it } from 'vitest';
import { loadManifest } from './manifest.js';
import { autonomousPlaytest } from './orchestrator.js';
import { autonomyDeterminismSignature } from './evaluation.js';

describe('multi-agent autonomy', () => {
  it('shares frontier knowledge and discovers a hidden sequence', async () => {
    const manifest = await loadManifest('fixtures/hidden-route.json');
    const result = await autonomousPlaytest(manifest, { episodes: 18, maxActionsPerEpisode: 3, maxElapsedMs: 30_000, seed: 3, stopOnHidden: true });
    expect(result.world.hiddenPrefixes.some(prefix => prefix.map(action => action.key).join('') === 'aab')).toBe(true);
    expect(result.stopReason).toBe('hidden-found');
    expect(result.contributions.filter(contribution => contribution.selectedEpisodes > 0).length).toBeGreaterThan(1);
    expect(result.episodeRecords.every(record => record.report.cleanup.confirmedExited)).toBe(true);
    const repeated = await autonomousPlaytest(manifest, { episodes: 18, maxActionsPerEpisode: 3, maxElapsedMs: 30_000, seed: 3, stopOnHidden: true });
    expect(autonomyDeterminismSignature(repeated)).toBe(autonomyDeterminismSignature(result));
  }, 60_000);
});
