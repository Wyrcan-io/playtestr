import { minimizeSequence, type MinimizeResult } from './minimize.js';
import { reproduceFinding, type ReplayRunner, type ReproductionResult } from './reproduce.js';
import type { InputAction, Replay, TargetManifest } from './types.js';

export interface FindingMinimizeOptions {
  maxAttempts?: number;
  maxElapsedMs?: number;
  candidateAttempts?: number;
  candidateRequiredMatches?: number;
  finalAttempts?: number;
  finalRequiredMatches?: number;
  signal?: AbortSignal;
}

export interface FindingMinimizeResult {
  signature: string;
  originalLength: number;
  replay: Replay;
  minimization: MinimizeResult<InputAction>;
  initialReproduction: ReproductionResult;
  finalReproduction: ReproductionResult;
}

export async function minimizeFindingReplay(
  runner: ReplayRunner,
  manifest: TargetManifest,
  replay: Replay,
  signature: string,
  options: FindingMinimizeOptions = {},
): Promise<FindingMinimizeResult> {
  const maxElapsedMs = options.maxElapsedMs ?? 60_000;
  const startedAt = Date.now();
  const remaining = (): number => Math.max(1, maxElapsedMs - (Date.now() - startedAt));
  const candidateAttempts = options.candidateAttempts ?? 2;
  const candidateRequiredMatches = options.candidateRequiredMatches ?? candidateAttempts;
  const initialReproduction = await reproduceFinding(runner, manifest, replay, signature, {
    attempts: candidateAttempts,
    requiredMatches: candidateRequiredMatches,
    maxElapsedMs: remaining(),
    signal: options.signal,
  });
  if (!initialReproduction.quorumMet) throw new Error(`Replay did not satisfy the exact-signature reproduction quorum: ${signature}`);

  const minimization = await minimizeSequence(replay.actions, async candidate => {
    if (options.signal?.aborted || remaining() <= 1) return false;
    const candidateReplay: Replay = { ...replay, actions: [...candidate] };
    const result = await reproduceFinding(runner, manifest, candidateReplay, signature, {
      attempts: candidateAttempts,
      requiredMatches: candidateRequiredMatches,
      maxElapsedMs: remaining(),
      signal: options.signal,
    });
    return result.quorumMet;
  }, {
    maxAttempts: options.maxAttempts,
    maxElapsedMs: remaining(),
    signal: options.signal,
  });

  const minimizedReplay: Replay = { ...replay, actions: minimization.items };
  const finalAttempts = options.finalAttempts ?? 3;
  const finalReproduction = await reproduceFinding(runner, manifest, minimizedReplay, signature, {
    attempts: finalAttempts,
    requiredMatches: options.finalRequiredMatches ?? finalAttempts,
    maxElapsedMs: remaining(),
    signal: options.signal,
  });
  if (!finalReproduction.quorumMet && !options.signal?.aborted) {
    throw new Error(`Minimized replay failed final exact-signature verification: ${signature}`);
  }
  return {
    signature,
    originalLength: replay.actions.length,
    replay: minimizedReplay,
    minimization,
    initialReproduction,
    finalReproduction,
  };
}
