import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { createTargetEnvironment, loadManifest } from './manifest.js';
import type { TargetManifest } from './types.js';

describe('target manifests', () => {
  it('resolves target working directories from the manifest location', async () => {
    const manifest = await loadManifest('fixtures/turn-counter.json');
    expect(manifest.schemaVersion).toBe(1);
    expect(manifest.cwd).toBe(resolve('fixtures'));
  });

  it('does not pass ambient secrets unless explicitly inherited', () => {
    const manifest: TargetManifest = {
      schemaVersion: 1,
      id: 'environment-test',
      command: 'node',
      env: { EXPLICIT: 'yes' },
      inheritEnv: ['OPTED_IN'],
    };
    const env = createTargetEnvironment(manifest, undefined, {
      PATH: 'tools',
      SECRET_TOKEN: 'must-not-leak',
      OPTED_IN: 'allowed',
    });
    expect(env.PATH).toBe('tools');
    expect(env.EXPLICIT).toBe('yes');
    expect(env.OPTED_IN).toBe('allowed');
    expect(env.SECRET_TOKEN).toBeUndefined();
  });

  it('rejects unknown fields instead of silently ignoring policy mistakes', async () => {
    await expect(loadManifest('fixtures/invalid-manifest.json')).rejects.toThrow('unknownPolicy');
  });
});
