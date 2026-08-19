import { baselinePolicy } from './agents.js';
import { LocalPtyBackend } from './backend.js';
import { ActionCorpus } from './corpus.js';
import { createFinding } from './findings.js';
import { fingerprintObservation } from './observations.js';
import { checkObservation } from './oracles.js';
import { createReplay } from './replay.js';
import type { ActionPolicy, CleanupReason, CleanupResult, ExecutionBackend, InputAction, OracleResult, RunOptions, RunReport, RunTermination, TargetManifest, TerminalObservation, TerminalSession } from './types.js';

export interface RunnerOptions {
  policy?: ActionPolicy;
  corpus?: ActionCorpus;
  backend?: ExecutionBackend;
}

type OperationResult = 'completed' | 'timeout' | 'cancelled';

const noCleanup: CleanupResult = {
  attempted: false,
  graceful: true,
  forced: false,
  mechanism: 'none',
  elapsedMs: 0,
  confirmedExited: true,
};

export class PlaytestRunner {
  private readonly policy?: ActionPolicy;
  private readonly corpus?: ActionCorpus;
  private readonly backend: ExecutionBackend;

  constructor(options: RunnerOptions = {}) {
    this.policy = options.policy;
    this.corpus = options.corpus;
    this.backend = options.backend ?? new LocalPtyBackend();
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
    let session: TerminalSession | undefined;
    let cleanup = noCleanup;
    let stalledSteps = 0;
    let previousStructural: string | undefined;

    const addFinding = (finding: OracleResult): void => {
      const duplicate = findings.some(existing => existing.signature === finding.signature);
      if (!duplicate) findings.push(finding);
    };

    const addRuntimeFinding = (
      kind: OracleResult['kind'],
      severity: OracleResult['severity'],
      message: string,
      discriminator: string,
    ): void => addFinding(createFinding({
      targetId: manifest.id,
      kind,
      severity,
      message,
      atAction: actions.length,
      observation: observations.at(-1),
      volatilePatterns: manifest.observation?.volatilePatterns,
      discriminator,
    }));

    const timeRemaining = (): number => Math.max(0, maxElapsedMs - (Date.now() - startedAt));
    const completesBeforeDeadline = async (operation: Promise<unknown>, timeoutMs: number): Promise<OperationResult> => {
      if (options.signal?.aborted) return 'cancelled';
      if (timeoutMs <= 0) return 'timeout';
      let timer: NodeJS.Timeout | undefined;
      let onAbort: (() => void) | undefined;
      try {
        return await Promise.race([
          operation.then(() => 'completed' as const),
          new Promise<'timeout'>(resolveTimeout => {
            timer = setTimeout(() => resolveTimeout('timeout'), timeoutMs);
          }),
          new Promise<'cancelled'>(resolveCancelled => {
            if (!options.signal) return;
            onAbort = () => resolveCancelled('cancelled');
            options.signal.addEventListener('abort', onAbort, { once: true });
          }),
        ]);
      } finally {
        if (timer) clearTimeout(timer);
        if (onAbort) options.signal?.removeEventListener('abort', onAbort);
      }
    };

    try {
      if (!Number.isSafeInteger(maxActions) || maxActions < 0) throw new Error('maxActions must be a non-negative safe integer');
      if (!Number.isSafeInteger(maxElapsedMs) || maxElapsedMs <= 0) throw new Error('maxElapsedMs must be a positive safe integer');
      if (!Number.isSafeInteger(maxStalledSteps) || maxStalledSteps <= 0) throw new Error('maxStalledSteps must be a positive safe integer');
      if (!Number.isSafeInteger(viewport.cols) || viewport.cols <= 0 || !Number.isSafeInteger(viewport.rows) || viewport.rows <= 0) {
        throw new Error('Viewport dimensions must be positive safe integers');
      }
      if (options.signal?.aborted) {
        status = 'cancelled';
        outcome = 'truncated';
        termination = { kind: 'cancelled', atAction: actions.length };
      } else {
        session = await this.backend.start({ manifest, seed: options.seed, viewport, signal: options.signal });
      }
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
          targetId: manifest.id,
          outputLimitExceeded: diagnostics.outputLimitExceeded,
          volatilePatterns: manifest.observation?.volatilePatterns,
        })) addFinding(finding);
        return current;
      };

      if (!session) throw new Error('Run cancelled before launch');
      if (options.signal?.aborted) {
        status = 'cancelled';
        outcome = 'truncated';
        termination = { kind: 'cancelled', atAction: actions.length };
      }
      const initial = record();
      const initialDiagnostics = session.diagnostics();
      if (status === 'cancelled') {
        // Cancellation takes precedence over diagnostics gathered during startup.
      } else if (initialDiagnostics.outputLimitExceeded) {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'output-limit', atAction: 0 };
      } else if ((manifest.requireInitialOutput ?? true) && (!initialDiagnostics.receivedOutput || initial.text.trim().length === 0)) {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'startup-failure', atAction: 0, exitCode: initial.exitCode, signal: initial.signal };
        addRuntimeFinding(
          'startup-failure',
          'error',
          initialDiagnostics.startupTimedOut
            ? 'The target produced no terminal output before the startup deadline.'
            : 'The target exited before producing terminal output.',
          initialDiagnostics.startupTimedOut ? 'startup-timeout' : 'early-exit',
        );
      } else if (!initial.processAlive) {
        outcome = initial.exitCode === 0 && initial.signal === undefined ? 'terminated' : 'failed';
        termination = { kind: 'target-exit', atAction: 0, exitCode: initial.exitCode, signal: initial.signal };
      }

      const policy = this.policy ?? baselinePolicy(manifest.allowedKeys);
      const scripted = options.actions;
      while (status === 'passed' && actions.length < maxActions && observations.at(-1)?.processAlive) {
        if (options.signal?.aborted) {
          status = 'cancelled';
          outcome = 'truncated';
          termination = { kind: 'cancelled', atAction: actions.length };
          break;
        }
        if (timeRemaining() === 0) {
          status = 'timed-out';
          outcome = 'truncated';
          termination = { kind: 'time-budget', atAction: actions.length };
          addRuntimeFinding('timeout', 'error', 'Episode time limit reached.', 'episode-time-budget');
          break;
        }
        if (stalledSteps >= maxStalledSteps) {
          status = 'stalled';
          outcome = 'truncated';
          termination = { kind: 'stall-budget', atAction: actions.length };
          addRuntimeFinding('stall', 'warning', 'No stable screen progress was observed for the configured number of steps.', 'structural-stall');
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
        if (sendCompleted === 'cancelled') {
          status = 'cancelled';
          outcome = 'truncated';
          termination = { kind: 'cancelled', atAction: actions.length };
          break;
        }
        if (sendCompleted === 'timeout') {
          status = 'timed-out';
          termination = { kind: 'time-budget', atAction: actions.length };
          addRuntimeFinding('timeout', 'error', 'Episode time limit reached during an action.', 'action-time-budget');
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
        const exitResult = await completesBeforeDeadline(
          session.waitForExit(Math.min(manifest.exitGraceMs ?? 2500, timeRemaining())),
          timeRemaining(),
        );
        if (exitResult === 'cancelled') {
          status = 'cancelled';
          outcome = 'truncated';
          termination = { kind: 'cancelled', atAction: actions.length };
        } else if (!session.observe().processAlive) {
          const final = record();
          outcome = final.exitCode === 0 && final.signal === undefined ? 'terminated' : 'failed';
          termination = { kind: 'target-exit', atAction: actions.length, exitCode: final.exitCode, signal: final.signal };
        }
      }
      if (status !== 'cancelled' && findings.some(finding => finding.kind === 'crash')) {
        status = 'crashed';
        outcome = 'failed';
      } else if (findings.some(finding => finding.severity === 'error') && status === 'passed') {
        status = 'failed';
        outcome = 'failed';
      }
    } catch (error) {
      if (options.signal?.aborted) {
        status = 'cancelled';
        outcome = 'truncated';
        termination = { kind: 'cancelled', atAction: actions.length };
      } else {
        status = 'failed';
        outcome = 'failed';
        termination = { kind: 'runner-error', atAction: actions.length };
        addRuntimeFinding('runner-error', 'error', error instanceof Error ? error.message : String(error), 'runner-exception');
      }
    } finally {
      if (session) {
        const reason: CleanupReason = status === 'cancelled'
          ? 'cancelled'
          : status === 'timed-out'
            ? 'timeout'
            : status === 'failed' || status === 'crashed'
              ? 'runner-error'
              : termination.kind === 'action-budget' || termination.kind === 'stall-budget' || termination.kind === 'output-limit'
                ? 'limit'
                : 'completed';
        try {
          cleanup = await session.stop(reason);
          if (!cleanup.confirmedExited || cleanup.error) {
            status = 'failed';
            outcome = 'failed';
            termination = { kind: 'runner-error', atAction: actions.length };
            addRuntimeFinding('runner-error', 'error', `Cleanup failed: ${cleanup.error ?? 'target exit was not confirmed'}`, 'cleanup-failure');
          }
        } catch (error) {
          cleanup = {
            ...noCleanup,
            attempted: true,
            graceful: false,
            confirmedExited: false,
            error: error instanceof Error ? error.message : String(error),
          };
          status = 'failed';
          outcome = 'failed';
          termination = { kind: 'runner-error', atAction: actions.length };
          addRuntimeFinding('runner-error', 'error', `Cleanup failed: ${cleanup.error}`, 'cleanup-exception');
        }
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
        backend: this.backend.id,
        capabilities: this.backend.capabilities,
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
      replay: createReplay(manifest, options.seed, viewport, actions, this.backend.replayIdentity?.() ?? { id: this.backend.id, capabilities: { ...this.backend.capabilities } }),
      cleanup,
    };
  }
}
