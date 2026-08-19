import { access, mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import type { TargetAdapter } from './adapter.js';
import { ActionCorpus, serializeCorpus, targetCompatibilityKey, type CorpusFileV1 } from './corpus.js';
import { autonomyDeterminismSignature } from './evaluation.js';
import { FindingRegistry, verifyFindingRecords, type FindingRecordV1 } from './finding-registry.js';
import { autonomousPlaytest, type AutonomyOptions, type AutonomyResult } from './orchestrator.js';
import { PlaytestRunner } from './runner.js';
import { WorldModel, type WorldModelSnapshot } from './world-model.js';
import type { TargetManifest } from './types.js';

export interface CampaignTotalsV1 {
  sessions: number;
  episodes: number;
  actions: number;
  elapsedMs: number;
}

export interface CampaignSessionV1 {
  session: number;
  startedAt: string;
  completedAt: string;
  seed: number;
  stopReason: AutonomyResult['stopReason'];
  episodes: number;
  actions: number;
  elapsedMs: number;
  newFindingSignatures: string[];
  determinismSignature: string;
}

export interface CampaignFileV1 {
  version: 1;
  id: string;
  targetId: string;
  targetCompatibilityKey: string;
  revision: number;
  createdAt: string;
  updatedAt: string;
  totals: CampaignTotalsV1;
  world: WorldModelSnapshot;
  corpus: CorpusFileV1;
  findings: FindingRecordV1[];
  sessions: CampaignSessionV1[];
}

export interface CampaignRunOptions extends Omit<AutonomyOptions, 'adapter' | 'world' | 'corpus'> {
  adapter?: TargetAdapter;
  verifyFindings?: boolean;
  verificationAttempts?: number;
  verificationRequiredMatches?: number;
  verificationMaxElapsedMs?: number;
  maxSessionHistory?: number;
}

export interface CampaignRunResult {
  campaign: CampaignFileV1;
  autonomy: AutonomyResult;
  newFindingSignatures: string[];
}

export class CampaignRevisionError extends Error {
  constructor(readonly expected: number, readonly actual: number) {
    super(`Campaign revision changed: expected ${expected}, found ${actual}`);
    this.name = 'CampaignRevisionError';
  }
}

async function exists(path: string): Promise<boolean> {
  try { await access(path); return true; } catch { return false; }
}

function cloneCampaign(campaign: CampaignFileV1): CampaignFileV1 {
  return JSON.parse(JSON.stringify(campaign)) as CampaignFileV1;
}

function validateCampaign(campaign: CampaignFileV1, manifest: TargetManifest): void {
  if (campaign.version !== 1 || typeof campaign.id !== 'string' || !campaign.id || campaign.targetId !== manifest.id) throw new Error('Campaign is not a valid V1 file for this target');
  if (campaign.targetCompatibilityKey !== targetCompatibilityKey(manifest)) throw new Error('Campaign target compatibility key does not match the current manifest');
  if (!Number.isSafeInteger(campaign.revision) || campaign.revision < 0) throw new Error('Campaign revision is invalid');
  if (!campaign.totals || Object.values(campaign.totals).some(value => !Number.isSafeInteger(value) || value < 0)) throw new Error('Campaign totals are invalid');
  if (!Array.isArray(campaign.sessions) || !Array.isArray(campaign.findings) || !campaign.corpus || campaign.corpus.version !== 1) throw new Error('Campaign evidence collections are invalid');
  if (campaign.corpus.targetId !== manifest.id || campaign.corpus.targetCompatibilityKey !== campaign.targetCompatibilityKey || !Array.isArray(campaign.corpus.entries)) throw new Error('Campaign corpus is incompatible');
  if (campaign.world.targetId !== manifest.id) throw new Error('Campaign world target is incompatible');
  if (campaign.findings.some(finding => finding.replay.targetId !== manifest.id)) throw new Error('Campaign finding replay target is incompatible');
  WorldModel.fromSnapshot(campaign.world);
  new FindingRegistry(campaign.findings);
  new ActionCorpus(campaign.corpus.entries);
}

export function createCampaign(manifest: TargetManifest, id = `${manifest.id}-campaign`): CampaignFileV1 {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/u.test(id)) throw new Error('Campaign ID must be 1-128 safe identifier characters');
  const now = new Date().toISOString();
  const corpus = new ActionCorpus();
  return {
    version: 1,
    id,
    targetId: manifest.id,
    targetCompatibilityKey: targetCompatibilityKey(manifest),
    revision: 0,
    createdAt: now,
    updatedAt: now,
    totals: { sessions: 0, episodes: 0, actions: 0, elapsedMs: 0 },
    world: new WorldModel(manifest.id).snapshot(),
    corpus: serializeCorpus(corpus, manifest),
    findings: [],
    sessions: [],
  };
}

export async function loadCampaign(file: string, manifest: TargetManifest): Promise<CampaignFileV1> {
  const parsed = JSON.parse(await readFile(resolve(file), 'utf8')) as CampaignFileV1;
  validateCampaign(parsed, manifest);
  return cloneCampaign(parsed);
}

export async function saveCampaign(
  campaign: CampaignFileV1,
  manifest: TargetManifest,
  file: string,
  options: { expectedRevision?: number } = {},
): Promise<CampaignFileV1> {
  validateCampaign(campaign, manifest);
  const path = resolve(file);
  const expectedRevision = options.expectedRevision ?? campaign.revision;
  let actualRevision = 0;
  if (await exists(path)) {
    const existing = JSON.parse(await readFile(path, 'utf8')) as Partial<CampaignFileV1>;
    if (!Number.isSafeInteger(existing.revision) || (existing.revision as number) < 0) throw new Error('Existing campaign revision is invalid');
    if (existing.id !== campaign.id || existing.targetId !== manifest.id || existing.targetCompatibilityKey !== campaign.targetCompatibilityKey) throw new Error('Existing campaign identity is incompatible');
    actualRevision = existing.revision as number;
  }
  if (actualRevision !== expectedRevision) throw new CampaignRevisionError(expectedRevision, actualRevision);
  const persisted = cloneCampaign({ ...campaign, revision: actualRevision + 1, updatedAt: new Date().toISOString() });
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${process.pid}-${Date.now()}`;
  const backup = `${path}.backup-${process.pid}-${Date.now()}`;
  let movedExisting = false;
  await writeFile(temporary, `${JSON.stringify(persisted, null, 2)}\n`, 'utf8');
  try {
    if (await exists(path)) { await rename(path, backup); movedExisting = true; }
    try { await rename(temporary, path); } catch (error) {
      if (movedExisting) await rename(backup, path);
      throw error;
    }
    if (movedExisting) await rm(backup, { force: true });
  } catch (error) {
    await rm(temporary, { force: true });
    throw error;
  }
  return persisted;
}

export async function runCampaign(manifest: TargetManifest, campaign: CampaignFileV1, options: CampaignRunOptions = {}): Promise<CampaignRunResult> {
  validateCampaign(campaign, manifest);
  if (options.adapter && options.adapter.targetId !== manifest.id) throw new Error('Campaign adapter target mismatch');
  const maxSessionHistory = options.maxSessionHistory ?? 100;
  if (!Number.isSafeInteger(maxSessionHistory) || maxSessionHistory <= 0) throw new Error('Campaign session history limit must be a positive safe integer');
  const session = campaign.totals.sessions + 1;
  const startedAt = new Date().toISOString();
  const world = WorldModel.fromSnapshot(campaign.world, options.adapter);
  const corpus = new ActionCorpus(campaign.corpus.entries);
  const autonomy = await autonomousPlaytest(manifest, { ...options, adapter: options.adapter, world, corpus });
  const registry = new FindingRegistry(campaign.findings);
  const newFindingSignatures = [...new Set(autonomy.episodeRecords.flatMap(record => registry.recordRun(record.report, session)))].sort();
  if (options.verifyFindings && newFindingSignatures.length && !options.signal?.aborted) {
    await verifyFindingRecords(registry, new PlaytestRunner(), manifest, newFindingSignatures, {
      attempts: options.verificationAttempts ?? 3,
      requiredMatches: options.verificationRequiredMatches ?? options.verificationAttempts ?? 3,
      maxElapsedMs: options.verificationMaxElapsedMs ?? 60_000,
      signal: options.signal,
    });
  }
  const sessionSummary: CampaignSessionV1 = {
    session,
    startedAt,
    completedAt: new Date().toISOString(),
    seed: autonomy.seed,
    stopReason: autonomy.stopReason,
    episodes: autonomy.episodes,
    actions: autonomy.actionCount,
    elapsedMs: autonomy.elapsedMs,
    newFindingSignatures,
    determinismSignature: autonomyDeterminismSignature(autonomy),
  };
  const updated = cloneCampaign({
    ...campaign,
    totals: {
      sessions: session,
      episodes: campaign.totals.episodes + autonomy.episodes,
      actions: campaign.totals.actions + autonomy.actionCount,
      elapsedMs: campaign.totals.elapsedMs + autonomy.elapsedMs,
    },
    world: autonomy.world,
    corpus: serializeCorpus(corpus, manifest),
    findings: [...registry.records],
    sessions: [...campaign.sessions, sessionSummary].slice(-maxSessionHistory),
  });
  return { campaign: updated, autonomy, newFindingSignatures };
}
