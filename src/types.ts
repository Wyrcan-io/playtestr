export type KeyName = string;

export interface InputAction {
  key: KeyName;
  holdMs?: number;
  waitMs?: number;
  label?: string;
}

export interface TerminalObservation {
  at: number;
  cols: number;
  rows: number;
  text: string;
  lines: string[];
  cursor: { x: number; y: number };
  alternateBuffer: boolean;
  changed: boolean;
  processAlive: boolean;
  exitCode?: number;
  signal?: number;
}

export interface TargetManifest {
  id: string;
  command: string;
  args?: string[];
  cwd?: string;
  env?: Record<string, string>;
  terminal?: { cols?: number; rows?: number };
  startupTimeoutMs?: number;
  stepTimeoutMs?: number;
  episodeTimeoutMs?: number;
  maxOutputBytes?: number;
  seed?: { mode: 'argv' | 'env'; flag?: string; envName?: string };
  allowedKeys?: string[];
}

export interface ReplayV1 {
  version: 1;
  targetId: string;
  command: string;
  args: string[];
  seed?: number;
  terminal: { cols: number; rows: number };
  actions: InputAction[];
}

export type OracleKind = 'crash' | 'timeout' | 'stall' | 'output-limit' | 'unexpected-exit' | 'no-progress';

export interface OracleResult {
  kind: OracleKind;
  severity: 'error' | 'warning';
  message: string;
  atAction: number;
}

export interface RunOptions {
  seed?: number;
  maxActions?: number;
  maxElapsedMs?: number;
  maxStalledSteps?: number;
  viewport?: { cols: number; rows: number };
  actions?: InputAction[];
  onObservation?: (observation: TerminalObservation) => void;
}

export interface RunReport {
  targetId: string;
  status: 'passed' | 'failed' | 'timed-out' | 'stalled' | 'crashed';
  seed?: number;
  actionCount: number;
  elapsedMs: number;
  actions: InputAction[];
  observations: TerminalObservation[];
  findings: OracleResult[];
  terminalText: string;
  replay: ReplayV1;
}

export interface TerminalSession {
  observe(): TerminalObservation;
  send(action: InputAction): Promise<void>;
  resize(cols: number, rows: number): Promise<void>;
  stop(): Promise<void>;
}

export interface ActionPolicyContext {
  observation: TerminalObservation;
  history: readonly TerminalObservation[];
  actions: readonly InputAction[];
  seenStates: ReadonlySet<string>;
}

export type ActionPolicy = (context: ActionPolicyContext) => InputAction | undefined;
