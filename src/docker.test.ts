import { describe, expect, it } from 'vitest';
import { createDockerExecutionPlan } from './docker.js';
import type { TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: 'game', command: 'node', args: ['game.mjs'], env: { NO_COLOR: '1' } };

describe('Docker execution planning', () => {
  it('builds a restrictive, mount-free, no-network profile', () => {
    const plan = createDockerExecutionPlan(manifest, { version: 1, image: 'example/game@sha256:abc' }, 'test');
    expect(plan.args).toEqual(expect.arrayContaining(['--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pull', 'never']));
    expect(plan.args).not.toContain('--mount');
    expect(plan.args).not.toContain('NO_COLOR=1');
    expect(plan.environmentNames).toEqual(['NO_COLOR']);
    expect(plan.capabilities.isolation).toBe('container');
  });

  it('requires separate acknowledgement for network and pulling', () => {
    expect(() => createDockerExecutionPlan(manifest, { version: 1, image: 'example/game', network: 'bridge' })).toThrow('allowNetwork');
    expect(() => createDockerExecutionPlan(manifest, { version: 1, image: 'example/game', pull: 'missing' })).toThrow('allowPull');
  });
});
