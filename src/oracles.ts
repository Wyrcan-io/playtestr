import type { OracleResult, TerminalObservation } from './types.js';
import { createFinding } from './findings.js';

export interface ObservationCheckOptions {
  targetId: string;
  outputLimitExceeded?: boolean;
  volatilePatterns?: readonly string[];
}

export function checkObservation(
  observation: TerminalObservation,
  actionCount: number,
  options: ObservationCheckOptions,
): OracleResult[] {
  const findings: OracleResult[] = [];
  if (options.outputLimitExceeded) {
    findings.push(createFinding({
      targetId: options.targetId,
      kind: 'output-limit',
      severity: 'error',
      evidenceLevel: 'confirmed',
      message: 'The target exceeded the configured output limit.',
      atAction: actionCount,
      observation,
      volatilePatterns: options.volatilePatterns,
      discriminator: 'output-limit',
    }));
  }
  if (!options.outputLimitExceeded && !observation.processAlive && observation.exitCode !== undefined && observation.exitCode !== 0) {
    findings.push(createFinding({
      targetId: options.targetId,
      kind: 'crash',
      severity: 'error',
      evidenceLevel: 'confirmed',
      message: `Target exited with code ${observation.exitCode}.`,
      atAction: actionCount,
      observation,
      volatilePatterns: options.volatilePatterns,
      discriminator: `exit:${observation.exitCode}`,
    }));
  }
  if (!options.outputLimitExceeded && !observation.processAlive && observation.signal !== undefined) {
    findings.push(createFinding({
      targetId: options.targetId,
      kind: 'crash',
      severity: 'error',
      evidenceLevel: 'confirmed',
      message: `Target exited from signal ${observation.signal}.`,
      atAction: actionCount,
      observation,
      volatilePatterns: options.volatilePatterns,
      discriminator: `signal:${observation.signal}`,
    }));
  }
  return findings;
}
