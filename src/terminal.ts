import headless from '@xterm/headless';
import type { Terminal as HeadlessTerminal } from '@xterm/headless';
import * as pty from 'node-pty';
import { resolve } from 'node:path';
import type { InputAction, TargetManifest, TerminalObservation, TerminalSession } from './types.js';

const { Terminal } = headless;

const sleep = (ms: number): Promise<void> => new Promise(resolveSleep => setTimeout(resolveSleep, ms));

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
}

export class PtyTerminalSession implements TerminalSession {
  private readonly terminal: HeadlessTerminal;
  private readonly process: pty.IPty;
  private readonly startedAt = Date.now();
  private lastText = '';
  private outputBytes = 0;
  private exitCode: number | undefined;
  private signal: number | undefined;
  private stopped = false;
  private writeQueue = Promise.resolve();
  private readonly firstOutput: Promise<void>;
  private resolveFirstOutput!: () => void;

  private constructor(process: pty.IPty, viewport: { cols: number; rows: number }, maxOutputBytes: number) {
    this.process = process;
    this.terminal = new Terminal({ cols: viewport.cols, rows: viewport.rows, allowProposedApi: true });
    this.maxOutputBytes = maxOutputBytes;
    this.firstOutput = new Promise<void>(resolveFirstOutput => {
      this.resolveFirstOutput = resolveFirstOutput;
    });
    process.onData(data => {
      this.outputBytes += Buffer.byteLength(data);
      this.resolveFirstOutput();
      if (this.outputBytes <= this.maxOutputBytes) {
        this.writeQueue = this.writeQueue.then(() => new Promise<void>(resolveWrite => {
          this.terminal.write(data, resolveWrite);
        }));
      }
    });
    process.onExit(event => {
      this.exitCode = event.exitCode;
      this.signal = event.signal;
    });
  }

  private readonly maxOutputBytes: number;

  static async start(options: PtyTerminalSessionOptions): Promise<PtyTerminalSession> {
    const viewport = {
      cols: options.viewport?.cols ?? options.manifest.terminal?.cols ?? 80,
      rows: options.viewport?.rows ?? options.manifest.terminal?.rows ?? 24,
    };
    const env = { ...process.env, ...(options.manifest.env ?? {}) };
    if (options.seed !== undefined && options.manifest.seed?.mode === 'env') {
      env[options.manifest.seed.envName ?? 'PLAYTESTR_SEED'] = String(options.seed);
    }
    const args = [...(options.manifest.args ?? [])];
    if (options.seed !== undefined && options.manifest.seed?.mode === 'argv') {
      args.push(options.manifest.seed.flag ?? '--seed', String(options.seed));
    }
    const command = process.platform === 'win32' && options.manifest.command === 'node'
      ? process.execPath
      : options.manifest.command;
    const child = pty.spawn(command, args, {
      name: 'xterm-256color',
      cols: viewport.cols,
      rows: viewport.rows,
      cwd: resolve(options.manifest.cwd ?? process.cwd()),
      env,
    });
    const session = new PtyTerminalSession(child, viewport, options.manifest.maxOutputBytes ?? 2_000_000);
    await session.waitForInitialOutput(options.manifest.startupTimeoutMs ?? 3000);
    await session.flush();
    return session;
  }

  private async waitForInitialOutput(timeoutMs: number): Promise<void> {
    await Promise.race([this.firstOutput, sleep(timeoutMs)]);
  }

  private async flush(): Promise<void> {
    await this.writeQueue;
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
      processAlive: this.exitCode === undefined && !this.stopped,
      exitCode: this.exitCode,
      signal: this.signal,
    };
    this.lastText = text;
    return observation;
  }

  async send(action: InputAction): Promise<void> {
    if (this.stopped) return;
    this.process.write(encodeKey(action.key));
    if ((action.holdMs ?? 0) > 0) await sleep(action.holdMs!);
    if ((action.waitMs ?? 0) > 0) await sleep(action.waitMs!);
    await this.flush();
  }

  async resize(cols: number, rows: number): Promise<void> {
    if (!this.stopped) this.process.resize(cols, rows);
    this.terminal.resize(cols, rows);
  }

  async stop(): Promise<void> {
    if (this.stopped) return;
    this.stopped = true;
    await Promise.race([this.firstOutput.then(() => sleep(50)), sleep(50)]);
    if (this.exitCode === undefined) {
      try { this.process.kill(); } catch { /* already exited */ }
    }
    await this.flush();
    this.terminal.dispose();
  }
}
