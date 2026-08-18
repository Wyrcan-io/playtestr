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

  start(options: ExecutionBackendStartOptions): Promise<TerminalSession> {
    return PtyTerminalSession.start(options);
  }
}
