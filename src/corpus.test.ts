import { describe, expect, it } from 'vitest';
import { ActionCorpus } from './corpus.js';

describe('action corpus', () => {
  it('deduplicates structural states and preserves the first prefix', () => {
    const corpus = new ActionCorpus();
    expect(corpus.record('one', [{ key: 'a' }], 1)).toBe(true);
    expect(corpus.record('one', [{ key: 'b' }], 2)).toBe(false);
    expect(corpus.record('two', [{ key: 'a' }, { key: 'b' }], 2)).toBe(true);
    expect(corpus.size).toBe(2);
    expect(corpus.entries[0]?.actions).toEqual([{ key: 'a' }]);
  });
});
