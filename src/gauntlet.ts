import { readFile } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import type { TargetAdapter } from './adapter.js';
import { benchmarkStrategies, type BenchmarkExpectations, type BenchmarkResult } from './benchmark.js';
import { loadManifest } from './manifest.js';
import { PlaytestRunner } from './runner.js';
import type { InputAction, OracleKind, RunReport } from './types.js';

export type GauntletScenarioKind = 'discovery' | 'robustness' | 'lifecycle';

export interface GauntletScenarioV1 {
  id: string;
  kind: GauntletScenarioKind;
  manifest: string;
  seeds: number[];
  episodes: number;
  maxActionsPerEpisode: number;
  expectations?: BenchmarkExpectations;
  minimumEvidenceScore?: number;
  expectedFindingKinds?: OracleKind[];
  actions?: InputAction[];
  requireCleanup?: boolean;
}

export interface GauntletFileV1 {
  version: 1;
  id: string;
  scenarios: GauntletScenarioV1[];
}

export interface GauntletScenarioResult {
  id: string;
  kind: GauntletScenarioKind;
  passed: boolean;
  benchmarks: BenchmarkResult[];
  runs: RunReport[];
  missingFindingKinds: OracleKind[];
  cleanupFailures: number;
}

export interface GauntletResult {
  suiteId: string;
  passed: boolean;
  scenarioCount: number;
  discoveryCount: number;
  robustnessCount: number;
  lifecycleCount: number;
  scenarios: GauntletScenarioResult[];
}

export interface RunGauntletOptions {
  adapters?: Readonly<Record<string, TargetAdapter>>;
  signal?: AbortSignal;
}

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function positive(value: unknown, label: string): number {
  if (!Number.isSafeInteger(value) || (value as number) <= 0) throw new Error(`${label} must be a positive safe integer`);
  return value as number;
}

function nonNegative(value: unknown, label: string): number {
  if (!Number.isSafeInteger(value) || (value as number) < 0) throw new Error(`${label} must be a non-negative safe integer`);
  return value as number;
}

function booleanValue(value: unknown, label: string): boolean {
  if (typeof value !== 'boolean') throw new Error(`${label} must be a boolean`);
  return value;
}

function strings(value: unknown, label: string): string[] {
  if (!Array.isArray(value) || value.some(item => typeof item !== 'string' || item.length === 0)) throw new Error(`${label} must be an array of non-empty strings`);
  return [...new Set(value as string[])];
}

function findingKinds(value: unknown, id: string): OracleKind[] {
  const kinds = strings(value, `${id} expectedFindingKinds`);
  const allowed = new Set<OracleKind>(['crash', 'timeout', 'stall', 'output-limit', 'startup-failure', 'runner-error']);
  if (kinds.some(kind => !allowed.has(kind as OracleKind))) throw new Error(`Gauntlet scenario ${id} contains an unknown finding kind`);
  return kinds as OracleKind[];
}

function parseScenario(value: unknown, index: number): GauntletScenarioV1 {
  const raw = object(value, `Gauntlet scenario ${index + 1}`);
  const id = typeof raw.id === 'string' && raw.id ? raw.id : undefined;
  const manifest = typeof raw.manifest === 'string' && raw.manifest ? raw.manifest : undefined;
  if (!id || !manifest) throw new Error(`Gauntlet scenario ${index + 1} requires id and manifest`);
  if (!['discovery', 'robustness', 'lifecycle'].includes(raw.kind as string)) throw new Error(`Gauntlet scenario ${id} has an invalid kind`);
  if (!Array.isArray(raw.seeds) || raw.seeds.length === 0 || raw.seeds.some(seed => !Number.isSafeInteger(seed))) throw new Error(`Gauntlet scenario ${id} requires safe integer seeds`);
  const expectations = raw.expectations === undefined ? undefined : object(raw.expectations, `Gauntlet scenario ${id} expectations`);
  if (raw.minimumEvidenceScore !== undefined && (!Number.isFinite(raw.minimumEvidenceScore) || (raw.minimumEvidenceScore as number) < 0 || (raw.minimumEvidenceScore as number) > 1)) throw new Error(`Gauntlet scenario ${id} minimumEvidenceScore must be from 0 to 1`);
  if (raw.actions !== undefined && !Array.isArray(raw.actions)) throw new Error(`Gauntlet scenario ${id} actions must be an array`);
  const actions = raw.actions === undefined ? undefined : (raw.actions as unknown[]).map((action, actionIndex) => {
    const parsed = object(action, `Gauntlet scenario ${id} action ${actionIndex + 1}`);
    if (typeof parsed.key !== 'string' || !parsed.key) throw new Error(`Gauntlet scenario ${id} action ${actionIndex + 1} requires a key`);
    return {
      key: parsed.key,
      ...(parsed.holdMs === undefined ? {} : { holdMs: nonNegative(parsed.holdMs, `Gauntlet scenario ${id} action holdMs`) }),
      ...(parsed.waitMs === undefined ? {} : { waitMs: nonNegative(parsed.waitMs, `Gauntlet scenario ${id} action waitMs`) }),
    };
  });
  return {
    id,
    kind: raw.kind as GauntletScenarioKind,
    manifest,
    seeds: raw.seeds as number[],
    episodes: positive(raw.episodes, `Gauntlet scenario ${id} episodes`),
    maxActionsPerEpisode: positive(raw.maxActionsPerEpisode, `Gauntlet scenario ${id} maxActionsPerEpisode`),
    ...(expectations ? { expectations: {
      ...(expectations.mechanics === undefined ? {} : { mechanics: strings(expectations.mechanics, `${id} mechanics`) }),
      ...(expectations.milestones === undefined ? {} : { milestones: strings(expectations.milestones, `${id} milestones`) }),
      ...(expectations.tags === undefined ? {} : { tags: strings(expectations.tags, `${id} tags`) }),
      ...(expectations.completion === undefined ? {} : { completion: booleanValue(expectations.completion, `${id} completion`) }),
      ...(expectations.hidden === undefined ? {} : { hidden: booleanValue(expectations.hidden, `${id} hidden`) }),
    } } : {}),
    ...(raw.minimumEvidenceScore === undefined ? {} : { minimumEvidenceScore: raw.minimumEvidenceScore as number }),
    ...(raw.expectedFindingKinds === undefined ? {} : { expectedFindingKinds: findingKinds(raw.expectedFindingKinds, id) }),
    ...(actions ? { actions } : {}),
    requireCleanup: raw.requireCleanup === undefined ? true : Boolean(raw.requireCleanup),
  };
}

export async function loadGauntlet(file: string): Promise<{ suite: GauntletFileV1; root: string }> {
  const suitePath = resolve(file);
  const root = dirname(suitePath);
  const raw = object(JSON.parse(await readFile(suitePath, 'utf8')), 'Gauntlet');
  if (raw.version !== 1 || typeof raw.id !== 'string' || !raw.id || !Array.isArray(raw.scenarios)) throw new Error('Gauntlet must be a valid V1 suite');
  const scenarios = raw.scenarios.map(parseScenario);
  if (scenarios.length === 0) throw new Error('Gauntlet requires at least one scenario');
  if (new Set(scenarios.map(scenario => scenario.id)).size !== scenarios.length) throw new Error('Gauntlet scenario IDs must be unique');
  for (const scenario of scenarios) {
    if (isAbsolute(scenario.manifest)) throw new Error(`Gauntlet scenario ${scenario.id} manifest must be relative`);
    const manifestPath = resolve(root, scenario.manifest);
    const outside = relative(root, manifestPath);
    if (outside.startsWith('..') || isAbsolute(outside)) throw new Error(`Gauntlet scenario ${scenario.id} manifest escapes the suite directory`);
  }
  return { suite: { version: 1, id: raw.id, scenarios }, root };
}

export async function runGauntlet(file: string, options: RunGauntletOptions = {}): Promise<GauntletResult> {
  const { suite, root } = await loadGauntlet(file);
  const scenarios: GauntletScenarioResult[] = [];
  for (const scenario of suite.scenarios) {
    if (options.signal?.aborted) break;
    const manifest = await loadManifest(resolve(root, scenario.manifest));
    const adapter = options.adapters?.[scenario.id];
    if (scenario.kind === 'discovery') {
      const benchmarks: BenchmarkResult[] = [];
      for (const seed of scenario.seeds) {
        if (options.signal?.aborted) break;
        benchmarks.push(await benchmarkStrategies(manifest, {
          episodes: scenario.episodes,
          maxActionsPerEpisode: scenario.maxActionsPerEpisode,
          seed,
          expectations: scenario.expectations,
          adapter,
          signal: options.signal,
        }));
      }
      const cleanupFailures = benchmarks.flatMap(result => result.strategies).reduce((total, strategy) => total + strategy.cleanupFailures, 0);
      const intelligent = benchmarks.map(result => result.strategies.find(strategy => strategy.strategy === 'intelligent-autonomy')!);
      const passed = benchmarks.length === scenario.seeds.length
        && cleanupFailures === 0
        && intelligent.every(strategy => strategy.evidenceScore >= (scenario.minimumEvidenceScore ?? (scenario.expectations ? 1 : 0)));
      scenarios.push({ id: scenario.id, kind: scenario.kind, passed, benchmarks, runs: [], missingFindingKinds: [], cleanupFailures });
      continue;
    }
    const runs: RunReport[] = [];
    for (const seed of scenario.seeds) {
      if (options.signal?.aborted) break;
      runs.push(await new PlaytestRunner().run(manifest, {
        seed,
        actions: scenario.actions,
        maxActions: scenario.actions?.length ?? scenario.maxActionsPerEpisode,
        maxElapsedMs: manifest.episodeTimeoutMs,
        signal: options.signal,
      }));
    }
    const observedKinds = new Set(runs.flatMap(run => run.findings.map(finding => finding.kind)));
    const missingFindingKinds = (scenario.expectedFindingKinds ?? []).filter(kind => !observedKinds.has(kind));
    const cleanupFailures = runs.filter(run => !run.cleanup.confirmedExited || run.cleanup.error).length;
    const passed = runs.length === scenario.seeds.length && missingFindingKinds.length === 0 && (!scenario.requireCleanup || cleanupFailures === 0);
    scenarios.push({ id: scenario.id, kind: scenario.kind, passed, benchmarks: [], runs, missingFindingKinds, cleanupFailures });
  }
  return {
    suiteId: suite.id,
    passed: scenarios.length === suite.scenarios.length && scenarios.every(scenario => scenario.passed),
    scenarioCount: scenarios.length,
    discoveryCount: scenarios.filter(scenario => scenario.kind === 'discovery').length,
    robustnessCount: scenarios.filter(scenario => scenario.kind === 'robustness').length,
    lifecycleCount: scenarios.filter(scenario => scenario.kind === 'lifecycle').length,
    scenarios,
  };
}
