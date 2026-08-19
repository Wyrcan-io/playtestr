import { PtyTerminalSession } from './terminal.js';
import type { ExecutionBackend, ExecutionBackendCapabilities, ExecutionBackendStartOptions, TerminalSession } from './types.js';

export class LocalPtyBackend implements ExecutionBackend {
  readonly id = 'local-pty';
  readonly capabilities: ExecutionBackendCapabilities = {
    isolation: 'none',
    processTreeCleanup: true,
    resize: true,
    signals: true,
    rawTerminalEvents: false,
  };

  replayIdentity() {
    return { id: this.id, capabilities: { ...this.capabilities }, runtime: 'node-pty', runtimeVersion: '1.2.0-beta.14' };
  }

  start(options: ExecutionBackendStartOptions): Promise<TerminalSession> {
    return PtyTerminalSession.start(options);
  }
}
