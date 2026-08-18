import { describe, expect, it } from 'vitest';
import { analyzeTerminalObservation } from './semantics.js';
import type { TerminalObservation } from './types.js';

function observation(text: string): TerminalObservation {
  return { at: 0, cols: 80, rows: 24, text, lines: text.split('\n'), cursor: { x: 0, y: 0 }, alternateBuffer: false, changed: true, processAlive: true };
}

describe('terminal semantics', () => {
  it('extracts stable options, actions, counters, and tags', () => {
    const semantic = analyzeTerminalObservation(observation('TRADING POST\nGold: 12\n[1] Mine ore\n[i] Inventory\nPress Enter to continue'));
    expect(semantic.title).toBe('TRADING POST');
    expect(semantic.actionHints).toEqual(expect.arrayContaining(['1', 'i', 'Enter']));
    expect(semantic.counters.gold).toBe(12);
    expect(semantic.tags).toEqual(expect.arrayContaining(['menu', 'inventory', 'resource', 'confirmation']));
    expect(semantic.signature).toHaveLength(64);
  });

  it('recognizes completion, failure, secret, and text prompts', () => {
    const semantic = analyzeTerminalObservation(observation('SECRET QUEST COMPLETE\nCommand:'));
    expect(semantic.tags).toEqual(expect.arrayContaining(['secret', 'completion', 'text-entry']));
  });
});
