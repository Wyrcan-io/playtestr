import type { ActionPolicy, InputAction } from './types.js';

const commonKeys = ['?', 'h', 'Enter', ' ', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'r', 'q'];

export function baselinePolicy(allowedKeys?: readonly string[]): ActionPolicy {
  const keys = allowedKeys === undefined ? commonKeys : [...allowedKeys];
  let index = 0;
  return context => {
    if (!context.observation.processAlive) return undefined;
    const key = keys[index++ % keys.length];
    return key ? { key, waitMs: 40, label: 'baseline exploration' } : undefined;
  };
}

export function scriptedPolicy(actions: readonly InputAction[]): ActionPolicy {
  let index = 0;
  return () => actions[index++];
}

export function actionDiversityPolicy(allowedKeys?: readonly string[]): ActionPolicy {
  const keys = allowedKeys === undefined ? commonKeys : [...allowedKeys];
  const counts = new Map<string, number>();
  return context => {
    if (!context.observation.processAlive || keys.length === 0) return undefined;
    const key = [...keys].sort((left, right) => (counts.get(left) ?? 0) - (counts.get(right) ?? 0))[0];
    if (!key) return undefined;
    counts.set(key, (counts.get(key) ?? 0) + 1);
    return { key, waitMs: 40, label: 'action-diversity exploration' };
  };
}

export function seededRandomPolicy(allowedKeys?: readonly string[], seed = 0): ActionPolicy {
  const keys = allowedKeys === undefined ? commonKeys : [...allowedKeys];
  let state = seed >>> 0;
  const random = (): number => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4_294_967_296;
  };
  return context => {
    if (!context.observation.processAlive || keys.length === 0) return undefined;
    const key = keys[Math.floor(random() * keys.length)];
    return key ? { key, waitMs: 40, label: 'seeded-random exploration' } : undefined;
  };
}

/** @deprecated This policy balances action use; it is not coverage-guided yet. */
export const explorationPolicy = actionDiversityPolicy;
