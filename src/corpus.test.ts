import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { ActionCorpus, loadCorpus, saveCorpus } from './corpus.js';
import type { TargetManifest } from './types.js';

describe('action corpus', () => {
  it('deduplicates structural states and preserves the first prefix', () => {
    const corpus = new ActionCorpus();
    expect(corpus.record('one', [{ key: 'a' }], 1)).toBe(true);
    expect(corpus.record('one', [{ key: 'b' }], 2)).toBe(false);
    expect(corpus.record('two', [{ key: 'a' }, { key: 'b' }], 2)).toBe(true);
    expect(corpus.size).toBe(2);
    expect(corpus.entries[0]?.actions).toEqual([{ key: 'a' }]);
  });

  it('replaces a state prefix only when the new prefix is shorter', () => {
    const corpus = new ActionCorpus();
    corpus.record('one', [{ key: 'a' }, { key: 'b' }], 2);
    expect(corpus.record('one', [{ key: 'a' }], 1)).toBe(false);
    expect(corpus.entries[0]?.actions).toEqual([{ key: 'a' }]);
  });

  it('persists only for a compatible target', async () => {
    const root = await mkdtemp(join(tmpdir(), 'playtestr-corpus-'));
    try {
      const path = join(root, 'corpus.json');
      const manifest: TargetManifest = { schemaVersion: 1, id: 'game', command: 'node', args: ['game.mjs'], allowedKeys: ['a'] };
      const corpus = new ActionCorpus();
      corpus.record('state', [{ key: 'a' }], 1);
      await saveCorpus(corpus, manifest, path);
      expect((await loadCorpus(path, manifest)).entries).toEqual(corpus.entries);
      await expect(loadCorpus(path, { ...manifest, allowedKeys: ['b'] })).rejects.toThrow('compatibility');
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
