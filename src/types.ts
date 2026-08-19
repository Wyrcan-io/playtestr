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
  discoveredAtEpisode?: number;
  provenance?: string;
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
  maxArtifactBytes?: number;
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

export type EvidenceLevel = 'observed' | 'reproduced' | 'confirmed' | 'reviewed';

export type OracleKind = 'crash' | 'timeout' | 'stall' | 'output-limit' | 'startup-failure' | 'runner-error';

export interface OracleResult {
  signatureVersion: 1;
  signature: string;
  kind: OracleKind;
  severity: 'error' | 'warning';
  evidenceLevel: EvidenceLevel;
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
  signal?: AbortSignal;
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
  | 'cancelled'
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
  status: 'passed' | 'failed' | 'timed-out' | 'stalled' | 'crashed' | 'cancelled';
  outcome: 'terminated' | 'truncated' | 'failed';
  termination: RunTermination;
  runtime: {
    backend: string;
    capabilities: ExecutionBackendCapabilities;
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
  cleanup: CleanupResult;
}

export interface TerminalSessionDiagnostics {
  outputBytes: number;
  outputLimitExceeded: boolean;
  receivedOutput: boolean;
  startupTimedOut: boolean;
  pid: number;
}

export type CleanupReason = 'completed' | 'cancelled' | 'timeout' | 'limit' | 'runner-error';

export interface CleanupResult {
  attempted: boolean;
  graceful: boolean;
  forced: boolean;
  mechanism: 'none' | 'pty-kill' | 'unix-process-group' | 'windows-taskkill';
  elapsedMs: number;
  confirmedExited: boolean;
  error?: string;
}

export interface TerminalSession {
  observe(): TerminalObservation;
  diagnostics(): TerminalSessionDiagnostics;
  probeProcessAlive(): boolean;
  send(action: InputAction): Promise<void>;
  waitForExit(timeoutMs?: number): Promise<boolean>;
  resize(cols: number, rows: number): Promise<void>;
  stop(reason?: CleanupReason): Promise<CleanupResult>;
}

export interface ExecutionBackendCapabilities {
  isolation: 'none' | 'process' | 'container' | 'browser-context';
  processTreeCleanup: boolean;
  resize: boolean;
  signals: boolean;
  rawTerminalEvents: boolean;
}

export interface ExecutionBackendStartOptions {
  manifest: TargetManifest;
  seed?: number;
  viewport?: { cols: number; rows: number };
  signal?: AbortSignal;
}

export interface ExecutionBackend {
  readonly id: string;
  readonly capabilities: ExecutionBackendCapabilities;
  start(options: ExecutionBackendStartOptions): Promise<TerminalSession>;
}

export interface ActionPolicyContext {
  observation: TerminalObservation;
  history: readonly TerminalObservation[];
  actions: readonly InputAction[];
  seenStates: ReadonlySet<string>;
}

export type ActionPolicy = (context: ActionPolicyContext) => InputAction | undefined;
