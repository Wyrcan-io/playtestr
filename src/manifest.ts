import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import type { TargetManifest } from './types.js';

const rootKeys = new Set([
  'schemaVersion', 'id', 'command', 'args', 'cwd', 'env', 'inheritEnv', 'terminal', 'observation',
  'requireInitialOutput', 'startupTimeoutMs', 'stepTimeoutMs', 'exitGraceMs', 'episodeTimeoutMs',
  'maxOutputBytes', 'seed', 'allowedKeys',
]);
const environmentName = /^[A-Za-z_][A-Za-z0-9_]*$/u;

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function rejectUnknownKeys(value: Record<string, unknown>, allowed: ReadonlySet<string>, label: string): void {
  const unknown = Object.keys(value).filter(key => !allowed.has(key));
  if (unknown.length) throw new Error(`${label} contains unknown field(s): ${unknown.join(', ')}`);
}

function stringValue(value: unknown, label: string): string {
  if (typeof value !== 'string' || value.length === 0) throw new Error(`${label} must be a non-empty string`);
  return value;
}

function stringArray(value: unknown, label: string): string[] {
  if (!Array.isArray(value) || value.some(item => typeof item !== 'string' || item.length === 0)) {
    throw new Error(`${label} must be an array of non-empty strings`);
  }
  return [...value];
}

function positiveInt(value: unknown, label: string, fallback: number): number {
  if (value === undefined) return fallback;
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${label} must be a positive safe integer`);
  }
  return value;
}

function optionalBoolean(value: unknown, label: string, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  if (typeof value !== 'boolean') throw new Error(`${label} must be a boolean`);
  return value;
}

function stringRecord(value: unknown, label: string): Record<string, string> {
  if (value === undefined) return {};
  const source = object(value, label);
  const result: Record<string, string> = {};
  for (const [key, item] of Object.entries(source)) {
    if (!environmentName.test(key)) throw new Error(`${label} contains invalid environment name: ${key}`);
    if (typeof item !== 'string') throw new Error(`${label}.${key} must be a string`);
    result[key] = item;
  }
  return result;
}

export async function loadManifest(file: string): Promise<TargetManifest> {
  const path = resolve(file);
  let parsed: unknown;
  try {
    parsed = JSON.parse(await readFile(path, 'utf8'));
  } catch (error) {
    throw new Error(`Cannot read manifest ${path}: ${error instanceof Error ? error.message : String(error)}`);
  }
  const raw = object(parsed, 'Manifest');
  rejectUnknownKeys(raw, rootKeys, 'Manifest');
  if (raw.schemaVersion !== 1) throw new Error('Manifest schemaVersion must be 1');

  const terminal = raw.terminal === undefined ? {} : object(raw.terminal, 'Manifest terminal');
  rejectUnknownKeys(terminal, new Set(['cols', 'rows']), 'Manifest terminal');

  const observation = raw.observation === undefined ? {} : object(raw.observation, 'Manifest observation');
  rejectUnknownKeys(observation, new Set(['volatilePatterns']), 'Manifest observation');
  const volatilePatterns = observation.volatilePatterns === undefined
    ? []
    : stringArray(observation.volatilePatterns, 'Manifest observation.volatilePatterns');
  for (const pattern of volatilePatterns) {
    try { new RegExp(pattern, 'g'); } catch { throw new Error(`Invalid volatile pattern: ${pattern}`); }
  }

  const seed = raw.seed === undefined ? undefined : object(raw.seed, 'Manifest seed');
  if (seed) {
    rejectUnknownKeys(seed, new Set(['mode', 'flag', 'envName']), 'Manifest seed');
    if (seed.mode !== 'argv' && seed.mode !== 'env') throw new Error('Manifest seed.mode must be argv or env');
    if (seed.flag !== undefined) stringValue(seed.flag, 'Manifest seed.flag');
    if (seed.envName !== undefined && !environmentName.test(stringValue(seed.envName, 'Manifest seed.envName'))) {
      throw new Error('Manifest seed.envName is not a valid environment name');
    }
  }

  const inheritEnv = raw.inheritEnv === undefined ? [] : [...new Set(stringArray(raw.inheritEnv, 'Manifest inheritEnv'))];
  for (const name of inheritEnv) {
    if (!environmentName.test(name)) throw new Error(`Manifest inheritEnv contains invalid environment name: ${name}`);
  }

  return {
    schemaVersion: 1,
    id: stringValue(raw.id, 'Manifest id'),
    command: stringValue(raw.command, 'Manifest command'),
    args: raw.args === undefined ? [] : stringArray(raw.args, 'Manifest args'),
    cwd: resolve(dirname(path), raw.cwd === undefined ? '.' : stringValue(raw.cwd, 'Manifest cwd')),
    env: stringRecord(raw.env, 'Manifest env'),
    inheritEnv,
    terminal: {
      cols: positiveInt(terminal.cols, 'Manifest terminal.cols', 80),
      rows: positiveInt(terminal.rows, 'Manifest terminal.rows', 24),
    },
    observation: { volatilePatterns },
    requireInitialOutput: optionalBoolean(raw.requireInitialOutput, 'Manifest requireInitialOutput', true),
    startupTimeoutMs: positiveInt(raw.startupTimeoutMs, 'Manifest startupTimeoutMs', 3000),
    stepTimeoutMs: positiveInt(raw.stepTimeoutMs, 'Manifest stepTimeoutMs', 250),
    exitGraceMs: positiveInt(raw.exitGraceMs, 'Manifest exitGraceMs', 2500),
    episodeTimeoutMs: positiveInt(raw.episodeTimeoutMs, 'Manifest episodeTimeoutMs', 30000),
    maxOutputBytes: positiveInt(raw.maxOutputBytes, 'Manifest maxOutputBytes', 2_000_000),
    seed: seed ? {
      mode: seed.mode as 'argv' | 'env',
      ...(seed.flag === undefined ? {} : { flag: seed.flag as string }),
      ...(seed.envName === undefined ? {} : { envName: seed.envName as string }),
    } : undefined,
    allowedKeys: raw.allowedKeys === undefined ? undefined : stringArray(raw.allowedKeys, 'Manifest allowedKeys'),
  };
}

const operationalEnvironmentNames = process.platform === 'win32'
  ? ['SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'Path', 'PATHEXT', 'TEMP', 'TMP']
  : ['PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR'];

export function createTargetEnvironment(
  manifest: TargetManifest,
  seed?: number,
  source: NodeJS.ProcessEnv = process.env,
): Record<string, string> {
  const env: Record<string, string> = {};
  for (const name of [...operationalEnvironmentNames, ...(manifest.inheritEnv ?? [])]) {
    const value = source[name];
    if (value !== undefined) env[name] = value;
  }
  Object.assign(env, manifest.env ?? {});
  if (seed !== undefined && manifest.seed?.mode === 'env') {
    env[manifest.seed.envName ?? 'PLAYTESTR_SEED'] = String(seed);
  }
  return env;
}

export function commandWithSeed(manifest: TargetManifest, seed?: number): { command: string; args: string[]; env: Record<string, string> } {
  const args = [...(manifest.args ?? [])];
  if (seed !== undefined && manifest.seed?.mode === 'argv') {
    args.push(manifest.seed.flag ?? '--seed', String(seed));
  }
  return { command: manifest.command, args, env: createTargetEnvironment(manifest, seed) };
}
