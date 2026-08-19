import { fingerprintObservation } from './observations.js';
import { analyzeTerminalObservation, type SemanticObservation, type SemanticOption } from './semantics.js';
import type { TargetAdapter } from './adapter.js';
import type { InputAction, RunReport, TargetManifest } from './types.js';

export interface WorldState {
  id: string;
  visits: number;
  firstSeenEpisode: number;
  shortestPrefix: InputAction[];
  semanticSignature: string;
  tags: string[];
  actionHints: string[];
  options?: SemanticOption[];
  milestones: string[];
  terminal: boolean;
  completion: boolean;
  hidden: boolean;
  failure: boolean;
  recoverable: boolean;
}

export interface WorldTransition {
  id: string;
  from: string;
  to: string;
  action: InputAction;
  count: number;
  changed: boolean;
  firstSeenEpisode: number;
}

export interface WorldActionOutcome {
  id: string;
  stateId: string;
  action: InputAction;
  attempts: number;
  changedCount: number;
  blockedCount: number;
  novelDestinationCount: number;
  failureCount: number;
  recoveryCount: number;
  completionCount: number;
  hiddenCount: number;
  totalReward: number;
  meanReward: number;
  destinations: string[];
}

export type FrontierStatus = 'untried' | 'uncertain' | 'productive' | 'blocked' | 'exhausted';

export interface WorldFrontier {
  id: string;
  stateId: string;
  action: InputAction;
  attempts: number;
  status: FrontierStatus;
  noveltyYield: number;
  expectedReward: number;
  priority: number;
}

export interface PrerequisiteHypothesis {
  id: string;
  actionKey: string;
  blockedStates: string[];
  productiveStates: string[];
  evidenceCount: number;
  confidence: number;
}

export interface MechanicHypothesis {
  id: string;
  evidenceCount: number;
  confidence: number;
  states: string[];
  actions: string[];
  sources: Array<'semantic' | 'transition' | 'adapter'>;
}

export interface WorldObjective {
  id: string;
  kind: 'mechanic' | 'milestone' | 'completion' | 'hidden' | 'recovery' | 'speedrun';
  description: string;
  priority: number;
  status: 'open' | 'observed' | 'complete';
}

export interface WorldModelSnapshotV1 {
  version: 1;
  targetId: string;
  episodes: number;
  states: WorldState[];
  transitions: WorldTransition[];
  mechanics: MechanicHypothesis[];
  milestones: string[];
  objectives: WorldObjective[];
  completionPrefixes: InputAction[][];
  hiddenPrefixes: InputAction[][];
}

export interface WorldModelSnapshot {
  version: 2;
  targetId: string;
  episodes: number;
  states: WorldState[];
  transitions: WorldTransition[];
  mechanics: MechanicHypothesis[];
  milestones: string[];
  objectives: WorldObjective[];
  completionPrefixes: InputAction[][];
  hiddenPrefixes: InputAction[][];
  actionVocabulary: string[];
  actionOutcomes: WorldActionOutcome[];
  frontiers: WorldFrontier[];
  prerequisites: PrerequisiteHypothesis[];
}

export type WorldModelSnapshotInput = WorldModelSnapshotV1 | WorldModelSnapshot;

export interface RewardComponents {
  states: number;
  transitions: number;
  mechanics: number;
  milestones: number;
  completion: number;
  hidden: number;
  findings: number;
  recovery: number;
}

export interface WorldModelDelta {
  newStates: string[];
  newTransitions: string[];
  newMechanics: string[];
  newMilestones: string[];
  completionDiscovered: boolean;
  hiddenDiscovered: boolean;
  productiveActions: string[];
  blockedActions: string[];
  reward: number;
  rewardComponents: RewardComponents;
}

const actionKey = (action: InputAction): string => JSON.stringify([action.key, action.holdMs ?? 0, action.waitMs ?? 0]);
const sequenceKey = (actions: readonly InputAction[]): string => JSON.stringify(actions.map(action => [action.key, action.holdMs ?? 0, action.waitMs ?? 0]));
const outcomeId = (stateId: string, action: InputAction): string => `${stateId}:${JSON.stringify(action.key)}`;

function merge(values: readonly string[], additions: readonly string[]): string[] {
  return [...new Set([...values, ...additions])].sort();
}

function evidenceConfidence(count: number): number {
  return Math.min(0.95, Number((0.4 + Math.log2(count + 1) * 0.2).toFixed(2)));
}

export class WorldModel {
  private readonly statesById = new Map<string, WorldState>();
  private readonly transitionsById = new Map<string, WorldTransition>();
  private readonly mechanicsById = new Map<string, MechanicHypothesis>();
  private readonly milestoneIds = new Set<string>();
  private readonly objectiveById = new Map<string, WorldObjective>();
  private readonly completions = new Map<string, InputAction[]>();
  private readonly hidden = new Map<string, InputAction[]>();
  private readonly actionVocabulary = new Set<string>();
  private readonly outcomesById = new Map<string, WorldActionOutcome>();
  private episodeCount = 0;

  constructor(readonly targetId: string, adapter?: TargetAdapter) {
    if (adapter && adapter.targetId !== targetId) throw new Error(`Adapter target ${adapter.targetId} does not match ${targetId}`);
    for (const objective of adapter?.objectives ?? []) {
      this.objectiveById.set(objective.id, { ...objective, priority: objective.priority ?? 50, status: 'open' });
    }
    for (const action of adapter?.actions ?? []) this.actionVocabulary.add(action);
  }

  static fromSnapshot(snapshot: WorldModelSnapshotInput, adapter?: TargetAdapter): WorldModel {
    if (![1, 2].includes(snapshot.version) || typeof snapshot.targetId !== 'string' || !snapshot.targetId) throw new Error('World snapshot must be a valid V1 or V2 snapshot');
    if (!Number.isSafeInteger(snapshot.episodes) || snapshot.episodes < 0) throw new Error('World snapshot episode count is invalid');
    for (const key of ['states', 'transitions', 'mechanics', 'milestones', 'objectives', 'completionPrefixes', 'hiddenPrefixes'] as const) {
      if (!Array.isArray(snapshot[key])) throw new Error(`World snapshot ${key} must be an array`);
    }
    const world = new WorldModel(snapshot.targetId, adapter);
    world.episodeCount = snapshot.episodes;
    world.objectiveById.clear();
    for (const state of snapshot.states) {
      if (!state || typeof state.id !== 'string' || world.statesById.has(state.id) || !Number.isSafeInteger(state.visits) || state.visits <= 0 || !Array.isArray(state.shortestPrefix)) throw new Error('World snapshot contains an invalid or duplicate state');
      world.statesById.set(state.id, { ...state, shortestPrefix: state.shortestPrefix.map(action => ({ ...action })), tags: [...state.tags], actionHints: [...state.actionHints], options: state.options?.map(option => ({ ...option })), milestones: [...state.milestones] });
    }
    for (const transition of snapshot.transitions) {
      if (!transition || typeof transition.id !== 'string' || world.transitionsById.has(transition.id) || !world.statesById.has(transition.from) || !world.statesById.has(transition.to)) throw new Error('World snapshot contains an invalid or duplicate transition');
      world.transitionsById.set(transition.id, { ...transition, action: { ...transition.action } });
    }
    for (const mechanic of snapshot.mechanics) {
      if (!mechanic || typeof mechanic.id !== 'string' || world.mechanicsById.has(mechanic.id) || !Number.isSafeInteger(mechanic.evidenceCount) || mechanic.evidenceCount <= 0) throw new Error('World snapshot contains an invalid or duplicate mechanic');
      world.mechanicsById.set(mechanic.id, { ...mechanic, states: [...mechanic.states], actions: [...mechanic.actions], sources: [...mechanic.sources] });
    }
    for (const milestone of snapshot.milestones) {
      if (typeof milestone !== 'string' || !milestone) throw new Error('World snapshot contains an invalid milestone');
      world.milestoneIds.add(milestone);
    }
    for (const objective of snapshot.objectives) {
      if (!objective || typeof objective.id !== 'string' || world.objectiveById.has(objective.id)) throw new Error('World snapshot contains an invalid or duplicate objective');
      world.objectiveById.set(objective.id, { ...objective });
    }
    const restorePrefixes = (prefixes: readonly InputAction[][], destination: Map<string, InputAction[]>): void => {
      for (const prefix of prefixes) {
        if (!Array.isArray(prefix)) throw new Error('World snapshot contains an invalid action prefix');
        const copy = prefix.map(action => ({ ...action }));
        destination.set(sequenceKey(copy), copy);
      }
    };
    restorePrefixes(snapshot.completionPrefixes, world.completions);
    restorePrefixes(snapshot.hiddenPrefixes, world.hidden);
    if (snapshot.version === 2) {
      for (const key of ['actionVocabulary', 'actionOutcomes', 'frontiers', 'prerequisites'] as const) {
        if (!Array.isArray(snapshot[key])) throw new Error(`World snapshot ${key} must be an array`);
      }
      for (const key of snapshot.actionVocabulary) {
        if (typeof key !== 'string' || !key) throw new Error('World snapshot contains an invalid action vocabulary');
        world.actionVocabulary.add(key);
      }
      for (const outcome of snapshot.actionOutcomes) {
        if (!outcome || typeof outcome.id !== 'string' || world.outcomesById.has(outcome.id) || !world.statesById.has(outcome.stateId) || !Number.isSafeInteger(outcome.attempts) || outcome.attempts <= 0) throw new Error('World snapshot contains an invalid or duplicate action outcome');
        world.outcomesById.set(outcome.id, { ...outcome, action: { ...outcome.action }, destinations: [...outcome.destinations] });
      }
    } else {
      for (const state of snapshot.states) for (const key of state.actionHints) world.actionVocabulary.add(key);
      for (const transition of snapshot.transitions) {
        world.actionVocabulary.add(transition.action.key);
        const id = outcomeId(transition.from, transition.action);
        const existing = world.outcomesById.get(id);
        const destination = world.statesById.get(transition.to)!;
        if (existing) {
          existing.attempts += transition.count;
          existing.changedCount += transition.changed ? transition.count : 0;
          existing.blockedCount += !transition.changed || destination.failure || destination.tags.includes('locked') ? transition.count : 0;
          existing.destinations = merge(existing.destinations, [transition.to]);
        } else {
          world.outcomesById.set(id, {
            id,
            stateId: transition.from,
            action: { ...transition.action },
            attempts: transition.count,
            changedCount: transition.changed ? transition.count : 0,
            blockedCount: !transition.changed || destination.failure || destination.tags.includes('locked') ? transition.count : 0,
            novelDestinationCount: 0,
            failureCount: destination.failure ? transition.count : 0,
            recoveryCount: destination.recoverable ? transition.count : 0,
            completionCount: destination.completion ? transition.count : 0,
            hiddenCount: destination.hidden ? transition.count : 0,
            totalReward: 0,
            meanReward: 0,
            destinations: [transition.to],
          });
        }
      }
    }
    return world;
  }

  get episodes(): number { return this.episodeCount; }
  get states(): readonly WorldState[] { return [...this.statesById.values()].sort((left, right) => left.id.localeCompare(right.id)); }
  get transitions(): readonly WorldTransition[] { return [...this.transitionsById.values()].sort((left, right) => left.id.localeCompare(right.id)); }
  get mechanics(): readonly MechanicHypothesis[] { return [...this.mechanicsById.values()].sort((left, right) => left.id.localeCompare(right.id)); }
  get milestones(): readonly string[] { return [...this.milestoneIds].sort(); }

  private recordMechanic(id: string, stateId: string, action: InputAction | undefined, source: MechanicHypothesis['sources'][number], delta: WorldModelDelta): void {
    const existing = this.mechanicsById.get(id);
    if (!existing) {
      this.mechanicsById.set(id, {
        id,
        evidenceCount: 1,
        confidence: evidenceConfidence(1),
        states: [stateId],
        actions: action ? [action.key] : [],
        sources: [source],
      });
      delta.newMechanics.push(id);
      return;
    }
    existing.evidenceCount += 1;
    existing.confidence = evidenceConfidence(existing.evidenceCount);
    existing.states = merge(existing.states, [stateId]);
    existing.actions = merge(existing.actions, action ? [action.key] : []);
    existing.sources = [...new Set([...existing.sources, source])].sort();
  }

  private updateObjectives(evidence: { mechanics: readonly string[]; milestones: readonly string[]; completion: boolean; hidden: boolean }): void {
    for (const objective of this.objectiveById.values()) {
      if (objective.kind === 'mechanic' && evidence.mechanics.includes(objective.id)) objective.status = 'complete';
      if (objective.kind === 'milestone' && evidence.milestones.includes(objective.id)) objective.status = 'complete';
      if (objective.kind === 'completion' && evidence.completion) objective.status = 'complete';
      if (objective.kind === 'hidden' && evidence.hidden) objective.status = 'complete';
    }
  }

  async ingest(report: RunReport, manifest: TargetManifest, adapter?: TargetAdapter): Promise<WorldModelDelta> {
    if (report.targetId !== this.targetId || manifest.id !== this.targetId) throw new Error('World model target mismatch');
    this.episodeCount += 1;
    for (const key of [...(manifest.allowedKeys ?? []), ...(adapter?.actions ?? [])]) this.actionVocabulary.add(key);
    const delta: WorldModelDelta = {
      newStates: [], newTransitions: [], newMechanics: [], newMilestones: [], completionDiscovered: false, hiddenDiscovered: false,
      productiveActions: [], blockedActions: [], reward: 0,
      rewardComponents: { states: 0, transitions: 0, mechanics: 0, milestones: 0, completion: 0, hidden: 0, findings: 0, recovery: 0 },
    };
    const stateIds: string[] = [];
    const semantics: SemanticObservation[] = [];

    for (let index = 0; index < report.observations.length; index += 1) {
      const observation = report.observations[index]!;
      const prefix = report.actions.slice(0, Math.min(index, report.actions.length));
      const stateId = fingerprintObservation(observation, manifest.observation).structural;
      const semantic = analyzeTerminalObservation(observation);
      const adapterEvidence = adapter ? await adapter.analyze({ manifest, observation, semantic, observationIndex: index, actions: prefix }) : {};
      const tags = merge(semantic.tags, adapterEvidence.tags ?? []);
      for (const key of semantic.actionHints) this.actionVocabulary.add(key);
      const milestones = [...new Set(adapterEvidence.milestones ?? [])].sort();
      const completion = Boolean(adapterEvidence.completion || tags.includes('completion'));
      const hidden = Boolean(adapterEvidence.hidden || tags.includes('secret'));
      const failure = Boolean(adapterEvidence.failure || tags.includes('failure') || tags.includes('error'));
      const recoverable = Boolean(adapterEvidence.recoverable || tags.includes('recovery'));
      const existing = this.statesById.get(stateId);
      if (!existing) {
        this.statesById.set(stateId, {
          id: stateId,
          visits: 1,
          firstSeenEpisode: this.episodeCount,
          shortestPrefix: prefix.map(action => ({ ...action })),
          semanticSignature: semantic.signature,
          tags,
          actionHints: [...semantic.actionHints].sort(),
          options: semantic.options.map(option => ({ ...option })),
          milestones,
          terminal: !observation.processAlive || completion || hidden,
          completion,
          hidden,
          failure,
          recoverable,
        });
        delta.newStates.push(stateId);
      } else {
        existing.visits += 1;
        if (prefix.length < existing.shortestPrefix.length) existing.shortestPrefix = prefix.map(action => ({ ...action }));
        existing.tags = merge(existing.tags, tags);
        existing.actionHints = merge(existing.actionHints, semantic.actionHints);
        existing.options = [...new Map([...(existing.options ?? []), ...semantic.options].map(option => [`${option.key ?? ''}:${option.label}`, { ...option }])).values()]
          .sort((left, right) => (left.key ?? '').localeCompare(right.key ?? '') || left.label.localeCompare(right.label));
        existing.milestones = merge(existing.milestones, milestones);
        existing.terminal ||= !observation.processAlive || completion || hidden;
        existing.completion ||= completion;
        existing.hidden ||= hidden;
        existing.failure ||= failure;
        existing.recoverable ||= recoverable;
      }
      for (const milestone of milestones) {
        if (!this.milestoneIds.has(milestone)) {
          this.milestoneIds.add(milestone);
          delta.newMilestones.push(milestone);
        }
      }
      const semanticMechanics = tags.filter(tag => !['completion', 'failure', 'error', 'secret', 'menu', 'confirmation'].includes(tag));
      for (const mechanic of semanticMechanics) this.recordMechanic(`semantic:${mechanic}`, stateId, report.actions[index - 1], 'semantic', delta);
      for (const mechanic of adapterEvidence.mechanics ?? []) this.recordMechanic(mechanic, stateId, report.actions[index - 1], 'adapter', delta);
      if (completion) {
        const key = sequenceKey(prefix);
        if (!this.completions.has(key)) {
          this.completions.set(key, prefix.map(action => ({ ...action })));
          delta.completionDiscovered = true;
        }
      }
      if (hidden) {
        const key = sequenceKey(prefix);
        if (!this.hidden.has(key)) {
          this.hidden.set(key, prefix.map(action => ({ ...action })));
          delta.hiddenDiscovered = true;
        }
      }
      this.updateObjectives({ mechanics: adapterEvidence.mechanics ?? [], milestones, completion, hidden });
      stateIds.push(stateId);
      semantics.push(semantic);
    }

    for (let index = 1; index < stateIds.length && index <= report.actions.length; index += 1) {
      const from = stateIds[index - 1]!;
      const to = stateIds[index]!;
      const action = report.actions[index - 1]!;
      const id = `${from}:${actionKey(action)}:${to}`;
      const existing = this.transitionsById.get(id);
      const isNewTransition = !existing;
      if (existing) existing.count += 1;
      else {
        this.transitionsById.set(id, { id, from, to, action: { ...action }, count: 1, changed: from !== to, firstSeenEpisode: this.episodeCount });
        delta.newTransitions.push(id);
      }
      const destination = this.statesById.get(to)!;
      const changed = from !== to;
      const blocked = !changed || destination.failure || destination.tags.includes('locked') || destination.tags.includes('error');
      const isNovelDestination = destination.firstSeenEpisode === this.episodeCount;
      const transitionReward = (isNovelDestination ? 5 : 0) + (isNewTransition ? 2 : 0) + (destination.completion ? 20 : 0) + (destination.hidden ? 20 : 0) + (destination.recoverable ? 5 : 0);
      const key = outcomeId(from, action);
      const outcome = this.outcomesById.get(key);
      if (outcome) {
        outcome.attempts += 1;
        outcome.changedCount += changed ? 1 : 0;
        outcome.blockedCount += blocked ? 1 : 0;
        outcome.novelDestinationCount += isNovelDestination ? 1 : 0;
        outcome.failureCount += destination.failure ? 1 : 0;
        outcome.recoveryCount += destination.recoverable ? 1 : 0;
        outcome.completionCount += destination.completion ? 1 : 0;
        outcome.hiddenCount += destination.hidden ? 1 : 0;
        outcome.totalReward += transitionReward;
        outcome.meanReward = Number((outcome.totalReward / outcome.attempts).toFixed(3));
        outcome.destinations = merge(outcome.destinations, [to]);
      } else {
        this.outcomesById.set(key, {
          id: key, stateId: from, action: { ...action }, attempts: 1, changedCount: changed ? 1 : 0,
          blockedCount: blocked ? 1 : 0, novelDestinationCount: isNovelDestination ? 1 : 0,
          failureCount: destination.failure ? 1 : 0, recoveryCount: destination.recoverable ? 1 : 0,
          completionCount: destination.completion ? 1 : 0, hiddenCount: destination.hidden ? 1 : 0,
          totalReward: transitionReward, meanReward: transitionReward, destinations: [to],
        });
      }
      if (changed) delta.productiveActions.push(action.key);
      if (blocked) delta.blockedActions.push(action.key);
      if (from !== to) this.recordMechanic(`action:${action.key}`, to, action, 'transition', delta);
      const previousCounters = semantics[index - 1]!.counters;
      const currentCounters = semantics[index]!.counters;
      for (const name of new Set([...Object.keys(previousCounters), ...Object.keys(currentCounters)])) {
        if (previousCounters[name] !== currentCounters[name]) this.recordMechanic(`counter:${name}`, to, action, 'transition', delta);
      }
    }
    delta.productiveActions = [...new Set(delta.productiveActions)].sort();
    delta.blockedActions = [...new Set(delta.blockedActions)].sort();
    delta.rewardComponents = {
      states: delta.newStates.length * 5,
      transitions: delta.newTransitions.length * 2,
      mechanics: delta.newMechanics.length * 4,
      milestones: delta.newMilestones.length * 8,
      completion: delta.completionDiscovered ? 20 : 0,
      hidden: delta.hiddenDiscovered ? 20 : 0,
      findings: (report.findings?.length ?? 0) * 8,
      recovery: stateIds.slice(1).filter(id => this.statesById.get(id)?.recoverable).length * 5,
    };
    delta.reward = Object.values(delta.rewardComponents).reduce((total, value) => total + value, 0);
    return delta;
  }

  shortestCompletionPrefix(): InputAction[] | undefined {
    return [...this.completions.values()].sort((left, right) => left.length - right.length || sequenceKey(left).localeCompare(sequenceKey(right)))[0]?.map(action => ({ ...action }));
  }

  private frontierSnapshot(): WorldFrontier[] {
    const frontiers: WorldFrontier[] = [];
    for (const state of this.states.filter(candidate => !candidate.terminal)) {
      for (const key of [...this.actionVocabulary].sort()) {
        const action = { key };
        const outcome = this.outcomesById.get(outcomeId(state.id, action));
        const status: FrontierStatus = !outcome
          ? 'untried'
          : outcome.blockedCount === outcome.attempts
            ? 'blocked'
            : outcome.changedCount > 0
              ? 'productive'
              : outcome.attempts < 2
                ? 'uncertain'
                : 'exhausted';
        const noveltyYield = outcome ? Number((outcome.novelDestinationCount / outcome.attempts).toFixed(3)) : 1;
        const expectedReward = outcome?.meanReward ?? 0;
        const uncertainty = outcome ? Math.sqrt(Math.log(this.episodeCount + 2) / (outcome.attempts + 1)) : 2;
        const statusValue: Record<FrontierStatus, number> = { untried: 30, uncertain: 20, productive: 12, blocked: -8, exhausted: -15 };
        frontiers.push({
          id: outcomeId(state.id, action), stateId: state.id, action,
          attempts: outcome?.attempts ?? 0, status, noveltyYield, expectedReward,
          priority: Number((statusValue[status] + expectedReward + noveltyYield * 10 + uncertainty * 5 - state.shortestPrefix.length).toFixed(3)),
        });
      }
    }
    return frontiers.sort((left, right) => right.priority - left.priority || left.id.localeCompare(right.id));
  }

  private prerequisiteSnapshot(): PrerequisiteHypothesis[] {
    const byAction = new Map<string, { blocked: Set<string>; productive: Set<string>; evidence: number }>();
    for (const outcome of this.outcomesById.values()) {
      const entry = byAction.get(outcome.action.key) ?? { blocked: new Set<string>(), productive: new Set<string>(), evidence: 0 };
      if (outcome.blockedCount > 0) entry.blocked.add(outcome.stateId);
      if (outcome.changedCount > 0) entry.productive.add(outcome.stateId);
      entry.evidence += outcome.blockedCount + outcome.changedCount;
      byAction.set(outcome.action.key, entry);
    }
    return [...byAction.entries()]
      .filter(([, evidence]) => evidence.blocked.size > 0 && evidence.productive.size > 0)
      .map(([key, evidence]) => ({
        id: `state-dependent:${key}`, actionKey: key,
        blockedStates: [...evidence.blocked].sort(), productiveStates: [...evidence.productive].sort(),
        evidenceCount: evidence.evidence, confidence: evidenceConfidence(evidence.evidence),
      }))
      .sort((left, right) => left.id.localeCompare(right.id));
  }

  snapshot(): WorldModelSnapshot {
    const sortPrefixes = (values: Iterable<InputAction[]>): InputAction[][] => [...values]
      .sort((left, right) => left.length - right.length || sequenceKey(left).localeCompare(sequenceKey(right)))
      .map(actions => actions.map(action => ({ ...action })));
    return {
      version: 2,
      targetId: this.targetId,
      episodes: this.episodeCount,
      states: this.states.map(state => ({ ...state, shortestPrefix: state.shortestPrefix.map(action => ({ ...action })), tags: [...state.tags], actionHints: [...state.actionHints], options: state.options?.map(option => ({ ...option })), milestones: [...state.milestones] })),
      transitions: this.transitions.map(transition => ({ ...transition, action: { ...transition.action } })),
      mechanics: this.mechanics.map(mechanic => ({ ...mechanic, states: [...mechanic.states], actions: [...mechanic.actions], sources: [...mechanic.sources] })),
      milestones: [...this.milestones],
      objectives: [...this.objectiveById.values()].sort((left, right) => left.id.localeCompare(right.id)).map(objective => ({ ...objective })),
      completionPrefixes: sortPrefixes(this.completions.values()),
      hiddenPrefixes: sortPrefixes(this.hidden.values()),
      actionVocabulary: [...this.actionVocabulary].sort(),
      actionOutcomes: [...this.outcomesById.values()].sort((left, right) => left.id.localeCompare(right.id)).map(outcome => ({ ...outcome, action: { ...outcome.action }, destinations: [...outcome.destinations] })),
      frontiers: this.frontierSnapshot(),
      prerequisites: this.prerequisiteSnapshot(),
    };
  }
}
