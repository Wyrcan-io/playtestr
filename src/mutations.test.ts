import { describe, expect, it } from 'vitest';
import { generateMutations, mutateWithOperator, type MutationOperator } from './mutations.js';

describe('deterministic replay mutations', () => {
  it('produces deterministic candidates and an append for every key', () => {
    const left = generateMutations([{ key: 'a' }, { key: 'a' }], ['a', 'b'], 42);
    expect(left).toEqual(generateMutations([{ key: 'a' }, { key: 'a' }], ['a', 'b'], 42));
    expect(left.some(candidate => candidate.actions.map(action => action.key).join('') === 'aab')).toBe(true);
  });

  it('supports every declared operator without mutating its source', () => {
    const source = [{ key: 'a', waitMs: 40 }, { key: 'b', waitMs: 40 }];
    const operators: MutationOperator[] = ['append', 'insert', 'delete', 'replace', 'repeat', 'splice', 'timing'];
    for (const operator of operators) expect(mutateWithOperator(source, operator, ['a', 'b'], 7, [{ key: 'b' }])).toBeInstanceOf(Array);
    expect(source).toEqual([{ key: 'a', waitMs: 40 }, { key: 'b', waitMs: 40 }]);
  });
});
