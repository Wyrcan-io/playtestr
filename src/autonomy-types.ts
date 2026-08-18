import type { TargetAdapter } from './adapter.js';
import type { InputAction, TargetManifest } from './types.js';
import type { WorldModelSnapshot } from './world-model.js';

export type AgentRole = 'mechanic-mapper' | 'edge-case' | 'secret-hunter' | 'speedrunner' | 'completionist' | 'recovery';

export interface AgentContext {
  manifest: TargetManifest;
  adapter?: TargetAdapter;
  world: WorldModelSnapshot;
  allowedActions: readonly string[];
  maxActionsPerEpisode: number;
  seed: number;
}

export interface AgentProposal {
  agentId: string;
  role: AgentRole;
  objectiveId: string;
  actions: InputAction[];
  score: number;
  reasons: string[];
  expectedTags: string[];
}

export interface AutonomousAgent {
  readonly id: string;
  readonly role: AgentRole;
  propose(context: AgentContext): AgentProposal[] | Promise<AgentProposal[]>;
}
