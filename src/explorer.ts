import { ActionCorpus, saveCorpus } from './corpus.js';
import { generateMutations } from './mutations.js';
import { PlaytestRunner } from './runner.js';
import type { InputAction, RunReport, TargetManifest } from './types.js';

export interface ExploreOptions {
  episodes?: number;
  maxActionsPerEpisode?: number;
  maxElapsedMsPerEpisode?: number;
  seed?: number;
  corpus?: ActionCorpus;
  corpusPath?: string;
  signal?: AbortSignal;
}

export interface ExplorationResult {
  episodes: number;
  actionCount: number;
  uniqueStates: number;
  corpus: ActionCorpus;
  reports: RunReport[];
  stopReason: 'complete' | 'cancelled' | 'queue-exhausted';
}

function sequenceKey(actions: readonly InputAction[]): string {
  return JSON.stringify(actions.map(action => action.key));
}

export async function exploreTarget(manifest: TargetManifest, options: ExploreOptions = {}): Promise<ExplorationResult> {
  const episodeBudget = options.episodes ?? 25;
  const maxActions = options.maxActionsPerEpisode ?? 12;
  const corpus = options.corpus ?? new ActionCorpus();
  const reports: RunReport[] = [];
  const queue: InputAction[][] = [[]];
  const queued = new Set<string>([sequenceKey([])]);
  const expandedFingerprints = new Set<string>();
  let actionCount = 0;
  let stopReason: ExplorationResult['stopReason'] = 'complete';

  while (reports.length < episodeBudget) {
    if (options.signal?.aborted) {
      stopReason = 'cancelled';
      break;
    }
    const candidate = queue.shift();
    if (!candidate) {
      stopReason = 'queue-exhausted';
      break;
    }
    const bounded = candidate.slice(0, maxActions);
    const report = await new PlaytestRunner({ corpus }).run(manifest, {
      seed: options.seed,
      actions: bounded,
      maxActions: bounded.length,
      maxElapsedMs: options.maxElapsedMsPerEpisode ?? manifest.episodeTimeoutMs,
      signal: options.signal,
    });
    reports.push(report);
    actionCount += report.actionCount;
    const entries = corpus.entries;
    for (const entry of entries) {
      if (expandedFingerprints.has(entry.fingerprint) || entry.actions.length >= maxActions) continue;
      expandedFingerprints.add(entry.fingerprint);
      const partner = entries[(reports.length + entry.actions.length) % entries.length]?.actions ?? [];
      for (const mutation of generateMutations(entry.actions, manifest.allowedKeys ?? [], (options.seed ?? 0) + reports.length, partner)) {
        if (mutation.actions.length > maxActions) continue;
        const key = sequenceKey(mutation.actions);
        if (!queued.has(key)) {
          queued.add(key);
          queue.push(mutation.actions);
        }
      }
    }
    queue.sort((left, right) => left.length - right.length || sequenceKey(left).localeCompare(sequenceKey(right)));
    if (options.corpusPath) await saveCorpus(corpus, manifest, options.corpusPath);
    if (report.status === 'cancelled') {
      stopReason = 'cancelled';
      break;
    }
  }
  return { episodes: reports.length, actionCount, uniqueStates: corpus.size, corpus, reports, stopReason };
}
