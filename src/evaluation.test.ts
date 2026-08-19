import { describe, expect, it } from 'vitest';
import { evaluateAutonomy } from './evaluation.js';
import type { AutonomyResult } from './orchestrator.js';

describe('autonomy evaluation', () => {
  it('reports explicit recall and missing externally declared evidence', () => {
    const result = {
      targetId: 'fixture', seed: 1, stopReason: 'episode-budget', episodes: 1, actionCount: 1, elapsedMs: 1,
      world: {
        version: 2, targetId: 'fixture', episodes: 1,
        states: [{ id: 'state', visits: 1, firstSeenEpisode: 1, shortestPrefix: [], semanticSignature: 'x', tags: ['help'], actionHints: [], milestones: ['started'], terminal: false, completion: false, hidden: false, failure: false, recoverable: false }],
        transitions: [], mechanics: [{ id: 'inspect', evidenceCount: 1, confidence: 0.6, states: ['state'], actions: [], sources: ['adapter'] }], milestones: ['started'], objectives: [], completionPrefixes: [], hiddenPrefixes: [],
        actionVocabulary: [], actionOutcomes: [], frontiers: [], prerequisites: [],
      },
      contributions: [], episodeRecords: [], learning: { version: 1, totalSelections: 0, records: [] },
    } as AutonomyResult;
    const evaluation = evaluateAutonomy(result, { id: 'scenario', targetId: 'fixture', expectedMechanics: ['inspect', 'move'], expectedMilestones: ['started'], expectedTags: ['help'], requireCompletion: true });
    expect(evaluation).toMatchObject({ passed: false, mechanicRecall: 0.5, milestoneRecall: 1, tagRecall: 1, missingMechanics: ['move'], completionFound: false });
  });
});
