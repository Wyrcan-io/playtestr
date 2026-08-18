import { baselinePolicy } from './agents.js';
import { ActionCorpus } from './corpus.js';
import { fingerprintObservation } from './observations.js';
import { checkObservation } from './oracles.js';
import { createReplay } from './replay.js';
import { PtyTerminalSession } from './terminal.js';
import type { ActionPolicy, InputAction, RunOptions, RunReport, TargetManifest, TerminalObservation } from './types.js';

export interface RunnerOptions {
  policy?: ActionPolicy;
  corpus?: ActionCorpus;
}

export class PlaytestRunner {
  private readonly policy?: ActionPolicy;
  private readonly corpus?: ActionCorpus;

  constructor(options: RunnerOptions = {}) {
    this.policy = options.policy;
    this.corpus = options.corpus;
  }

  async run(manifest: TargetManifest, options: RunOptions = {}): Promise<RunReport> {
    const viewport = {
      cols: options.viewport?.cols ?? manifest.terminal?.cols ?? 80,
      rows: options.viewport?.rows ?? manifest.terminal?.rows ?? 24,
    };
    const maxActions = options.maxActions ?? 100;
    const maxElapsedMs = options.maxElapsedMs ?? manifest.episodeTimeoutMs ?? 30000;
    const maxStalledSteps = options.maxStalledSteps ?? 20;
    const actions: InputAction[] = [];
    const observations: TerminalObservation[] = [];
    const findings = [] as RunReport['findings'];
    const corpus = this.corpus ?? new ActionCorpus();
    const seenStates = new Set<string>();
    let novelTransitions = 0;
    const startedAt = Date.now();
    let status: RunReport['status'] = 'passed';
    let session: PtyTerminalSession | undefined;
    let stalledSteps = 0;

    try {
      session = await PtyTerminalSession.start({ manifest, seed: options.seed, viewport });
      const record = (): TerminalObservation => {
        const current = session!.observe();
        const previous = observations.at(-1);
        observations.push(current);
        options.onObservation?.(current);
        const fingerprint = fingerprintObservation(current);
        const wasNovel = corpus.record(fingerprint.structural, actions, actions.length);
        seenStates.add(fingerprint.structural);
        if (wasNovel && previous) novelTransitions += 1;
        stalledSteps = previous && !current.changed ? stalledSteps + 1 : 0;
        findings.push(...checkObservation(current, actions.length));
        return current;
      };
      record();
      const policy = this.policy ?? baselinePolicy(manifest.allowedKeys);
      const scripted = options.actions;
      while (actions.length < maxActions) {
        if (Date.now() - startedAt >= maxElapsedMs) {
          status = 'timed-out';
          findings.push({ kind: 'timeout', severity: 'error', message: 'Episode time limit reached.', atAction: actions.length });
          break;
        }
        if (stalledSteps >= maxStalledSteps) {
          status = 'stalled';
          findings.push({ kind: 'stall', severity: 'warning', message: 'No visible progress was observed for the configured number of steps.', atAction: actions.length });
          break;
        }
        const observation = observations.at(-1)!;
        const action = scripted
          ? scripted[actions.length]
          : policy({ observation, history: observations, actions, seenStates });
        if (!action) break;
        actions.push(action);
        await session.send({ ...action, waitMs: action.waitMs ?? manifest.stepTimeoutMs ?? 250 });
        record();
        if (await session.waitForExit(25)) record();
        if (!observations.at(-1)!.processAlive) break;
      }
      if (observations.at(-1)?.processAlive) {
        await session.waitForExit(manifest.exitGraceMs ?? 1100);
        if (!session.observe().processAlive) record();
      }
      if (findings.some(finding => finding.severity === 'error') && status === 'passed') status = 'failed';
    } catch (error) {
      status = 'crashed';
      findings.push({ kind: 'crash', severity: 'error', message: error instanceof Error ? error.message : String(error), atAction: actions.length });
    } finally {
      await session?.stop();
    }

    const elapsedMs = Date.now() - startedAt;
    return {
      targetId: manifest.id,
      status,
      seed: options.seed,
      actionCount: actions.length,
      elapsedMs,
      actions,
      observations,
      findings,
      uniqueStates: seenStates.size,
      novelTransitions,
      corpusSize: corpus.size,
      terminalText: observations.at(-1)?.text ?? '',
      replay: createReplay(manifest, options.seed, viewport, actions),
    };
  }
}
