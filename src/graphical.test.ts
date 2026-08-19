import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { runGraphicalEpisode, type GraphicalAction, type GraphicalBackend, type GraphicalObservation } from './graphical.js';

describe('graphical backend contract', () => {
  it('runs a bounded deterministic in-memory episode and confirms cleanup', async () => {
    const applied: GraphicalAction[] = [];
    const observation = (): GraphicalObservation => ({ at: applied.length, width: 800, height: 600, frameDigest: createHash('sha256').update(JSON.stringify(applied)).digest('hex'), changed: applied.length > 0 });
    const backend: GraphicalBackend = {
      id: 'memory-graphical',
      capabilities: { isolation: 'browser-context', accessibilityTree: true, screenshots: true, video: false, pointer: true, keyboard: true },
      async start() {
        return { async observe() { return observation(); }, async send(action) { applied.push(action); }, async close() { return { attempted: true, confirmedClosed: true }; } };
      },
    };
    const result = await runGraphicalEpisode(backend, { version: 1, id: 'canvas-game', url: 'http://127.0.0.1/game', viewport: { width: 800, height: 600 } }, [{ kind: 'pointer', x: 0.5, y: 0.5 }, { kind: 'key', key: 'Space' }]);
    expect(result).toMatchObject({ status: 'passed', backendId: 'memory-graphical', cleanup: { confirmedClosed: true } });
    expect(result.observations).toHaveLength(3);
  });

  it('rejects out-of-bounds pointer actions', async () => {
    const backend: GraphicalBackend = {
      id: 'memory',
      capabilities: { isolation: 'none', accessibilityTree: false, screenshots: false, video: false, pointer: true, keyboard: true },
      async start() { return { async observe() { return { at: 0, width: 1, height: 1, frameDigest: 'x', changed: false }; }, async send() {}, async close() { return { attempted: true, confirmedClosed: true }; } }; },
    };
    const result = await runGraphicalEpisode(backend, { version: 1, id: 'game', url: 'local', viewport: { width: 1, height: 1 } }, [{ kind: 'pointer', x: 2, y: 0 }]);
    expect(result.status).toBe('failed');
  });
});
