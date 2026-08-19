import { reproduceFinding, type ReplayRunner, type ReproductionOptions, type ReproductionResult } from './reproduce.js';
import type { EvidenceLevel, OracleKind, Replay, RunReport, TargetManifest } from './types.js';

export interface FindingRecordV1 {
  version: 1;
  signature: string;
  kind: OracleKind;
  severity: 'error' | 'warning';
  evidenceLevel: EvidenceLevel;
  occurrenceCount: number;
  firstSession: number;
  lastSession: number;
  messages: string[];
  statuses: RunReport['status'][];
  seeds: number[];
  replay: Replay;
  reproduction?: ReproductionResult;
}

const evidenceRank: Record<EvidenceLevel, number> = { observed: 0, reproduced: 1, confirmed: 2, reviewed: 3 };

function cloneReplay(replay: Replay): Replay {
  return { ...replay, args: [...replay.args], terminal: { ...replay.terminal }, actions: replay.actions.map(action => ({ ...action })) };
}

function cloneRecord(record: FindingRecordV1): FindingRecordV1 {
  return {
    ...record,
    messages: [...record.messages],
    statuses: [...record.statuses],
    seeds: [...record.seeds],
    replay: cloneReplay(record.replay),
    ...(record.reproduction ? { reproduction: { ...record.reproduction, attempts: record.reproduction.attempts.map(attempt => ({ ...attempt, observedSignatures: [...attempt.observedSignatures] })) } } : {}),
  };
}

export class FindingRegistry {
  private readonly bySignature = new Map<string, FindingRecordV1>();

  constructor(records: readonly FindingRecordV1[] = []) {
    for (const record of records) {
      if (record.version !== 1 || !/^[a-f0-9]{64}$/u.test(record.signature) || !Number.isSafeInteger(record.occurrenceCount) || record.occurrenceCount <= 0) {
        throw new Error('Finding registry contains an invalid V1 record');
      }
      if (this.bySignature.has(record.signature)) throw new Error(`Finding registry contains duplicate signature: ${record.signature}`);
      this.bySignature.set(record.signature, cloneRecord(record));
    }
  }

  get records(): readonly FindingRecordV1[] {
    return [...this.bySignature.values()].sort((left, right) => left.signature.localeCompare(right.signature)).map(cloneRecord);
  }

  recordRun(report: RunReport, session: number): string[] {
    if (!Number.isSafeInteger(session) || session <= 0) throw new Error('Finding session must be a positive safe integer');
    const created: string[] = [];
    for (const finding of report.findings) {
      const existing = this.bySignature.get(finding.signature);
      if (!existing) {
        this.bySignature.set(finding.signature, {
          version: 1,
          signature: finding.signature,
          kind: finding.kind,
          severity: finding.severity,
          evidenceLevel: finding.evidenceLevel,
          occurrenceCount: 1,
          firstSession: session,
          lastSession: session,
          messages: [finding.message],
          statuses: [report.status],
          seeds: report.seed === undefined ? [] : [report.seed],
          replay: cloneReplay(report.replay),
        });
        created.push(finding.signature);
        continue;
      }
      existing.occurrenceCount += 1;
      existing.lastSession = session;
      existing.messages = [...new Set([...existing.messages, finding.message])].sort();
      existing.statuses = [...new Set([...existing.statuses, report.status])].sort();
      if (report.seed !== undefined) existing.seeds = [...new Set([...existing.seeds, report.seed])].sort((left, right) => left - right);
      if (finding.severity === 'error') existing.severity = 'error';
      if (evidenceRank[finding.evidenceLevel] > evidenceRank[existing.evidenceLevel]) existing.evidenceLevel = finding.evidenceLevel;
      if (report.replay.actions.length < existing.replay.actions.length) existing.replay = cloneReplay(report.replay);
    }
    return created.sort();
  }

  applyReproduction(signature: string, reproduction: ReproductionResult): void {
    const record = this.bySignature.get(signature);
    if (!record) throw new Error(`Unknown finding signature: ${signature}`);
    if (reproduction.signature !== signature) throw new Error('Reproduction signature mismatch');
    record.reproduction = { ...reproduction, attempts: reproduction.attempts.map(attempt => ({ ...attempt, observedSignatures: [...attempt.observedSignatures] })) };
    if (reproduction.quorumMet && evidenceRank.reproduced > evidenceRank[record.evidenceLevel]) record.evidenceLevel = 'reproduced';
  }
}

export async function verifyFindingRecords(
  registry: FindingRegistry,
  runner: ReplayRunner,
  manifest: TargetManifest,
  signatures: readonly string[],
  options: ReproductionOptions = {},
): Promise<ReproductionResult[]> {
  const records = new Map(registry.records.map(record => [record.signature, record]));
  const results: ReproductionResult[] = [];
  for (const signature of [...new Set(signatures)].sort()) {
    if (options.signal?.aborted) break;
    const record = records.get(signature);
    if (!record) throw new Error(`Unknown finding signature: ${signature}`);
    const result = await reproduceFinding(runner, manifest, record.replay, signature, options);
    registry.applyReproduction(signature, result);
    results.push(result);
  }
  return results;
}
