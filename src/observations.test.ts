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

  it('masks explicitly declared volatile screen regions', () => {
    const first = fingerprintObservation(observation('TIME 10\nSCORE 4'), { volatilePatterns: ['TIME \\d+'] });
    const second = fingerprintObservation(observation('TIME 11\nSCORE 4'), { volatilePatterns: ['TIME \\d+'] });
    const scoreChange = fingerprintObservation(observation('TIME 11\nSCORE 5'), { volatilePatterns: ['TIME \\d+'] });
    expect(first.structural).toBe(second.structural);
    expect(second.structural).not.toBe(scoreChange.structural);
  });
});
