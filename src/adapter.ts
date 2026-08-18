import type { SemanticObservation } from './semantics.js';
import type { InputAction, TargetManifest, TerminalObservation } from './types.js';

export interface AdapterObservationContext {
  manifest: TargetManifest;
  observation: TerminalObservation;
  semantic: SemanticObservation;
  observationIndex: number;
  actions: readonly InputAction[];
}

export interface AdapterEvidence {
  tags?: string[];
  mechanics?: string[];
  milestones?: string[];
  completion?: boolean;
  hidden?: boolean;
  failure?: boolean;
  recoverable?: boolean;
}

export interface AdapterObjective {
  id: string;
  kind: 'mechanic' | 'milestone' | 'completion' | 'hidden' | 'recovery' | 'speedrun';
  description: string;
  priority?: number;
}

/** Structural protocol: adapter packages do not need a runtime dependency on Playtestr. */
export interface TargetAdapter {
  readonly version: 1;
  readonly id: string;
  readonly targetId: string;
  readonly actions?: readonly string[];
  readonly bootstrapActions?: readonly InputAction[];
  readonly objectives?: readonly AdapterObjective[];
  analyze(context: AdapterObservationContext): AdapterEvidence | Promise<AdapterEvidence>;
}
