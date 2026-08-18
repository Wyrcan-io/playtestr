import { access, mkdir, mkdtemp, rename, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, join, parse, resolve } from 'node:path';
import type { RunReport } from './types.js';

export interface ArtifactWriteOptions {
  maxBytes?: number;
  report?: unknown;
}

export interface ArtifactWriteResult {
  root: string;
  bytes: number;
  files: readonly string[];
}

export class ArtifactQuotaError extends Error {
  constructor(readonly actualBytes: number, readonly maxBytes: number) {
    super(`Artifact bundle requires ${actualBytes} bytes, exceeding the ${maxBytes}-byte limit`);
    this.name = 'ArtifactQuotaError';
  }
}

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

export async function writeRunArtifacts(
  run: RunReport,
  artifactRoot: string,
  options: ArtifactWriteOptions = {},
): Promise<ArtifactWriteResult> {
  return writeArtifactBundle(artifactRoot, {
    'report.json': `${JSON.stringify(options.report ?? run, null, 2)}\n`,
    'replay.json': `${JSON.stringify(run.replay, null, 2)}\n`,
    'last-screen.txt': run.terminalText,
  }, options.maxBytes);
}

export async function writeArtifactBundle(
  artifactRoot: string,
  content: Readonly<Record<string, string | Buffer>>,
  byteLimit = 10_000_000,
): Promise<ArtifactWriteResult> {
  const root = resolve(artifactRoot);
  if (root === parse(root).root) throw new Error('Artifact root cannot be a filesystem root');
  const maxBytes = byteLimit;
  if (!Number.isSafeInteger(maxBytes) || maxBytes <= 0) throw new Error('Artifact byte limit must be a positive safe integer');

  const files = new Map<string, Buffer>();
  for (const [filename, value] of Object.entries(content)) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/u.test(filename)) throw new Error(`Unsafe artifact filename: ${filename}`);
    files.set(filename, Buffer.isBuffer(value) ? value : Buffer.from(value, 'utf8'));
  }
  const bytes = [...files.values()].reduce((total, content) => total + content.byteLength, 0);
  if (bytes > maxBytes) throw new ArtifactQuotaError(bytes, maxBytes);

  const parent = dirname(root);
  const name = basename(root);
  await mkdir(parent, { recursive: true });
  const temporary = await mkdtemp(join(parent, `.${name}.tmp-`));
  const backup = join(parent, `.${name}.backup-${process.pid}-${Date.now()}`);
  let movedExisting = false;
  try {
    await Promise.all([...files].map(([filename, content]) => writeFile(join(temporary, filename), content)));
    if (await exists(root)) {
      await rename(root, backup);
      movedExisting = true;
    }
    try {
      await rename(temporary, root);
    } catch (error) {
      if (movedExisting) await rename(backup, root);
      throw error;
    }
    if (movedExisting) await rm(backup, { recursive: true, force: true });
  } catch (error) {
    await rm(temporary, { recursive: true, force: true });
    throw error;
  }
  return { root, bytes, files: [...files.keys()] };
}
