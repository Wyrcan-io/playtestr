import { describe, expect, it } from 'vitest';
import { minimizeSequence } from './minimize.js';

describe('replay minimizer', () => {
  it('removes actions that are not required for the predicate', async () => {
    const result = await minimizeSequence(['noise', 'keep', 'noise', 'keep'], async candidate => candidate.includes('keep'), { maxAttempts: 30 });
    expect(result.items).toEqual(['keep']);
    expect(result.attempts).toBeGreaterThan(0);
  });
});
