import type { OracleResult, TerminalObservation } from './types.js';

export function checkObservation(observation: TerminalObservation, actionCount: number, maxOutputBytesExceeded = false): OracleResult[] {
  const findings: OracleResult[] = [];
  if (maxOutputBytesExceeded) findings.push({ kind: 'output-limit', severity: 'error', message: 'The target exceeded the configured output limit.', atAction: actionCount });
  if (!observation.processAlive && observation.exitCode !== undefined && observation.exitCode !== 0) {
    findings.push({ kind: 'crash', severity: 'error', message: `Target exited with code ${observation.exitCode}.`, atAction: actionCount });
  }
  if (!observation.processAlive && observation.signal !== undefined) {
    findings.push({ kind: 'crash', severity: 'error', message: `Target exited from signal ${observation.signal}.`, atAction: actionCount });
  }
  return findings;
}
