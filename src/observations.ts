import { createHash } from 'node:crypto';
import type { ObservationFingerprint, TerminalObservation } from './types.js';

function digest(value: string): string {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

export function normalizeScreenText(text: string): string {
  return text
    .replace(/\r\n/gu, '\n')
    .split('\n')
    .map(line => line.replace(/\s+$/u, ''))
    .join('\n')
    .replace(/\n+$/u, '');
}

export function fingerprintObservation(observation: Pick<TerminalObservation, 'cols' | 'rows' | 'text' | 'cursor' | 'alternateBuffer'>): ObservationFingerprint {
  const text = normalizeScreenText(observation.text);
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
