export type GraphicalAction =
  | { kind: 'key'; key: string; state?: 'press' | 'down' | 'up' }
  | { kind: 'pointer'; x: number; y: number; button?: 'left' | 'middle' | 'right'; state?: 'click' | 'down' | 'up' }
  | { kind: 'wait'; ms: number };

export interface GraphicalObservation {
  at: number;
  width: number;
  height: number;
  frameDigest: string;
  accessibilityText?: string;
  interactiveLabels?: string[];
  changed: boolean;
}

export interface GraphicalTargetV1 {
  version: 1;
  id: string;
  url: string;
  viewport: { width: number; height: number; deviceScaleFactor?: number };
  locale?: string;
  timezone?: string;
  colorScheme?: 'light' | 'dark';
  reducedMotion?: boolean;
}

export interface GraphicalBackendCapabilities {
  isolation: 'browser-context' | 'process' | 'none';
  accessibilityTree: boolean;
  screenshots: boolean;
  video: boolean;
  pointer: boolean;
  keyboard: boolean;
}

export interface GraphicalCleanup {
  attempted: boolean;
  confirmedClosed: boolean;
  error?: string;
}

export interface GraphicalSession {
  observe(): Promise<GraphicalObservation>;
  send(action: GraphicalAction): Promise<void>;
  close(): Promise<GraphicalCleanup>;
}

export interface GraphicalBackend {
  readonly id: string;
  readonly capabilities: GraphicalBackendCapabilities;
  start(target: GraphicalTargetV1, signal?: AbortSignal): Promise<GraphicalSession>;
}

export interface GraphicalEpisodeResultV1 {
  version: 1;
  targetId: string;
  backendId: string;
  capabilities: GraphicalBackendCapabilities;
  status: 'passed' | 'cancelled' | 'failed';
  actions: GraphicalAction[];
  observations: GraphicalObservation[];
  elapsedMs: number;
  cleanup: GraphicalCleanup;
  error?: string;
}

function validateTarget(target: GraphicalTargetV1): void {
  if (target.version !== 1 || !target.id || !target.url) throw new Error('Graphical target must be a valid V1 target');
  for (const [name, value] of [['width', target.viewport.width], ['height', target.viewport.height], ['deviceScaleFactor', target.viewport.deviceScaleFactor ?? 1]] as const) {
    if (!Number.isFinite(value) || value <= 0) throw new Error(`Graphical viewport ${name} must be positive`);
  }
}

function validateAction(action: GraphicalAction): void {
  if (action.kind === 'key') {
    if (!action.key || Buffer.byteLength(action.key, 'utf8') > 256) throw new Error('Graphical key action is invalid');
  } else if (action.kind === 'pointer') {
    if (![action.x, action.y].every(value => Number.isFinite(value) && value >= 0 && value <= 1)) throw new Error('Graphical pointer coordinates must be normalized from 0 to 1');
  } else if (!Number.isSafeInteger(action.ms) || action.ms < 0 || action.ms > 60_000) throw new Error('Graphical wait must be from 0 to 60000ms');
}

export async function runGraphicalEpisode(
  backend: GraphicalBackend,
  target: GraphicalTargetV1,
  actions: readonly GraphicalAction[],
  options: { maxActions?: number; maxElapsedMs?: number; signal?: AbortSignal } = {},
): Promise<GraphicalEpisodeResultV1> {
  validateTarget(target);
  const maxActions = options.maxActions ?? actions.length;
  const maxElapsedMs = options.maxElapsedMs ?? 30_000;
  if (!Number.isSafeInteger(maxActions) || maxActions < 0 || !Number.isSafeInteger(maxElapsedMs) || maxElapsedMs <= 0) throw new Error('Graphical episode budgets are invalid');
  const started = Date.now();
  const sent: GraphicalAction[] = [];
  const observations: GraphicalObservation[] = [];
  let session: GraphicalSession | undefined;
  let status: GraphicalEpisodeResultV1['status'] = 'passed';
  let error: string | undefined;
  let cleanup: GraphicalCleanup = { attempted: false, confirmedClosed: true };
  try {
    if (options.signal?.aborted) status = 'cancelled';
    else {
      session = await backend.start(target, options.signal);
      observations.push(await session.observe());
      for (const action of actions.slice(0, maxActions)) {
        if (options.signal?.aborted) { status = 'cancelled'; break; }
        if (Date.now() - started >= maxElapsedMs) { status = 'failed'; error = 'Graphical episode time budget reached'; break; }
        validateAction(action);
        await session.send(action);
        sent.push({ ...action });
        observations.push(await session.observe());
      }
    }
  } catch (caught) {
    status = options.signal?.aborted ? 'cancelled' : 'failed';
    error = caught instanceof Error ? caught.message : String(caught);
  } finally {
    if (session) {
      try { cleanup = await session.close(); } catch (caught) {
        cleanup = { attempted: true, confirmedClosed: false, error: caught instanceof Error ? caught.message : String(caught) };
      }
      if (!cleanup.confirmedClosed) status = 'failed';
    }
  }
  return {
    version: 1,
    targetId: target.id,
    backendId: backend.id,
    capabilities: { ...backend.capabilities },
    status,
    actions: sent,
    observations,
    elapsedMs: Date.now() - started,
    cleanup,
    ...(error ? { error } : {}),
  };
}
