export interface MinimizeOptions {
  maxAttempts?: number;
  minChunkSize?: number;
  maxElapsedMs?: number;
  signal?: AbortSignal;
}

export interface MinimizeResult<T> {
  items: T[];
  attempts: number;
  stopReason: 'complete' | 'max-attempts' | 'time-budget' | 'cancelled';
}

/** Delta-debug an ordered replay while preserving an async failure predicate. */
export async function minimizeSequence<T>(
  source: readonly T[],
  reproduces: (candidate: readonly T[]) => Promise<boolean>,
  options: MinimizeOptions = {},
): Promise<MinimizeResult<T>> {
  let current = [...source];
  let attempts = 0;
  let chunkCount = 2;
  const maxAttempts = options.maxAttempts ?? 100;
  const minChunkSize = Math.max(1, options.minChunkSize ?? 1);
  const maxElapsedMs = options.maxElapsedMs ?? 30_000;
  const startedAt = Date.now();
  let stopReason: MinimizeResult<T>['stopReason'] = 'complete';

  while (current.length >= minChunkSize && attempts < maxAttempts) {
    if (options.signal?.aborted) {
      stopReason = 'cancelled';
      break;
    }
    if (Date.now() - startedAt >= maxElapsedMs) {
      stopReason = 'time-budget';
      break;
    }
    const chunkSize = Math.ceil(current.length / chunkCount);
    let reduced = false;
    for (let start = 0; start < current.length && attempts < maxAttempts; start += chunkSize) {
      if (options.signal?.aborted || Date.now() - startedAt >= maxElapsedMs) break;
      const candidate = current.slice(0, start).concat(current.slice(start + chunkSize));
      if (candidate.length < minChunkSize) continue;
      attempts += 1;
      if (await reproduces(candidate)) {
        current = candidate;
        chunkCount = Math.max(2, chunkCount - 1);
        reduced = true;
        break;
      }
    }
    if (options.signal?.aborted) {
      stopReason = 'cancelled';
      break;
    }
    if (Date.now() - startedAt >= maxElapsedMs) {
      stopReason = 'time-budget';
      break;
    }
    if (!reduced) {
      if (chunkCount >= current.length) break;
      chunkCount = Math.min(current.length, chunkCount * 2);
    }
  }
  if (stopReason === 'complete' && attempts >= maxAttempts) stopReason = 'max-attempts';
  return { items: current, attempts, stopReason };
}
