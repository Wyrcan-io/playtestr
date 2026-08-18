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

export interface ObservationFingerprint {
  exact: string;
  structural: string;
}

export interface CorpusEntry {
  fingerprint: string;
  actions: InputAction[];
  firstSeenAtAction: number;
}

export interface ObservationPolicy {
  /** Regular expressions replaced before structural hashing. */
  volatilePatterns?: string[];
}

export interface TargetManifest {
  schemaVersion: 1;
  id: string;
  command: string;
  args?: string[];
  cwd?: string;
  env?: Record<string, string>;
  /** Additional host variable names to inherit. Ambient variables are denied by default. */
  inheritEnv?: string[];
  terminal?: { cols?: number; rows?: number };
  observation?: ObservationPolicy;
  requireInitialOutput?: boolean;
  startupTimeoutMs?: number;
  stepTimeoutMs?: number;
  exitGraceMs?: number;
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
  cwd?: string;
  seed?: number;
  terminal: { cols: number; rows: number };
  actions: InputAction[];
}

export type OracleKind = 'crash' | 'timeout' | 'stall' | 'output-limit' | 'startup-failure' | 'runner-error';

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

export type RunTerminationKind =
  | 'target-exit'
  | 'policy-complete'
  | 'action-budget'
  | 'time-budget'
  | 'stall-budget'
  | 'startup-failure'
  | 'output-limit'
  | 'runner-error';

export interface RunTermination {
  kind: RunTerminationKind;
  atAction: number;
  exitCode?: number;
  signal?: number;
}

export interface RunReport {
  schemaVersion: 1;
  targetId: string;
  status: 'passed' | 'failed' | 'timed-out' | 'stalled' | 'crashed';
  outcome: 'terminated' | 'truncated' | 'failed';
  termination: RunTermination;
  runtime: {
    backend: 'local-pty';
    platform: NodeJS.Platform;
    arch: string;
    node: string;
  };
  seed?: number;
  actionCount: number;
  elapsedMs: number;
  actions: InputAction[];
  observations: TerminalObservation[];
  findings: OracleResult[];
  uniqueStates: number;
  novelTransitions: number;
  newCorpusEntries: number;
  corpusSize: number;
  terminalText: string;
  replay: ReplayV1;
}

export interface TerminalSessionDiagnostics {
  outputBytes: number;
  outputLimitExceeded: boolean;
  receivedOutput: boolean;
  startupTimedOut: boolean;
}

export interface TerminalSession {
  observe(): TerminalObservation;
  diagnostics(): TerminalSessionDiagnostics;
  probeProcessAlive(): boolean;
  send(action: InputAction): Promise<void>;
  waitForExit(timeoutMs?: number): Promise<boolean>;
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
