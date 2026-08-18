import headless from '@xterm/headless';
import type { Terminal as HeadlessTerminal } from '@xterm/headless';
import * as pty from 'node-pty';
import { resolve } from 'node:path';
import { commandWithSeed } from './manifest.js';
import { forceTerminateProcessTree, probePid } from './process-tree.js';
import type { CleanupReason, CleanupResult, InputAction, TargetManifest, TerminalObservation, TerminalSession, TerminalSessionDiagnostics } from './types.js';

const { Terminal } = headless;

const sleep = (ms: number): Promise<void> => new Promise(resolveSleep => setTimeout(resolveSleep, ms));

async function waitUntilSettledOrTimeout(signal: Promise<void>, timeoutMs: number): Promise<void> {
  let timer: NodeJS.Timeout | undefined;
  try {
    await Promise.race([
      signal,
      new Promise<void>(resolveTimeout => {
        timer = setTimeout(resolveTimeout, timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

const keyBytes: Record<string, string> = {
  ArrowUp: '\x1b[A', ArrowDown: '\x1b[B', ArrowLeft: '\x1b[D', ArrowRight: '\x1b[C',
  Enter: '\r', Escape: '\x1b', Tab: '\t', Backspace: '\x7f', Space: ' ', ' ': ' ',
};

export function encodeKey(key: string): string {
  return keyBytes[key] ?? key;
}

export interface PtyTerminalSessionOptions {
  manifest: TargetManifest;
  seed?: number;
  viewport?: { cols: number; rows: number };
  signal?: AbortSignal;
}

interface WindowsPtyInternals {
  _agent?: { inSocket?: { destroy(): void } };
}

function closeWindowsInputPipe(ptyProcess: pty.IPty): void {
  if (process.platform !== 'win32') return;
  // node-pty 1.2.0-beta.14 does not close this pipe through IPty.kill(). Keep this
  // compatibility shim guarded and covered by the natural-process-exit soak.
  try { (ptyProcess as unknown as WindowsPtyInternals)._agent?.inSocket?.destroy(); } catch { /* already closed */ }
}

export class PtyTerminalSession implements TerminalSession {
  private readonly terminal: HeadlessTerminal;
  private readonly process: pty.IPty;
  private readonly dataSubscription: pty.IDisposable;
  private readonly exitSubscription: pty.IDisposable;
  private readonly startedAt = Date.now();
  private lastText = '';
  private outputBytes = 0;
  private outputLimitExceeded = false;
  private receivedOutput = false;
  private startupTimedOut = false;
  private exitCode: number | undefined;
  private signal: number | undefined;
  private exited = false;
  private stopped = false;
  private writeQueue = Promise.resolve();
  private readonly pendingDelays = new Map<NodeJS.Timeout, () => void>();
  private readonly firstOutput: Promise<void>;
  private resolveFirstOutput!: () => void;
  private readonly exitPromise: Promise<void>;
  private resolveExit!: () => void;

  private constructor(process: pty.IPty, viewport: { cols: number; rows: number }, maxOutputBytes: number) {
    this.process = process;
    this.terminal = new Terminal({ cols: viewport.cols, rows: viewport.rows, allowProposedApi: true });
    this.maxOutputBytes = maxOutputBytes;
    this.firstOutput = new Promise<void>(resolveFirstOutput => {
      this.resolveFirstOutput = resolveFirstOutput;
    });
    this.exitPromise = new Promise<void>(resolveExit => {
      this.resolveExit = resolveExit;
    });
    this.dataSubscription = process.onData(data => {
      this.outputBytes += Buffer.byteLength(data);
      this.receivedOutput = true;
      this.resolveFirstOutput();
      if (this.outputBytes > this.maxOutputBytes) {
        if (!this.outputLimitExceeded) {
          this.outputLimitExceeded = true;
          try { this.process.kill(); } catch { /* target is already closing */ }
        }
      } else {
        this.writeQueue = this.writeQueue.then(() => new Promise<void>(resolveWrite => {
          this.terminal.write(data, resolveWrite);
        }));
      }
    });
    this.exitSubscription = process.onExit(event => {
      this.exited = true;
      this.exitCode = event.exitCode;
      this.signal = event.signal;
      this.resolveExit();
    });
  }

  private readonly maxOutputBytes: number;

  static async start(options: PtyTerminalSessionOptions): Promise<PtyTerminalSession> {
    const viewport = {
      cols: options.viewport?.cols ?? options.manifest.terminal?.cols ?? 80,
      rows: options.viewport?.rows ?? options.manifest.terminal?.rows ?? 24,
    };
    const launch = commandWithSeed(options.manifest, options.seed);
    const command = process.platform === 'win32' && launch.command === 'node'
      ? process.execPath
      : launch.command;
    const child = pty.spawn(command, launch.args, {
      name: 'xterm-256color',
      cols: viewport.cols,
      rows: viewport.rows,
      cwd: resolve(options.manifest.cwd ?? process.cwd()),
      env: launch.env,
    });
    const session = new PtyTerminalSession(child, viewport, options.manifest.maxOutputBytes ?? 2_000_000);
    await session.waitForInitialOutput(options.manifest.startupTimeoutMs ?? 3000, options.signal);
    // Rendering the first bytes can precede target-side input handler setup by a
    // scheduler turn, especially under ConPTY. Give startup one short settle tick.
    if (!options.signal?.aborted) await sleep(25);
    await session.flush();
    return session;
  }

  private async waitForInitialOutput(timeoutMs: number, signal?: AbortSignal): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (!this.exited && !signal?.aborted && Date.now() < deadline) {
      const remaining = deadline - Date.now();
      await Promise.race([this.firstOutput, this.exitPromise, sleep(Math.min(25, remaining))]);
      await this.flush();
      const buffer = this.terminal.buffer.active;
      const hasRenderedText = Array.from({ length: buffer.length }, (_, index) =>
        buffer.getLine(index)?.translateToString(true) ?? '').join('\n').trim().length > 0;
      if (hasRenderedText || this.outputLimitExceeded) return;
      await sleep(Math.min(10, Math.max(0, deadline - Date.now())));
    }
    this.startupTimedOut = !signal?.aborted && !this.exited;
  }

  private async flush(): Promise<void> {
    await this.writeQueue;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolveDelay => {
      let timer: NodeJS.Timeout;
      const finish = (): void => {
        clearTimeout(timer);
        this.pendingDelays.delete(timer);
        resolveDelay();
      };
      timer = setTimeout(finish, ms);
      this.pendingDelays.set(timer, finish);
    });
  }

  private cancelPendingDelays(): void {
    for (const finish of [...this.pendingDelays.values()]) finish();
  }

  observe(): TerminalObservation {
    const buffer = this.terminal.buffer.active;
    const lines = Array.from({ length: buffer.length }, (_, index) => buffer.getLine(index)?.translateToString(true) ?? '');
    const text = lines.join('\n').replace(/\s+$/u, '');
    const observation: TerminalObservation = {
      at: Date.now() - this.startedAt,
      cols: this.terminal.cols,
      rows: this.terminal.rows,
      text,
      lines,
      cursor: { x: buffer.cursorX, y: buffer.cursorY },
      alternateBuffer: this.terminal.buffer.active !== this.terminal.buffer.normal,
      changed: text !== this.lastText,
      processAlive: !this.exited && !this.stopped,
      exitCode: this.exitCode,
      signal: this.signal,
    };
    this.lastText = text;
    return observation;
  }

  diagnostics(): TerminalSessionDiagnostics {
    return {
      outputBytes: this.outputBytes,
      outputLimitExceeded: this.outputLimitExceeded,
      receivedOutput: this.receivedOutput,
      startupTimedOut: this.startupTimedOut,
      pid: this.process.pid,
    };
  }

  probeProcessAlive(): boolean {
    if (this.exited || this.stopped) return false;
    return probePid(this.process.pid);
  }

  async send(action: InputAction): Promise<void> {
    if (this.stopped) return;
    this.process.write(encodeKey(action.key));
    if ((action.holdMs ?? 0) > 0) await this.delay(action.holdMs!);
    if ((action.waitMs ?? 0) > 0) await this.delay(action.waitMs!);
    await this.flush();
  }

  async waitForExit(timeoutMs = 0): Promise<boolean> {
    if (this.exited) return true;
    if (timeoutMs > 0) await waitUntilSettledOrTimeout(this.exitPromise, timeoutMs);
    return this.exited;
  }

  async resize(cols: number, rows: number): Promise<void> {
    if (!this.stopped) this.process.resize(cols, rows);
    this.terminal.resize(cols, rows);
  }

  async stop(_reason: CleanupReason = 'completed'): Promise<CleanupResult> {
    const cleanupStartedAt = Date.now();
    if (this.stopped) {
      return { attempted: false, graceful: this.exited, forced: false, mechanism: 'none', elapsedMs: 0, confirmedExited: !probePid(this.process.pid) };
    }
    this.cancelPendingDelays();
    let graceful = this.exited;
    let forced = false;
    let mechanism: CleanupResult['mechanism'] = 'none';
    let cleanupError: string | undefined;
    await this.waitForExit(50);
    graceful = this.exited || !probePid(this.process.pid);
    if (!this.exited) {
      try { this.process.write('\x03'); } catch { /* already closing */ }
      await this.waitForExit(150);
      graceful = this.exited || !probePid(this.process.pid);
    }
    if (!this.exited && probePid(this.process.pid)) {
      forced = true;
      const tree = await forceTerminateProcessTree(this.process.pid);
      mechanism = tree.mechanism;
      cleanupError = tree.error;
    }
    if (process.platform === 'win32' || !this.exited) {
      try { this.process.kill(); } catch { /* native PTY is already closed */ }
      // Closing ConPTY's input worker after kill lets its exit callback drain
      // promptly; the OS pid probe below remains the cleanup authority.
      closeWindowsInputPipe(this.process);
      await this.waitForExit(process.platform === 'win32' ? 750 : 500);
    }
    closeWindowsInputPipe(this.process);
    const confirmedExited = !probePid(this.process.pid);
    if (!confirmedExited && !cleanupError) cleanupError = 'The target process did not confirm exit after forced tree cleanup';
    this.stopped = true;
    this.dataSubscription.dispose();
    this.exitSubscription.dispose();
    await Promise.race([this.flush(), sleep(250)]);
    this.terminal.dispose();
    return {
      attempted: true,
      graceful,
      forced,
      mechanism: mechanism === 'none' && forced ? 'pty-kill' : mechanism,
      elapsedMs: Date.now() - cleanupStartedAt,
      confirmedExited,
      ...(cleanupError ? { error: cleanupError } : {}),
    };
  }
}
