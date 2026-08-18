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
