export interface MinimizeOptions {
  maxAttempts?: number;
  minChunkSize?: number;
}

export interface MinimizeResult<T> {
  items: T[];
  attempts: number;
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

  while (current.length >= minChunkSize && attempts < maxAttempts) {
    const chunkSize = Math.ceil(current.length / chunkCount);
    let reduced = false;
    for (let start = 0; start < current.length && attempts < maxAttempts; start += chunkSize) {
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
    if (!reduced) {
      if (chunkCount >= current.length) break;
      chunkCount = Math.min(current.length, chunkCount * 2);
    }
  }
  return { items: current, attempts };
}
