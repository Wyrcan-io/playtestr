import { describe, expect, it } from 'vitest';
import { fingerprintObservation, normalizeScreenText } from './observations.js';

const observation = (text: string, cursor = { x: 0, y: 0 }) => ({
  cols: 80,
  rows: 24,
  text,
  cursor,
  alternateBuffer: false,
});

describe('observation fingerprints', () => {
  it('normalizes trailing terminal whitespace', () => {
    expect(normalizeScreenText('A  \nB\n\n')).toBe('A\nB');
    expect(fingerprintObservation(observation('A  \nB'))).toEqual(fingerprintObservation(observation('A\nB')));
  });

  it('keeps cursor movement distinct in exact fingerprints', () => {
    const first = fingerprintObservation(observation('A', { x: 0, y: 0 }));
    const second = fingerprintObservation(observation('A', { x: 1, y: 0 }));
    expect(first.structural).toBe(second.structural);
    expect(first.exact).not.toBe(second.exact);
  });
});
