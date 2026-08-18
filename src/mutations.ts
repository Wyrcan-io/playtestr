import type { InputAction } from './types.js';

export type MutationOperator = 'append' | 'insert' | 'delete' | 'replace' | 'repeat' | 'splice' | 'timing';

export interface MutationCandidate {
  actions: InputAction[];
  operator: MutationOperator;
  seed: number;
}

function randomSource(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4_294_967_296;
  };
}

function choose<T>(values: readonly T[], random: () => number): T | undefined {
  return values[Math.floor(random() * values.length)];
}

export function mutateWithOperator(
  source: readonly InputAction[],
  operator: MutationOperator,
  allowedKeys: readonly string[],
  seed: number,
  partner: readonly InputAction[] = [],
): InputAction[] {
  const random = randomSource(seed);
  const actions = source.map(action => ({ ...action }));
  const key = choose(allowedKeys, random);
  const index = Math.floor(random() * (actions.length + 1));
  if (operator === 'append' && key) actions.push({ key, waitMs: 40, label: 'mutation:append' });
  if (operator === 'insert' && key) actions.splice(index, 0, { key, waitMs: 40, label: 'mutation:insert' });
  if (operator === 'delete' && actions.length > 0) actions.splice(Math.min(index, actions.length - 1), 1);
  if (operator === 'replace' && key && actions.length > 0) actions[Math.min(index, actions.length - 1)] = { key, waitMs: 40, label: 'mutation:replace' };
  if (operator === 'replace' && key && actions.length === 0) actions.push({ key, waitMs: 40, label: 'mutation:replace' });
  if (operator === 'repeat' && actions.length > 0) {
    const selected = actions[Math.min(index, actions.length - 1)]!;
    actions.splice(Math.min(index, actions.length), 0, { ...selected, label: 'mutation:repeat' });
  }
  if (operator === 'splice' && partner.length > 0) {
    const partnerStart = Math.floor(random() * partner.length);
    actions.splice(index, 0, ...partner.slice(partnerStart).map(action => ({ ...action, label: 'mutation:splice' })));
  }
  if (operator === 'timing' && actions.length > 0) {
    const selected = Math.min(index, actions.length - 1);
    actions[selected] = { ...actions[selected]!, waitMs: [0, 10, 100, 250][Math.floor(random() * 4)]!, label: 'mutation:timing' };
  }
  return actions;
}

export function generateMutations(
  source: readonly InputAction[],
  allowedKeys: readonly string[],
  seed: number,
  partner: readonly InputAction[] = [],
): MutationCandidate[] {
  const candidates: MutationCandidate[] = allowedKeys.map((key, index) => ({
    actions: [...source.map(action => ({ ...action })), { key, waitMs: 40, label: 'mutation:append' }],
    operator: 'append',
    seed: seed + index,
  }));
  const operators: MutationOperator[] = ['insert', 'delete', 'replace', 'repeat', 'splice', 'timing'];
  operators.forEach((operator, index) => {
    candidates.push({ actions: mutateWithOperator(source, operator, allowedKeys, seed + allowedKeys.length + index, partner), operator, seed: seed + allowedKeys.length + index });
  });
  const unique = new Map<string, MutationCandidate>();
  for (const candidate of candidates) {
    if (candidate.actions.length === 0 || candidate.actions.some(action => !action.key)) continue;
    unique.set(JSON.stringify(candidate.actions.map(action => [action.key, action.holdMs ?? 0, action.waitMs ?? 0])), candidate);
  }
  return [...unique.values()];
}
