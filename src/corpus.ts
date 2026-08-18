import type { CorpusEntry, InputAction } from './types.js';

export class ActionCorpus {
  private readonly entriesByFingerprint = new Map<string, CorpusEntry>();

  get size(): number {
    return this.entriesByFingerprint.size;
  }

  get entries(): readonly CorpusEntry[] {
    return [...this.entriesByFingerprint.values()];
  }

  record(fingerprint: string, actions: readonly InputAction[], firstSeenAtAction: number): boolean {
    if (this.entriesByFingerprint.has(fingerprint)) return false;
    this.entriesByFingerprint.set(fingerprint, {
      fingerprint,
      actions: [...actions],
      firstSeenAtAction,
    });
    return true;
  }

  clear(): void {
    this.entriesByFingerprint.clear();
  }
}
