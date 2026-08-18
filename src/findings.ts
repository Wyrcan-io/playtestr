import { createHash } from 'node:crypto';
import { fingerprintObservation } from './observations.js';
import type { EvidenceLevel, OracleKind, OracleResult, TerminalObservation } from './types.js';

export interface FindingInput {
  targetId: string;
  kind: OracleKind;
  severity: OracleResult['severity'];
  evidenceLevel?: EvidenceLevel;
  message: string;
  atAction: number;
  observation?: TerminalObservation;
  volatilePatterns?: readonly string[];
  discriminator?: string | number;
}

function digest(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

export function createFinding(input: FindingInput): OracleResult {
  const structural = input.observation
    ? fingerprintObservation(input.observation, { volatilePatterns: input.volatilePatterns }).structural
    : undefined;
  return {
    signatureVersion: 1,
    signature: digest({
      version: 1,
      targetId: input.targetId,
      kind: input.kind,
      discriminator: input.discriminator,
      structural,
    }),
    kind: input.kind,
    severity: input.severity,
    evidenceLevel: input.evidenceLevel ?? 'observed',
    message: input.message,
    atAction: input.atAction,
  };
}

export function sameFinding(left: Pick<OracleResult, 'signature'>, right: Pick<OracleResult, 'signature'>): boolean {
  return left.signature === right.signature;
}
