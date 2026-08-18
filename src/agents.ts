import type { ActionPolicy, InputAction } from './types.js';

const commonKeys = ['?', 'h', 'Enter', ' ', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'r', 'q'];

export function baselinePolicy(allowedKeys?: readonly string[]): ActionPolicy {
  const keys = allowedKeys?.length ? [...allowedKeys] : commonKeys;
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

export function explorationPolicy(allowedKeys?: readonly string[]): ActionPolicy {
  const keys = allowedKeys?.length ? [...allowedKeys] : commonKeys;
  const counts = new Map<string, number>();
  return context => {
    if (!context.observation.processAlive || keys.length === 0) return undefined;
    const key = [...keys].sort((left, right) => (counts.get(left) ?? 0) - (counts.get(right) ?? 0))[0];
    if (!key) return undefined;
    counts.set(key, (counts.get(key) ?? 0) + 1);
    return { key, waitMs: 40, label: 'novelty exploration' };
  };
}
