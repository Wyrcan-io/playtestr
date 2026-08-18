import { createHash } from 'node:crypto';
import { autonomousPlaytest, type AutonomyOptions, type AutonomyResult } from './orchestrator.js';
import type { TargetAdapter } from './adapter.js';
import type { TargetManifest } from './types.js';

export interface EvaluationScenario {
  id: string;
  targetId: string;
  expectedMechanics?: string[];
  expectedMilestones?: string[];
  expectedTags?: string[];
  requireCompletion?: boolean;
  requireHidden?: boolean;
}

export interface AutonomyEvaluation {
  scenarioId: string;
  targetId: string;
  passed: boolean;
  mechanicRecall: number;
  milestoneRecall: number;
  tagRecall: number;
  observedMechanics: string[];
  observedMilestones: string[];
  observedTags: string[];
  missingMechanics: string[];
  missingMilestones: string[];
  missingTags: string[];
  completionFound: boolean;
  hiddenFound: boolean;
  uniqueStates: number;
  uniqueTransitions: number;
  actions: number;
  episodes: number;
  cleanupFailures: number;
  contributingAgents: string[];
  determinismSignature: string;
}

export interface ExecutableEvaluationScenario {
  scenario: EvaluationScenario;
  manifest: TargetManifest;
  adapter?: TargetAdapter;
  autonomy?: Omit<AutonomyOptions, 'adapter'>;
}

export interface EvaluationSuiteResult {
  passed: boolean;
  scenarioCount: number;
  evaluations: AutonomyEvaluation[];
  runs: AutonomyResult[];
}

const ratio = (observed: ReadonlySet<string>, expected: readonly string[]): number => expected.length === 0
  ? 1
  : Number((expected.filter(value => observed.has(value)).length / expected.length).toFixed(3));

function signature(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

export function autonomyDeterminismSignature(result: AutonomyResult): string {
  return signature({
    targetId: result.targetId,
    seed: result.seed,
    stopReason: result.stopReason,
    selected: result.episodeRecords.map(record => ({ agentId: record.agentId, objectiveId: record.objectiveId, actions: record.actions.map(action => [action.key, action.holdMs ?? 0, action.waitMs ?? 0]) })),
    states: result.world.states.map(state => ({ id: state.id, tags: state.tags, milestones: state.milestones, completion: state.completion, hidden: state.hidden })),
    mechanics: result.world.mechanics.map(mechanic => mechanic.id),
    milestones: result.world.milestones,
  });
}

export function evaluateAutonomy(result: AutonomyResult, scenario: EvaluationScenario): AutonomyEvaluation {
  if (scenario.targetId !== result.targetId) throw new Error(`Evaluation target ${scenario.targetId} does not match result target ${result.targetId}`);
  const expectedMechanics = [...new Set(scenario.expectedMechanics ?? [])].sort();
  const expectedMilestones = [...new Set(scenario.expectedMilestones ?? [])].sort();
  const expectedTags = [...new Set(scenario.expectedTags ?? [])].sort();
  const observedMechanics = [...new Set(result.world.mechanics.map(mechanic => mechanic.id))].sort();
  const observedMilestones = [...new Set(result.world.milestones)].sort();
  const observedTags = [...new Set(result.world.states.flatMap(state => state.tags))].sort();
  const mechanicSet = new Set(observedMechanics);
  const milestoneSet = new Set(observedMilestones);
  const tagSet = new Set(observedTags);
  const missingMechanics = expectedMechanics.filter(value => !mechanicSet.has(value));
  const missingMilestones = expectedMilestones.filter(value => !milestoneSet.has(value));
  const missingTags = expectedTags.filter(value => !tagSet.has(value));
  const completionFound = result.world.completionPrefixes.length > 0;
  const hiddenFound = result.world.hiddenPrefixes.length > 0;
  const cleanupFailures = result.episodeRecords.filter(record => !record.report.cleanup.confirmedExited || record.report.cleanup.error).length;
  const passed = missingMechanics.length === 0
    && missingMilestones.length === 0
    && missingTags.length === 0
    && (!scenario.requireCompletion || completionFound)
    && (!scenario.requireHidden || hiddenFound)
    && cleanupFailures === 0;
  return {
    scenarioId: scenario.id,
    targetId: result.targetId,
    passed,
    mechanicRecall: ratio(mechanicSet, expectedMechanics),
    milestoneRecall: ratio(milestoneSet, expectedMilestones),
    tagRecall: ratio(tagSet, expectedTags),
    observedMechanics,
    observedMilestones,
    observedTags,
    missingMechanics,
    missingMilestones,
    missingTags,
    completionFound,
    hiddenFound,
    uniqueStates: result.world.states.length,
    uniqueTransitions: result.world.transitions.length,
    actions: result.actionCount,
    episodes: result.episodes,
    cleanupFailures,
    contributingAgents: result.contributions.filter(contribution => contribution.newStates || contribution.newMechanics || contribution.newMilestones || contribution.findingSignatures.length).map(contribution => contribution.agentId).sort(),
    determinismSignature: autonomyDeterminismSignature(result),
  };
}

export async function runEvaluationSuite(scenarios: readonly ExecutableEvaluationScenario[]): Promise<EvaluationSuiteResult> {
  const evaluations: AutonomyEvaluation[] = [];
  const runs: AutonomyResult[] = [];
  for (const executable of scenarios) {
    if (executable.scenario.targetId !== executable.manifest.id) throw new Error(`Scenario ${executable.scenario.id} target mismatch`);
    const result = await autonomousPlaytest(executable.manifest, { ...executable.autonomy, adapter: executable.adapter });
    runs.push(result);
    evaluations.push(evaluateAutonomy(result, executable.scenario));
  }
  return { passed: evaluations.every(evaluation => evaluation.passed), scenarioCount: evaluations.length, evaluations, runs };
}
