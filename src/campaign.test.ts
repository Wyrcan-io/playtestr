import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CampaignRevisionError, createCampaign, loadCampaign, saveCampaign } from './campaign.js';
import type { TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'campaign-game', command: 'node', args: ['game.mjs'], allowedKeys: ['a'] };

describe('campaign persistence', () => {
  it('atomically saves and reloads compatible revisioned state', async () => {
    const root = await mkdtemp(join(tmpdir(), 'playtestr-campaign-'));
    try {
      const file = join(root, 'campaign.json');
      const first = await saveCampaign(createCampaign(manifest), manifest, file);
      expect(first.revision).toBe(1);
      expect(first.world.version).toBe(2);
      expect(first.agentLearning).toEqual({ version: 1, totalSelections: 0, records: [] });
      expect(await loadCampaign(file, manifest)).toEqual(first);
      const second = await saveCampaign(first, manifest, file);
      expect(second.revision).toBe(2);
      await expect(saveCampaign(first, manifest, file)).rejects.toBeInstanceOf(CampaignRevisionError);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  it('rejects campaign evidence after a manifest compatibility change', async () => {
    const root = await mkdtemp(join(tmpdir(), 'playtestr-campaign-'));
    try {
      const file = join(root, 'campaign.json');
      await saveCampaign(createCampaign(manifest), manifest, file);
      await expect(loadCampaign(file, { ...manifest, allowedKeys: ['b'] })).rejects.toThrow('compatibility');
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
