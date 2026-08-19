import type { AgentContext } from './autonomy-types.js';
import type { InputAction } from './types.js';
import type { WorldFrontier, WorldState } from './world-model.js';

export interface WorldPlan {
  id: string;
  stateId: string;
  actions: InputAction[];
  score: number;
  reasons: string[];
  expectedTags: string[];
}

const clone = (actions: readonly InputAction[]): InputAction[] => actions.map(action => ({ ...action }));
const planKey = (actions: readonly InputAction[]): string => JSON.stringify(actions.map(action => action.key));

function semanticKeys(state: WorldState): string[] {
  return [...new Set([
    ...state.actionHints,
    ...(state.options ?? []).flatMap(option => option.key ? [option.key] : []),
  ])];
}

function frontierPlan(context: AgentContext, state: WorldState, frontier: WorldFrontier): WorldPlan | undefined {
  if (state.shortestPrefix.length + 1 > context.maxActionsPerEpisode) return undefined;
  const hints = semanticKeys(state);
  const hinted = hints.includes(frontier.action.key);
  const objectiveWords = context.world.objectives
    .filter(objective => objective.status !== 'complete')
    .flatMap(objective => `${objective.id} ${objective.description}`.toLowerCase().match(/[a-z]{3,}/gu) ?? []);
  const option = state.options?.find(candidate => candidate.key === frontier.action.key)?.label ?? '';
  const optionIndex = state.options?.findIndex(candidate => candidate.key === frontier.action.key) ?? -1;
  const presentationPriority = optionIndex >= 0 ? Math.max(0, 60 - optionIndex * 15) : 0;
  const relevant = objectiveWords.filter(word => `${frontier.action.key} ${option}`.toLowerCase().includes(word)).length;
  const prerequisite = context.world.prerequisites.some(hypothesis => hypothesis.actionKey === frontier.action.key && hypothesis.productiveStates.includes(state.id));
  const expectedTags = [
    ...(state.tags.includes('locked') ? ['recovery'] : []),
    ...(frontier.status === 'untried' ? ['novelty'] : []),
  ];
  return {
    id: `frontier:${state.id}:${frontier.action.key}`,
    stateId: state.id,
    actions: [...clone(state.shortestPrefix), { key: frontier.action.key, waitMs: 50, label: 'planner:frontier' }],
    score: Number((frontier.priority + (hinted ? 75 : 0) + presentationPriority + relevant * 25 + (prerequisite ? 20 : 0) + state.shortestPrefix.length * 8).toFixed(3)),
    reasons: [
      'return-then-explore',
      `frontier:${frontier.status}`,
      ...(hinted ? ['screen-action-hint'] : []),
      ...(optionIndex === 0 ? ['primary-presented-option'] : []),
      ...(relevant ? ['objective-action-match'] : []),
      ...(prerequisite ? ['state-dependent-action'] : []),
    ],
    expectedTags,
  };
}

/** Pure deterministic planning over a persisted world snapshot. */
export function planWorldFrontiers(context: AgentContext, limit = 128): WorldPlan[] {
  const states = new Map(context.world.states.map(state => [state.id, state]));
  const candidates = context.world.frontiers
    .filter(frontier => ['untried', 'uncertain'].includes(frontier.status))
    .flatMap(frontier => {
      const state = states.get(frontier.stateId);
      if (!state || state.terminal) return [];
      const planned = frontierPlan(context, state, frontier);
      return planned ? [planned] : [];
    });
  const unique = new Map<string, WorldPlan>();
  for (const candidate of candidates) {
    const key = planKey(candidate.actions);
    const previous = unique.get(key);
    if (!previous || candidate.score > previous.score) unique.set(key, candidate);
  }
  return [...unique.values()]
    .sort((left, right) => right.score - left.score || left.actions.length - right.actions.length || left.id.localeCompare(right.id))
    .slice(0, limit);
}
