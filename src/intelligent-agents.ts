import type { AgentContext, AgentProposal, AutonomousAgent, AgentRole } from './autonomy-types.js';
import type { InputAction } from './types.js';

const semanticKey = (actions: readonly InputAction[]): string => JSON.stringify(actions.map(action => action.key));
const clonePrefix = (actions: readonly InputAction[]): InputAction[] => actions.map(action => ({ ...action }));

function proposal(
  agent: AutonomousAgent,
  objectiveId: string,
  actions: InputAction[],
  score: number,
  reasons: string[],
  expectedTags: string[] = [],
): AgentProposal {
  return { agentId: agent.id, role: agent.role, objectiveId, actions, score, reasons, expectedTags };
}

function actionsFromContext(context: AgentContext): string[] {
  return [...new Set([
    ...context.allowedActions,
    ...(context.adapter?.actions ?? []),
    ...context.world.states.flatMap(state => state.actionHints),
  ])].filter(Boolean).sort();
}

function bounded(actions: InputAction[], context: AgentContext): InputAction[] {
  return actions.slice(0, context.maxActionsPerEpisode);
}

function productiveStates(context: AgentContext) {
  return [...context.world.states]
    .filter(state => !state.terminal)
    .sort((left, right) => left.shortestPrefix.length - right.shortestPrefix.length || left.id.localeCompare(right.id));
}

export class MechanicMapperAgent implements AutonomousAgent {
  readonly id = 'mechanic-mapper-v1';
  readonly role: AgentRole = 'mechanic-mapper';

  propose(context: AgentContext): AgentProposal[] {
    const candidates: AgentProposal[] = [];
    const actions = actionsFromContext(context);
    const tried = new Set(context.world.transitions.map(transition => `${transition.from}:${transition.action.key}`));
    for (const state of productiveStates(context)) {
      for (const key of actions) {
        if (tried.has(`${state.id}:${key}`)) continue;
        candidates.push(proposal(this, `map:${key}`, bounded([...clonePrefix(state.shortestPrefix), { key, waitMs: 40, label: 'mechanic-map' }], context), 110 - state.shortestPrefix.length * 3, ['untried-action-at-state'], []));
      }
    }
    return candidates;
  }
}

export class EdgeCaseAgent implements AutonomousAgent {
  readonly id = 'edge-case-v1';
  readonly role: AgentRole = 'edge-case';

  propose(context: AgentContext): AgentProposal[] {
    const actions = actionsFromContext(context);
    const base = productiveStates(context).slice(0, 3);
    const proposals: AgentProposal[] = [];
    for (const state of base) {
      for (const key of actions.slice(0, 6)) {
        const prefix = clonePrefix(state.shortestPrefix);
        proposals.push(proposal(this, `repeat:${key}`, bounded([...prefix, { key, waitMs: 0, label: 'edge:rapid' }, { key, waitMs: 0, label: 'edge:repeat' }], context), 93 - prefix.length, ['rapid-repeat'], ['error', 'failure']));
        proposals.push(proposal(this, `wait:${key}`, bounded([...prefix, { key, waitMs: 250, holdMs: 100, label: 'edge:timing' }], context), 88 - prefix.length, ['timing-boundary'], ['timing']));
        for (const second of actions.slice(0, 6)) {
          if (second === key) continue;
          proposals.push(proposal(this, `rapid-pair:${key}:${second}`, bounded([...prefix, { key, waitMs: 0, label: 'edge:rapid-pair' }, { key: second, waitMs: 0, label: 'edge:rapid-pair' }], context), 95 - prefix.length, ['rapid-action-pair'], ['error', 'timing']));
          proposals.push(proposal(this, `delayed-pair:${key}:${second}`, bounded([...prefix, { key, waitMs: 250, label: 'edge:delayed-pair' }, { key: second, waitMs: 0, label: 'edge:delayed-pair' }], context), 125 - prefix.length, ['delayed-action-pair'], ['timing', 'completion']));
          proposals.push(proposal(this, `mixed-timing:${key}:${second}`, bounded([
            ...prefix,
            { key, waitMs: 0, label: 'edge:mixed-rapid' },
            { key: second, waitMs: 0, label: 'edge:mixed-rapid' },
            { key, waitMs: 250, label: 'edge:mixed-delayed' },
            { key: second, waitMs: 0, label: 'edge:mixed-delayed' },
          ], context), 130 - prefix.length, ['compare-rapid-and-delayed-pair'], ['error', 'timing', 'completion']));
        }
      }
    }
    return proposals;
  }
}

export class SecretHunterAgent implements AutonomousAgent {
  readonly id = 'secret-hunter-v1';
  readonly role: AgentRole = 'secret-hunter';

  propose(context: AgentContext): AgentProposal[] {
    const actions = actionsFromContext(context);
    const counts = new Map<string, number>();
    for (const transition of context.world.transitions) counts.set(transition.action.key, (counts.get(transition.action.key) ?? 0) + transition.count);
    const uncommon = [...actions].sort((left, right) => (counts.get(left) ?? 0) - (counts.get(right) ?? 0) || left.localeCompare(right));
    const states = productiveStates(context).filter(state => state.shortestPrefix.length < context.maxActionsPerEpisode);
    const proposals: AgentProposal[] = [];
    for (const state of states) {
      for (const key of uncommon.slice(0, 5)) {
        proposals.push(proposal(this, `secret:${key}`, bounded([...clonePrefix(state.shortestPrefix), { key, waitMs: 40, label: 'secret-hunt' }], context), 98 - state.shortestPrefix.length * 2 - (counts.get(key) ?? 0), ['low-frequency-action', 'frontier-prefix'], ['secret', 'hidden']));
      }
    }
    return proposals;
  }
}

export class SpeedrunnerAgent implements AutonomousAgent {
  readonly id = 'speedrunner-v1';
  readonly role: AgentRole = 'speedrunner';

  propose(context: AgentContext): AgentProposal[] {
    const completion = context.world.completionPrefixes[0];
    if (!completion?.length) return [];
    const proposals = [proposal(this, 'speedrun:replay', clonePrefix(completion), 125, ['known-shortest-completion'], ['completion'])];
    for (let index = 0; index < completion.length; index += 1) {
      const actions = completion.slice(0, index).concat(completion.slice(index + 1)).map(action => ({ ...action, label: 'speedrun:remove-detour' }));
      if (actions.length) proposals.push(proposal(this, `speedrun:remove:${index}`, actions, 130 - actions.length, ['remove-one-action'], ['completion']));
    }
    return proposals;
  }
}

export class CompletionistAgent implements AutonomousAgent {
  readonly id = 'completionist-v1';
  readonly role: AgentRole = 'completionist';

  propose(context: AgentContext): AgentProposal[] {
    const openObjectives = context.world.objectives.filter(objective => objective.status !== 'complete').sort((left, right) => right.priority - left.priority || left.id.localeCompare(right.id));
    const missingTags = ['help', 'inventory', 'resource', 'navigation', 'puzzle', 'timing', 'text-entry', 'completion']
      .filter(tag => !context.world.states.some(state => state.tags.includes(tag)));
    const actions = actionsFromContext(context);
    const states = productiveStates(context).slice(0, 8);
    const proposals: AgentProposal[] = [];
    for (const state of states) {
      for (const key of actions) {
        const objective = openObjectives[0];
        const optionLabel = state.options?.find(option => option.key === key)?.label ?? '';
        const objectiveWords = `${objective?.id ?? ''} ${objective?.description ?? ''}`.toLowerCase().match(/[a-z]{3,}/gu) ?? [];
        const actionText = `${key} ${optionLabel}`.toLowerCase();
        const relevance = objectiveWords.filter(word => actionText.includes(word)).length * 25;
        proposals.push(proposal(this, objective?.id ?? `complete:${key}`, bounded([...clonePrefix(state.shortestPrefix), { key, waitMs: 60, label: 'completionist' }], context), 88 + openObjectives.length * 2 + relevance - state.shortestPrefix.length, ['unmet-objective', ...(relevance ? ['objective-action-match'] : []), ...(missingTags.length ? ['missing-semantic-tags'] : [])], missingTags.slice(0, 3)));
      }
    }
    return proposals;
  }
}

export class RecoveryAgent implements AutonomousAgent {
  readonly id = 'recovery-v1';
  readonly role: AgentRole = 'recovery';

  propose(context: AgentContext): AgentProposal[] {
    const recoveryKeys = ['Escape', 'Backspace', 'Enter', 'q', 'r'].filter(key => actionsFromContext(context).includes(key));
    const states = productiveStates(context).filter(state => state.failure || state.tags.some(tag => ['help', 'error', 'locked'].includes(tag)));
    return states.flatMap(state => recoveryKeys.map(key => proposal(this, `recover:${key}`, bounded([...clonePrefix(state.shortestPrefix), { key, waitMs: 60, label: 'recovery-test' }], context), 96 - state.shortestPrefix.length, ['recover-from-confusing-state'], ['recovery'])));
  }
}

export function defaultAutonomousAgents(): AutonomousAgent[] {
  return [
    new MechanicMapperAgent(),
    new EdgeCaseAgent(),
    new SecretHunterAgent(),
    new SpeedrunnerAgent(),
    new CompletionistAgent(),
    new RecoveryAgent(),
  ];
}

export function deduplicateProposals(proposals: readonly AgentProposal[]): AgentProposal[] {
  const unique = new Map<string, AgentProposal>();
  for (const candidate of proposals) {
    const key = `${candidate.agentId}:${semanticKey(candidate.actions)}`;
    const previous = unique.get(key);
    if (!previous || candidate.score > previous.score) unique.set(key, candidate);
  }
  return [...unique.values()];
}
