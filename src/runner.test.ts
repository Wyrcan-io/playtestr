import { describe, expect, it } from 'vitest';
import { encodeKey } from './terminal.js';
import { createReplay, parseReplay } from './replay.js';
import type { TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'fixture', command: 'node', args: ['fixture.mjs'] };

describe('playtestr primitives', () => {
  it('encodes terminal keys', () => {
    expect(encodeKey('ArrowRight')).toBe('\x1b[C');
    expect(encodeKey('Enter')).toBe('\r');
    expect(encodeKey('x')).toBe('x');
  });

  it('creates versioned deterministic replays', () => {
    const replay = createReplay(manifest, 42, { cols: 80, rows: 24 }, [{ key: 'Enter', waitMs: 10 }]);
    expect(replay).toMatchObject({
      version: 2,
      targetId: 'fixture',
      command: 'node',
      args: ['fixture.mjs'],
      seed: 42,
      terminal: { cols: 80, rows: 24 },
      actions: [{ key: 'Enter', waitMs: 10 }],
      backend: { id: 'local-pty', capabilities: { isolation: 'none' } },
    });
    expect(replay.targetManifestHash).toMatch(/^[a-f0-9]{64}$/u);
    expect(replay.targetArtifactHash).toMatch(/^[a-f0-9]{64}$/u);
    expect(createReplay(manifest, 42, { cols: 80, rows: 24 }, [{ key: 'Enter', waitMs: 10 }])).toEqual(replay);
  });

  it('migrates Replay V1 to backend-aware Replay V2', () => {
    const migrated = parseReplay({ version: 1, targetId: 'fixture', command: 'node', args: ['fixture.mjs'], terminal: { cols: 80, rows: 24 }, actions: [{ key: 'x' }] });
    expect(migrated).toMatchObject({ version: 2, targetId: 'fixture', backend: { id: 'legacy-local-pty' }, actions: [{ key: 'x' }] });
    expect(parseReplay(migrated)).toEqual(migrated);
  });
});
