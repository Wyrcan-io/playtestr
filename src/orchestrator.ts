import { ActionCorpus } from './corpus.js';
import { defaultAutonomousAgents, deduplicateProposals } from './intelligent-agents.js';
import { PlaytestRunner } from './runner.js';
import { WorldModel, type WorldModelDelta, type WorldModelSnapshot } from './world-model.js';
import type { TargetAdapter } from './adapter.js';
import type { AgentProposal, AutonomousAgent } from './autonomy-types.js';
import type { InputAction, RunReport, TargetManifest } from './types.js';

export interface AutonomyOptions {
  episodes?: number;
  maxActionsPerEpisode?: number;
  maxTotalActions?: number;
  maxElapsedMs?: number;
  maxElapsedMsPerEpisode?: number;
  seed?: number;
  adapter?: TargetAdapter;
  agents?: readonly AutonomousAgent[];
  world?: WorldModel;
  corpus?: ActionCorpus;
  stopOnCompletion?: boolean;
  stopOnHidden?: boolean;
  signal?: AbortSignal;
  learning?: AgentLearningSnapshot;
}

export interface AgentLearningRecord {
  agentId: string;
  role: AutonomousAgent['role'];
  selections: number;
  actions: number;
  totalReward: number;
  meanReward: number;
  stateYield: number;
  transitionYield: number;
  mechanicYield: number;
  milestoneYield: number;
  completionYield: number;
  hiddenYield: number;
  findingYield: number;
  lastSelectedEpisode: number;
}

export interface AgentLearningSnapshot {
  version: 1;
  totalSelections: number;
  records: AgentLearningRecord[];
}

export interface AgentContribution {
  agentId: string;
  role: AutonomousAgent['role'];
  selectedEpisodes: number;
  actions: number;
  newStates: number;
  newTransitions: number;
  newMechanics: number;
  newMilestones: number;
  findingSignatures: string[];
  completionDiscoveries: number;
  hiddenDiscoveries: number;
  reward: number;
}

export interface AutonomyEpisode {
  episode: number;
  agentId: string;
  role: AutonomousAgent['role'] | 'bootstrap';
  objectiveId: string;
  proposalScore: number;
  reasons: string[];
  expectedTags: string[];
  actions: InputAction[];
  report: RunReport;
  delta: WorldModelDelta;
}

export interface AutonomyResult {
  targetId: string;
  seed: number;
  episodes: number;
  actionCount: number;
  elapsedMs: number;
  stopReason: 'complete' | 'hidden-found' | 'episode-budget' | 'action-budget' | 'time-budget' | 'queue-exhausted' | 'cancelled' | 'runner-error';
  world: WorldModelSnapshot;
  contributions: AgentContribution[];
  episodeRecords: AutonomyEpisode[];
  learning: AgentLearningSnapshot;
}

const defaultActions = ['?', 'h', 'Enter', 'Space', 'Escape', 'Tab', 'Backspace', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'r', 'q'];
const timingClass = (action: InputAction): string => (action.waitMs ?? 0) === 0 ? 'rapid' : (action.waitMs ?? 0) >= 200 || (action.holdMs ?? 0) >= 100 ? 'slow' : 'normal';
const sequenceKey = (actions: readonly InputAction[]): string => JSON.stringify(actions.map(action => [action.key, timingClass(action)]));

function emptyContribution(agent: AutonomousAgent): AgentContribution {
  return { agentId: agent.id, role: agent.role, selectedEpisodes: 0, actions: 0, newStates: 0, newTransitions: 0, newMechanics: 0, newMilestones: 0, findingSignatures: [], completionDiscoveries: 0, hiddenDiscoveries: 0, reward: 0 };
}

function emptyLearning(agent: AutonomousAgent): AgentLearningRecord {
  return { agentId: agent.id, role: agent.role, selections: 0, actions: 0, totalReward: 0, meanReward: 0, stateYield: 0, transitionYield: 0, mechanicYield: 0, milestoneYield: 0, completionYield: 0, hiddenYield: 0, findingYield: 0, lastSelectedEpisode: 0 };
}

function learningState(agents: readonly AutonomousAgent[], snapshot?: AgentLearningSnapshot): Map<string, AgentLearningRecord> {
  if (snapshot && (snapshot.version !== 1 || !Number.isSafeInteger(snapshot.totalSelections) || snapshot.totalSelections < 0 || !Array.isArray(snapshot.records))) throw new Error('Agent learning snapshot is invalid');
  const supplied = new Map((snapshot?.records ?? []).map(record => [record.agentId, record]));
  return new Map(agents.map(agent => {
    const previous = supplied.get(agent.id);
    if (!previous) return [agent.id, emptyLearning(agent)];
    if (previous.role !== agent.role || !Number.isSafeInteger(previous.selections) || previous.selections < 0 || !Number.isFinite(previous.totalReward)) throw new Error(`Agent learning record is invalid: ${agent.id}`);
    return [agent.id, { ...previous }];
  }));
}

function proposalScore(candidate: AgentProposal, world: WorldModelSnapshot, learning: ReadonlyMap<string, AgentLearningRecord>): number {
  const record = learning.get(candidate.agentId);
  const totalSelections = [...learning.values()].reduce((total, value) => total + value.selections, 0);
  const exploration = !record || record.selections === 0 ? 80 : Math.sqrt((2 * Math.log(totalSelections + 1)) / record.selections) * 18;
  const learnedValue = record?.meanReward ?? 0;
  const unseenTagValue = candidate.expectedTags.filter(tag => !world.states.some(state => state.tags.includes(tag))).length * 5;
  const objectiveValue = world.objectives.some(objective => objective.id === candidate.objectiveId && objective.status !== 'complete') ? 15 : 0;
  return candidate.score + exploration + learnedValue + unseenTagValue + objectiveValue - candidate.actions.length * 0.25;
}

export async function autonomousPlaytest(manifest: TargetManifest, options: AutonomyOptions = {}): Promise<AutonomyResult> {
  const startedAt = Date.now();
  const seed = options.seed ?? 0;
  const episodeBudget = options.episodes ?? 30;
  const maxActionsPerEpisode = options.maxActionsPerEpisode ?? 12;
  const maxTotalActions = options.maxTotalActions ?? episodeBudget * maxActionsPerEpisode;
  const maxElapsedMs = options.maxElapsedMs ?? 120_000;
  for (const [name, value, allowZero] of [
    ['episodes', episodeBudget, false],
    ['maxActionsPerEpisode', maxActionsPerEpisode, false],
    ['maxTotalActions', maxTotalActions, true],
    ['maxElapsedMs', maxElapsedMs, false],
  ] as const) {
    if (!Number.isSafeInteger(value) || value < (allowZero ? 0 : 1)) throw new Error(`${name} must be a ${allowZero ? 'non-negative' : 'positive'} safe integer`);
  }
  const adapter = options.adapter;
  if (adapter && adapter.targetId !== manifest.id) throw new Error(`Adapter target ${adapter.targetId} does not match manifest target ${manifest.id}`);
  const agents = [...(options.agents ?? defaultAutonomousAgents())];
  if (!agents.length) throw new Error('Autonomy requires at least one agent');
  const duplicateAgent = agents.find((agent, index) => agents.findIndex(candidate => candidate.id === agent.id) !== index);
  if (duplicateAgent) throw new Error(`Duplicate autonomous agent id: ${duplicateAgent.id}`);
  const allowedActions = [...new Set(manifest.allowedKeys ?? adapter?.actions ?? defaultActions)].filter(Boolean).sort();
  if (!allowedActions.length) throw new Error('Autonomy requires at least one allowed action');
  const world = options.world ?? new WorldModel(manifest.id, adapter);
  const corpus = options.corpus ?? new ActionCorpus();
  const contributions = new Map(agents.map(agent => [agent.id, emptyContribution(agent)]));
  const learning = learningState(agents, options.learning);
  const seenSequences = new Set<string>();
  const episodeRecords: AutonomyEpisode[] = [];
  let actionCount = 0;
  let stopReason: AutonomyResult['stopReason'] = 'episode-budget';

  const runEpisode = async (agentId: string, role: AutonomyEpisode['role'], objectiveId: string, score: number, reasons: string[], expectedTags: string[], actions: InputAction[]): Promise<AutonomyEpisode> => {
    const report = await new PlaytestRunner({ corpus }).run(manifest, {
      seed,
      actions,
      maxActions: actions.length,
      maxElapsedMs: options.maxElapsedMsPerEpisode ?? manifest.episodeTimeoutMs,
      signal: options.signal,
    });
    const delta = await world.ingest(report, manifest, adapter);
    const record: AutonomyEpisode = { episode: episodeRecords.length + 1, agentId, role, objectiveId, proposalScore: score, reasons, expectedTags, actions: actions.map(action => ({ ...action })), report, delta };
    episodeRecords.push(record);
    actionCount += report.actionCount;
    return record;
  };

  const bootstrapActions = (adapter?.bootstrapActions ?? []).slice(0, Math.min(maxActionsPerEpisode, maxTotalActions)).map(action => ({ ...action }));
  if (bootstrapActions.some(action => !allowedActions.includes(action.key))) throw new Error('Adapter bootstrap action is outside the allowed action vocabulary');
  const bootstrap = await runEpisode('system', 'bootstrap', 'observe-initial-state', 0, ['bootstrap-observation'], [], bootstrapActions);
  seenSequences.add(sequenceKey(bootstrapActions));
  if (bootstrap.report.status === 'cancelled') stopReason = 'cancelled';
  else if (bootstrap.report.termination.kind === 'runner-error') stopReason = 'runner-error';

  while (episodeRecords.length < episodeBudget && stopReason === 'episode-budget') {
    if (options.signal?.aborted) { stopReason = 'cancelled'; break; }
    if (Date.now() - startedAt >= maxElapsedMs) { stopReason = 'time-budget'; break; }
    if (actionCount >= maxTotalActions) { stopReason = 'action-budget'; break; }
    const snapshot = world.snapshot();
    if (options.stopOnCompletion && snapshot.completionPrefixes.length) { stopReason = 'complete'; break; }
    if (options.stopOnHidden && snapshot.hiddenPrefixes.length) { stopReason = 'hidden-found'; break; }
    const context = { manifest, adapter, world: snapshot, allowedActions, maxActionsPerEpisode, seed };
    const generated = (await Promise.all(agents.map(agent => agent.propose(context)))).flat();
    const candidates = deduplicateProposals(generated)
      .filter(candidate => candidate.actions.length > 0 && candidate.actions.length <= maxActionsPerEpisode)
      .filter(candidate => candidate.actions.every(action => allowedActions.includes(action.key)))
      .filter(candidate => !seenSequences.has(sequenceKey(candidate.actions)))
      .filter(candidate => candidate.actions.length <= maxTotalActions - actionCount)
      .map(candidate => ({ candidate, adjustedScore: proposalScore(candidate, snapshot, learning) }))
      .sort((left, right) => right.adjustedScore - left.adjustedScore
        || left.candidate.agentId.localeCompare(right.candidate.agentId)
        || left.candidate.objectiveId.localeCompare(right.candidate.objectiveId)
        || sequenceKey(left.candidate.actions).localeCompare(sequenceKey(right.candidate.actions)));
    const selected = candidates[0];
    if (!selected) { stopReason = 'queue-exhausted'; break; }
    seenSequences.add(sequenceKey(selected.candidate.actions));
    const record = await runEpisode(
      selected.candidate.agentId,
      selected.candidate.role,
      selected.candidate.objectiveId,
      selected.adjustedScore,
      selected.candidate.reasons,
      selected.candidate.expectedTags,
      selected.candidate.actions,
    );
    const contribution = contributions.get(selected.candidate.agentId)!;
    contribution.selectedEpisodes += 1;
    contribution.actions += record.report.actionCount;
    contribution.newStates += record.delta.newStates.length;
    contribution.newTransitions += record.delta.newTransitions.length;
    contribution.newMechanics += record.delta.newMechanics.length;
    contribution.newMilestones += record.delta.newMilestones.length;
    contribution.findingSignatures = [...new Set([...contribution.findingSignatures, ...record.report.findings.map(finding => finding.signature)])].sort();
    if (record.delta.completionDiscovered) contribution.completionDiscoveries += 1;
    if (record.delta.hiddenDiscovered) contribution.hiddenDiscoveries += 1;
    contribution.reward += record.delta.reward;
    const learned = learning.get(selected.candidate.agentId)!;
    learned.selections += 1;
    learned.actions += record.report.actionCount;
    learned.totalReward += record.delta.reward;
    learned.meanReward = Number((learned.totalReward / learned.selections).toFixed(3));
    learned.stateYield += record.delta.newStates.length;
    learned.transitionYield += record.delta.newTransitions.length;
    learned.mechanicYield += record.delta.newMechanics.length;
    learned.milestoneYield += record.delta.newMilestones.length;
    learned.completionYield += record.delta.completionDiscovered ? 1 : 0;
    learned.hiddenYield += record.delta.hiddenDiscovered ? 1 : 0;
    learned.findingYield += record.report.findings.length;
    learned.lastSelectedEpisode = [...learning.values()].reduce((total, value) => total + value.selections, 0);
    if (record.report.status === 'cancelled') stopReason = 'cancelled';
    if (record.report.termination.kind === 'runner-error') stopReason = 'runner-error';
  }

  const finalWorld = world.snapshot();
  if (stopReason === 'episode-budget' && options.stopOnCompletion && finalWorld.completionPrefixes.length) stopReason = 'complete';
  if (stopReason === 'episode-budget' && options.stopOnHidden && finalWorld.hiddenPrefixes.length) stopReason = 'hidden-found';
  return {
    targetId: manifest.id,
    seed,
    episodes: episodeRecords.length,
    actionCount,
    elapsedMs: Date.now() - startedAt,
    stopReason,
    world: finalWorld,
    contributions: [...contributions.values()].sort((left, right) => left.agentId.localeCompare(right.agentId)),
    episodeRecords,
    learning: {
      version: 1,
      totalSelections: [...learning.values()].reduce((total, record) => total + record.selections, 0),
      records: [...learning.values()].sort((left, right) => left.agentId.localeCompare(right.agentId)).map(record => ({ ...record })),
    },
  };
}
