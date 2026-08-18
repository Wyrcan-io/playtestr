import { createHash } from 'node:crypto';
import type { ObservationFingerprint, TerminalObservation } from './types.js';

function digest(value: string): string {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

export interface ObservationNormalizationOptions {
  volatilePatterns?: readonly string[];
}

export function normalizeScreenText(text: string, options: ObservationNormalizationOptions = {}): string {
  let normalized = text
    .replace(/\r\n/gu, '\n')
    .split('\n')
    .map(line => line.replace(/\s+$/u, ''))
    .join('\n')
    .replace(/\n+$/u, '');
  for (const pattern of options.volatilePatterns ?? []) {
    normalized = normalized.replace(new RegExp(pattern, 'g'), '<volatile>');
  }
  return normalized;
}

export function fingerprintObservation(
  observation: Pick<TerminalObservation, 'cols' | 'rows' | 'text' | 'cursor' | 'alternateBuffer'>,
  options: ObservationNormalizationOptions = {},
): ObservationFingerprint {
  const text = normalizeScreenText(observation.text, options);
  const structural = [
    observation.cols,
    observation.rows,
    observation.alternateBuffer ? 'alternate' : 'normal',
    text,
  ].join('|');
  const exact = [
    structural,
    observation.cursor.x,
    observation.cursor.y,
  ].join('|');
  return { exact: digest(exact), structural: digest(structural) };
}
