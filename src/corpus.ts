import { createHash } from 'node:crypto';
import { access, mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import type { CorpusEntry, InputAction, TargetManifest } from './types.js';

export interface CorpusFileV1 {
  version: 1;
  targetId: string;
  targetCompatibilityKey: string;
  entries: CorpusEntry[];
}

function hash(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

export function targetCompatibilityKey(manifest: TargetManifest): string {
  return hash({
    version: 1,
    id: manifest.id,
    command: manifest.command,
    args: manifest.args ?? [],
    terminal: manifest.terminal ?? {},
    allowedKeys: manifest.allowedKeys ?? [],
    envNames: Object.keys(manifest.env ?? {}).sort(),
    envDigest: hash(Object.entries(manifest.env ?? {}).sort(([left], [right]) => left.localeCompare(right))),
  });
}

async function exists(path: string): Promise<boolean> {
  try { await access(path); return true; } catch { return false; }
}

export class ActionCorpus {
  private readonly entriesByFingerprint = new Map<string, CorpusEntry>();

  constructor(entries: readonly CorpusEntry[] = []) {
    for (const entry of entries) this.record(entry.fingerprint, entry.actions, entry.firstSeenAtAction, entry);
  }

  get size(): number {
    return this.entriesByFingerprint.size;
  }

  get entries(): readonly CorpusEntry[] {
    return [...this.entriesByFingerprint.values()].sort((left, right) => left.fingerprint.localeCompare(right.fingerprint));
  }

  record(
    fingerprint: string,
    actions: readonly InputAction[],
    firstSeenAtAction: number,
    metadata: Pick<CorpusEntry, 'discoveredAtEpisode' | 'provenance'> = {},
  ): boolean {
    const existing = this.entriesByFingerprint.get(fingerprint);
    if (existing && existing.actions.length <= actions.length) return false;
    this.entriesByFingerprint.set(fingerprint, {
      fingerprint,
      actions: [...actions],
      firstSeenAtAction,
      ...metadata,
    });
    return existing === undefined;
  }

  clear(): void {
    this.entriesByFingerprint.clear();
  }
}

export function serializeCorpus(corpus: ActionCorpus, manifest: TargetManifest): CorpusFileV1 {
  return {
    version: 1,
    targetId: manifest.id,
    targetCompatibilityKey: targetCompatibilityKey(manifest),
    entries: corpus.entries.map(entry => ({ ...entry, actions: entry.actions.map(action => ({ ...action })) })),
  };
}

export async function saveCorpus(corpus: ActionCorpus, manifest: TargetManifest, file: string): Promise<void> {
  const path = resolve(file);
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${process.pid}-${Date.now()}`;
  const backup = `${path}.backup-${process.pid}-${Date.now()}`;
  let movedExisting = false;
  await writeFile(temporary, `${JSON.stringify(serializeCorpus(corpus, manifest), null, 2)}\n`, 'utf8');
  try {
    if (await exists(path)) {
      await rename(path, backup);
      movedExisting = true;
    }
    try {
      await rename(temporary, path);
    } catch (error) {
      if (movedExisting) await rename(backup, path);
      throw error;
    }
    if (movedExisting) await rm(backup, { force: true });
  } catch (error) {
    await rm(temporary, { force: true });
    throw error;
  }
}

export async function loadCorpus(file: string, manifest: TargetManifest): Promise<ActionCorpus> {
  const parsed = JSON.parse(await readFile(resolve(file), 'utf8')) as Partial<CorpusFileV1>;
  if (parsed.version !== 1 || parsed.targetId !== manifest.id || !Array.isArray(parsed.entries)) {
    throw new Error('Corpus is not a valid V1 file for this target');
  }
  if (parsed.targetCompatibilityKey !== targetCompatibilityKey(manifest)) {
    throw new Error('Corpus target compatibility key does not match the current manifest');
  }
  for (const entry of parsed.entries) {
    if (!entry || typeof entry.fingerprint !== 'string' || !Array.isArray(entry.actions) || !Number.isSafeInteger(entry.firstSeenAtAction)) {
      throw new Error('Corpus contains an invalid entry');
    }
  }
  return new ActionCorpus(parsed.entries);
}
