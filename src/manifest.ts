import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import type { TargetManifest } from './types.js';

const asPositiveInt = (value: unknown, fallback: number): number =>
  typeof value === 'number' && Number.isInteger(value) && value > 0 ? value : fallback;

export async function loadManifest(file: string): Promise<TargetManifest> {
  const path = resolve(file);
  const raw = JSON.parse(await readFile(path, 'utf8')) as Partial<TargetManifest>;
  if (!raw.id || typeof raw.id !== 'string') throw new Error('Manifest requires a string id');
  if (!raw.command || typeof raw.command !== 'string') throw new Error('Manifest requires a string command');
  if (raw.args !== undefined && (!Array.isArray(raw.args) || raw.args.some(value => typeof value !== 'string'))) {
    throw new Error('Manifest args must be an array of strings');
  }
  return {
    ...raw,
    id: raw.id,
    command: raw.command,
    args: raw.args ?? [],
    terminal: {
      cols: asPositiveInt(raw.terminal?.cols, 80),
      rows: asPositiveInt(raw.terminal?.rows, 24),
    },
    startupTimeoutMs: asPositiveInt(raw.startupTimeoutMs, 3000),
    stepTimeoutMs: asPositiveInt(raw.stepTimeoutMs, 250),
    episodeTimeoutMs: asPositiveInt(raw.episodeTimeoutMs, 30000),
    maxOutputBytes: asPositiveInt(raw.maxOutputBytes, 2_000_000),
  };
}

export function commandWithSeed(manifest: TargetManifest, seed?: number): { command: string; args: string[]; env: Record<string, string> } {
  const args = [...(manifest.args ?? [])];
  const env = { ...(manifest.env ?? {}) };
  if (seed !== undefined && manifest.seed?.mode === 'argv') {
    args.push(manifest.seed.flag ?? '--seed', String(seed));
  }
  if (seed !== undefined && manifest.seed?.mode === 'env') {
    env[manifest.seed.envName ?? 'PLAYTESTR_SEED'] = String(seed);
  }
  return { command: manifest.command, args, env };
}
