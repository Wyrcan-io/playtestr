import { createHash } from 'node:crypto';
import type { AgentContext, AgentProposal, AgentRole, AutonomousAgent } from './autonomy-types.js';
import type { InputAction } from './types.js';

export interface SupervisorRequestV1 {
  version: 1;
  requestId: string;
  targetId: string;
  seed: number;
  allowedActions: string[];
  maxActionsPerProposal: number;
  world: {
    episodes: number;
    states: number;
    transitions: number;
    mechanics: string[];
    milestones: string[];
    objectives: Array<{ id: string; kind: string; description: string; status: string }>;
    recentSemantics: Array<{ tags: string[]; actionHints: string[]; milestones: string[]; terminal: boolean }>;
  };
}

export interface SupervisorProposalV1 {
  objectiveId: string;
  actions: InputAction[];
  score: number;
  reasons?: string[];
  expectedTags?: string[];
}

export interface SupervisorProvider {
  readonly id: string;
  readonly version: string;
  propose(request: SupervisorRequestV1, signal: AbortSignal): unknown | Promise<unknown>;
}

export interface ProviderSupervisedAgentOptions {
  role?: AgentRole;
  timeoutMs?: number;
  maxResponseBytes?: number;
  maxProposals?: number;
}

function requestFor(context: AgentContext): SupervisorRequestV1 {
  const body = {
    targetId: context.manifest.id,
    seed: context.seed,
    allowedActions: [...context.allowedActions],
    maxActionsPerProposal: context.maxActionsPerEpisode,
    worldSignature: {
      episodes: context.world.episodes,
      states: context.world.states.map(state => state.id),
      transitions: context.world.transitions.map(transition => transition.id),
      mechanics: context.world.mechanics.map(mechanic => mechanic.id),
      milestones: context.world.milestones,
      objectives: context.world.objectives.map(objective => [objective.id, objective.status]),
    },
  };
  const requestId = createHash('sha256').update(JSON.stringify(body), 'utf8').digest('hex');
  return {
    version: 1,
    requestId,
    targetId: context.manifest.id,
    seed: context.seed,
    allowedActions: [...context.allowedActions],
    maxActionsPerProposal: context.maxActionsPerEpisode,
    world: {
      episodes: context.world.episodes,
      states: context.world.states.length,
      transitions: context.world.transitions.length,
      mechanics: context.world.mechanics.map(mechanic => mechanic.id).slice(0, 200),
      milestones: context.world.milestones.slice(0, 200),
      objectives: context.world.objectives.slice(0, 100).map(objective => ({ id: objective.id, kind: objective.kind, description: objective.description.slice(0, 500), status: objective.status })),
      recentSemantics: [...context.world.states].sort((left, right) => right.firstSeenEpisode - left.firstSeenEpisode || left.id.localeCompare(right.id)).slice(0, 20).map(state => ({ tags: state.tags.slice(0, 30), actionHints: state.actionHints.slice(0, 30), milestones: state.milestones.slice(0, 30), terminal: state.terminal })),
    },
  };
}

function stringArray(value: unknown, maximum: number): string[] | undefined {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > maximum || value.some(item => typeof item !== 'string' || !item || item.length > 500)) return undefined;
  return [...new Set(value as string[])];
}

function validateProposal(value: unknown, context: AgentContext): Omit<AgentProposal, 'agentId' | 'role'> | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const raw = value as Record<string, unknown>;
  if (typeof raw.objectiveId !== 'string' || !raw.objectiveId || raw.objectiveId.length > 200) return undefined;
  if (!Number.isFinite(raw.score) || (raw.score as number) < 0 || (raw.score as number) > 1000) return undefined;
  if (!Array.isArray(raw.actions) || raw.actions.length === 0 || raw.actions.length > context.maxActionsPerEpisode) return undefined;
  const actions: InputAction[] = [];
  for (const value of raw.actions) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
    const action = value as Record<string, unknown>;
    if (typeof action.key !== 'string' || !context.allowedActions.includes(action.key)) return undefined;
    for (const timing of ['holdMs', 'waitMs'] as const) {
      const amount = action[timing];
      if (amount !== undefined && (!Number.isSafeInteger(amount) || (amount as number) < 0 || (amount as number) > 60_000)) return undefined;
    }
    actions.push({ key: action.key, ...(action.holdMs === undefined ? {} : { holdMs: action.holdMs as number }), ...(action.waitMs === undefined ? {} : { waitMs: action.waitMs as number }) });
  }
  const reasons = stringArray(raw.reasons, 20);
  const expectedTags = stringArray(raw.expectedTags, 30);
  if (!reasons || !expectedTags) return undefined;
  return { objectiveId: raw.objectiveId, actions, score: raw.score as number, reasons, expectedTags };
}

export class ProviderSupervisedAgent implements AutonomousAgent {
  readonly id: string;
  readonly role: AgentRole;
  private readonly timeoutMs: number;
  private readonly maxResponseBytes: number;
  private readonly maxProposals: number;

  constructor(readonly provider: SupervisorProvider, options: ProviderSupervisedAgentOptions = {}) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/u.test(provider.id) || !provider.version) throw new Error('Supervisor provider requires a safe ID and version');
    this.id = `supervisor:${provider.id}`;
    this.role = options.role ?? 'mechanic-mapper';
    this.timeoutMs = options.timeoutMs ?? 10_000;
    this.maxResponseBytes = options.maxResponseBytes ?? 64 * 1024;
    this.maxProposals = options.maxProposals ?? 8;
    for (const [label, value] of [['timeout', this.timeoutMs], ['response byte limit', this.maxResponseBytes], ['proposal limit', this.maxProposals]] as const) {
      if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`Supervisor ${label} must be a positive safe integer`);
    }
  }

  async propose(context: AgentContext): Promise<AgentProposal[]> {
    const request = requestFor(context);
    const controller = new AbortController();
    let timer: NodeJS.Timeout | undefined;
    try {
      const response = await Promise.race([
        Promise.resolve(this.provider.propose(request, controller.signal)),
        new Promise<never>((_, reject) => { timer = setTimeout(() => { controller.abort('timeout'); reject(new Error('Supervisor provider timed out')); }, this.timeoutMs); }),
      ]);
      const serialized = JSON.stringify(response);
      if (Buffer.byteLength(serialized, 'utf8') > this.maxResponseBytes || !Array.isArray(response) || response.length > this.maxProposals) return [];
      return response.map(value => validateProposal(value, context)).filter((value): value is Omit<AgentProposal, 'agentId' | 'role'> => Boolean(value)).map(proposal => ({ ...proposal, agentId: this.id, role: this.role }));
    } catch {
      return [];
    } finally {
      if (timer) clearTimeout(timer);
    }
  }
}
