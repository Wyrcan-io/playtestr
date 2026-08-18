import { describe, expect, it } from 'vitest';
import { encodeKey } from './terminal.js';
import { createReplay } from './replay.js';
import type { TargetManifest } from './types.js';

const manifest: TargetManifest = { id: 'fixture', command: 'node', args: ['fixture.mjs'] };

describe('playtestr primitives', () => {
  it('encodes terminal keys', () => {
    expect(encodeKey('ArrowRight')).toBe('\x1b[C');
    expect(encodeKey('Enter')).toBe('\r');
    expect(encodeKey('x')).toBe('x');
  });

  it('creates versioned deterministic replays', () => {
    const replay = createReplay(manifest, 42, { cols: 80, rows: 24 }, [{ key: 'Enter', waitMs: 10 }]);
    expect(replay).toEqual({
      version: 1,
      targetId: 'fixture',
      command: 'node',
      args: ['fixture.mjs'],
      seed: 42,
      terminal: { cols: 80, rows: 24 },
      actions: [{ key: 'Enter', waitMs: 10 }],
    });
  });
});
