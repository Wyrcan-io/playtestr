import { baselinePolicy } from './agents.js';
import { ActionCorpus } from './corpus.js';
import { fingerprintObservation } from './observations.js';
import { checkObservation } from './oracles.js';
import { createReplay } from './replay.js';
import { PtyTerminalSession } from './terminal.js';
import type { ActionPolicy, InputAction, OracleResult, RunOptions, RunReport, RunTermination, TargetManifest, TerminalObservation } from './types.js';

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
    const startingCorpusSize = corpus.size;
    const seenStates = new Set<string>();
    const seenTransitions = new Set<string>();
    const startedAt = Date.now();
    let status: RunReport['status'] = 'passed';
    let outcome: RunReport['outcome'] = 'truncated';
    let termination: RunTermination = { kind: 'policy-complete', atAction: 0 };
    let session: PtyTerminalSession | undefined;
    let stalledSteps = 0;
    let previousStructural: string | undefined;

    const addFinding = (finding: OracleResult): void => {
      const duplicate = findings.some(existing =>
        existing.kind === finding.kind && existing.atAction === finding.atAction && existing.message === finding.message);
      if (!duplicate) findings.push(finding);
    };

    const timeRemaining = (): number => Math.max(0, maxElapsedMs - (Date.now() - startedAt));
    const completesBeforeDeadline = async (operation: Promise<void>, timeoutMs: number): Promise<boolean> => {
      let timer: NodeJS.Timeout | undefined;
      try {
        return await Promise.race([
          operation.then(() => true),
          new Promise<false>(resolveTimeout => {
            timer = setTimeout(() => resolveTimeout(false), timeoutMs);
          }),
        ]);
      } finally {
        if (timer) clearTimeout(timer);
      }
    };

    try {
      if (!Number.isSafeInteger(maxActions) || maxActions < 0) throw new Error('maxActions must be a non-negative safe integer');
      if (!Number.isSafeInteger(maxElapsedMs) || maxElapsedMs <= 0) throw new Error('maxElapsedMs must be a positive safe integer');
      if (!Number.isSafeInteger(maxStalledSteps) || maxStalledSteps <= 0) throw new Error('maxStalledSteps must be a positive safe integer');
      if (!Number.isSafeInteger(viewport.cols) || viewport.cols <= 0 || !Number.isSafeInteger(viewport.rows) || viewport.rows <= 0) {
        throw new Error('Viewport dimensions must be positive safe integers');
      }
      session = await PtyTerminalSession.start({ manifest, seed: options.seed, viewport });
      const record = (): TerminalObservation => {
        const current = session!.observe();
        observations.push(current);
        options.onObservation?.(current);
        const fingerprint = fingerprintObservation(current, manifest.observation);
        corpus.record(fingerprint.structural, actions, actions.length);
        seenStates.add(fingerprint.structural);
        if (previousStructural !== undefined) {
          const action = actions.at(-1);
          const actionKey = action ? JSON.stringify([action.key, action.holdMs ?? 0, action.waitMs ?? 0]) : '<none>';
          seenTransitions.add(`${previousStructural}:${actionKey}:${fingerprint.structural}`);
          stalledSteps = previousStructural === fingerprint.structural ? stalledSteps + 1 : 0;
        }
        previousStructural = fingerprint.structural;
        const diagnostics = session!.diagnostics();
        for (const finding of checkObservation(current, actions.length, {
          outputLimitExceeded: diagnostics.outputLimitExceeded,
        })) addFinding(finding);
        return current;
      };

      const initial = record();
      const initialDiagnostics = session.diagnostics();
      if (initialDiagnostics.outputLimitExceeded) {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'output-limit', atAction: 0 };
      } else if ((manifest.requireInitialOutput ?? true) && (!initialDiagnostics.receivedOutput || initial.text.trim().length === 0)) {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'startup-failure', atAction: 0, exitCode: initial.exitCode, signal: initial.signal };
        addFinding({
          kind: 'startup-failure',
          severity: 'error',
          message: initialDiagnostics.startupTimedOut
            ? 'The target produced no terminal output before the startup deadline.'
            : 'The target exited before producing terminal output.',
          atAction: 0,
        });
      } else if (!initial.processAlive) {
        outcome = initial.exitCode === 0 && initial.signal === undefined ? 'terminated' : 'failed';
        termination = { kind: 'target-exit', atAction: 0, exitCode: initial.exitCode, signal: initial.signal };
      }

      const policy = this.policy ?? baselinePolicy(manifest.allowedKeys);
      const scripted = options.actions;
      while (status === 'passed' && actions.length < maxActions && initial.processAlive) {
        if (timeRemaining() === 0) {
          status = 'timed-out';
          outcome = 'truncated';
          termination = { kind: 'time-budget', atAction: actions.length };
          addFinding({ kind: 'timeout', severity: 'error', message: 'Episode time limit reached.', atAction: actions.length });
          break;
        }
        if (stalledSteps >= maxStalledSteps) {
          status = 'stalled';
          outcome = 'truncated';
          termination = { kind: 'stall-budget', atAction: actions.length };
          addFinding({ kind: 'stall', severity: 'warning', message: 'No stable screen progress was observed for the configured number of steps.', atAction: actions.length });
          break;
        }
        const observation = observations.at(-1)!;
        const action = scripted
          ? scripted[actions.length]
          : policy({ observation, history: observations, actions, seenStates });
        if (!action) {
          termination = { kind: 'policy-complete', atAction: actions.length };
          break;
        }
        if (typeof action.key !== 'string' || action.key.length === 0 || Buffer.byteLength(action.key, 'utf8') > 256) {
          throw new Error('Action key must contain between 1 and 256 UTF-8 bytes');
        }
        for (const [name, value] of [['holdMs', action.holdMs], ['waitMs', action.waitMs]] as const) {
          if (value !== undefined && (!Number.isSafeInteger(value) || value < 0 || value > 60_000)) {
            throw new Error(`Action ${name} must be a safe integer from 0 to 60000`);
          }
        }
        actions.push(action);
        const sendCompleted = await completesBeforeDeadline(
          session.send({ ...action, waitMs: action.waitMs ?? manifest.stepTimeoutMs ?? 250 }),
          timeRemaining(),
        );
        if (!sendCompleted) {
          status = 'timed-out';
          termination = { kind: 'time-budget', atAction: actions.length };
          addFinding({ kind: 'timeout', severity: 'error', message: 'Episode time limit reached during an action.', atAction: actions.length });
          break;
        }
        await session.waitForExit(Math.min(25, timeRemaining()));
        if (!session.probeProcessAlive()) {
          await session.waitForExit(Math.min(manifest.exitGraceMs ?? 2500, timeRemaining()));
        }
        const current = record();
        const diagnostics = session.diagnostics();
        if (diagnostics.outputLimitExceeded) {
          status = 'failed';
          outcome = 'failed';
          termination = { kind: 'output-limit', atAction: actions.length };
          break;
        }
        if (!current.processAlive) {
          outcome = current.exitCode === 0 && current.signal === undefined ? 'terminated' : 'failed';
          termination = { kind: 'target-exit', atAction: actions.length, exitCode: current.exitCode, signal: current.signal };
          break;
        }
      }

      if (status === 'passed' && actions.length >= maxActions && observations.at(-1)?.processAlive) {
        termination = { kind: 'action-budget', atAction: actions.length };
      }
      if (status === 'passed' && observations.at(-1)?.processAlive && timeRemaining() > 0) {
        await session.waitForExit(Math.min(manifest.exitGraceMs ?? 1100, timeRemaining()));
        if (!session.observe().processAlive) {
          const final = record();
          outcome = final.exitCode === 0 && final.signal === undefined ? 'terminated' : 'failed';
          termination = { kind: 'target-exit', atAction: actions.length, exitCode: final.exitCode, signal: final.signal };
        }
      }
      if (findings.some(finding => finding.kind === 'crash')) {
        status = 'crashed';
        outcome = 'failed';
      } else if (findings.some(finding => finding.severity === 'error') && status === 'passed') {
        status = 'failed';
        outcome = 'failed';
      }
    } catch (error) {
      status = 'failed';
      outcome = 'failed';
      termination = { kind: 'runner-error', atAction: actions.length };
      addFinding({ kind: 'runner-error', severity: 'error', message: error instanceof Error ? error.message : String(error), atAction: actions.length });
    } finally {
      try {
        await session?.stop();
      } catch (error) {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'runner-error', atAction: actions.length };
        addFinding({
          kind: 'runner-error',
          severity: 'error',
          message: `Cleanup failed: ${error instanceof Error ? error.message : String(error)}`,
          atAction: actions.length,
        });
      }
    }

    const elapsedMs = Date.now() - startedAt;
    return {
      schemaVersion: 1,
      targetId: manifest.id,
      status,
      outcome,
      termination,
      runtime: {
        backend: 'local-pty',
        platform: process.platform,
        arch: process.arch,
        node: process.version,
      },
      seed: options.seed,
      actionCount: actions.length,
      elapsedMs,
      actions,
      observations,
      findings,
      uniqueStates: seenStates.size,
      novelTransitions: seenTransitions.size,
      newCorpusEntries: corpus.size - startingCorpusSize,
      corpusSize: corpus.size,
      terminalText: observations.at(-1)?.text ?? '',
      replay: createReplay(manifest, options.seed, viewport, actions),
    };
  }
}
