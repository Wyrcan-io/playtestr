import { createHash } from 'node:crypto';
import { normalizeScreenText } from './observations.js';
import type { TerminalObservation } from './types.js';

export type BuiltInSemanticTag =
  | 'menu'
  | 'help'
  | 'inventory'
  | 'resource'
  | 'navigation'
  | 'combat'
  | 'puzzle'
  | 'timing'
  | 'text-entry'
  | 'confirmation'
  | 'completion'
  | 'failure'
  | 'error'
  | 'secret'
  | 'locked'
  | 'recovery';

export interface SemanticOption {
  key?: string;
  label: string;
}

export interface SemanticObservation {
  version: 1;
  signature: string;
  title?: string;
  lines: string[];
  prompt?: string;
  options: SemanticOption[];
  actionHints: string[];
  counters: Record<string, number>;
  tags: string[];
}

export interface SemanticAnalyzer {
  readonly id: string;
  analyze(observation: TerminalObservation): SemanticObservation | Promise<SemanticObservation>;
}

const tagPatterns: ReadonlyArray<[BuiltInSemanticTag, RegExp]> = [
  ['help', /\b(?:help|instructions?|controls?|how to play)\b/iu],
  ['inventory', /\b(?:inventory|items?|equipment|backpack|carrying)\b/iu],
  ['resource', /\b(?:gold|coins?|credits?|energy|health|mana|fuel|score|supplies|wood|ore)\b/iu],
  ['navigation', /\b(?:north|south|east|west|room|map|route|move|travel|door)\b/iu],
  ['combat', /\b(?:attack|fight|enemy|damage|weapon|defend|battle)\b/iu],
  ['puzzle', /\b(?:puzzle|code|solve|switch|lever|riddle|sequence)\b/iu],
  ['timing', /\b(?:time|timer|seconds?|wait|charge|cooldown|too early|too late)\b/iu],
  ['text-entry', /(?:^|\n)\s*(?:>|command:|type\s+\w+|enter\s+command)/iu],
  ['confirmation', /\b(?:confirm|are you sure|press enter|continue\?)\b/iu],
  ['completion', /\b(?:(?:mission|quest|trial|campaign|game|training|tutorial) complete|completed the|victory|you win|you won|successfully escaped|ending unlocked)\b/iu],
  ['failure', /\b(?:game over|you lose|failed|defeat|dead|failure)\b/iu],
  ['error', /\b(?:error|invalid|unknown command|not allowed|cannot|can't)\b/iu],
  ['secret', /\b(?:secret|hidden|bonus|easter egg|speedrun door)\b/iu],
  ['locked', /\b(?:locked|requires?|need\s+\w+|unavailable)\b/iu],
  ['recovery', /\b(?:back|return|resume|retry|restart|escape)\b/iu],
];

function digest(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

function normalizedKey(value: string): string | undefined {
  const key = value.trim().replace(/^['"`]|['"`]$/gu, '');
  if (!key) return undefined;
  const aliases: Record<string, string> = {
    enter: 'Enter', return: 'Enter', esc: 'Escape', escape: 'Escape', space: 'Space',
    tab: 'Tab', backspace: 'Backspace', up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight',
  };
  return aliases[key.toLowerCase()] ?? (key.length <= 32 ? key : undefined);
}

function extractOptions(lines: readonly string[]): SemanticOption[] {
  const options: SemanticOption[] = [];
  const patterns = [
    /^\s*\[([^\]]{1,20})\]\s*(.+)$/u,
    /^\s*\(([^)]{1,20})\)\s*(.+)$/u,
    /^\s*([0-9A-Za-z?])\s*[).:-]\s*(.+)$/u,
  ];
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = pattern.exec(line);
      if (!match) continue;
      options.push({ key: normalizedKey(match[1]!), label: match[2]!.trim() });
      break;
    }
  }
  return options;
}

function extractActionHints(text: string, options: readonly SemanticOption[]): string[] {
  const hints = options.flatMap(option => option.key ? [option.key] : []);
  const patterns = [
    /\bpress\s+(?:the\s+)?(?:key\s+)?([A-Za-z0-9?]+|Enter|Escape|Space|Tab|Backspace|Arrow(?:Up|Down|Left|Right))/giu,
    /\b(?:use|type)\s+['"`]([^'"`]{1,20})['"`]/giu,
  ];
  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      const key = normalizedKey(match[1]!);
      if (key) hints.push(key);
    }
  }
  return [...new Set(hints)];
}

function extractCounters(lines: readonly string[]): Record<string, number> {
  const counters: Record<string, number> = {};
  for (const line of lines) {
    for (const match of line.matchAll(/\b([A-Za-z][A-Za-z -]{1,24})\s*[:=]\s*(-?\d+(?:\.\d+)?)/gu)) {
      const label = match[1]!.trim().toLowerCase().replace(/\s+/gu, '-');
      const value = Number(match[2]);
      if (Number.isFinite(value)) counters[label] = value;
    }
  }
  return counters;
}

export function analyzeTerminalObservation(observation: TerminalObservation): SemanticObservation {
  const normalized = normalizeScreenText(observation.text);
  const lines = normalized.split('\n').map(line => line.trim()).filter(Boolean);
  const options = extractOptions(lines);
  const prompt = [...lines].reverse().find(line => /(?:[>:?]|\b(?:choose|select|press|command)\b)\s*$/iu.test(line));
  const tags = tagPatterns.filter(([, pattern]) => pattern.test(normalized)).map(([tag]) => tag);
  if (options.length >= 2) tags.push('menu');
  const actionHints = extractActionHints(normalized, options);
  const counters = extractCounters(lines);
  const stableTags = [...new Set(tags)].sort();
  const result = {
    version: 1 as const,
    title: lines[0],
    lines,
    prompt,
    options,
    actionHints,
    counters,
    tags: stableTags,
  };
  return { ...result, signature: digest(result) };
}

export class DeterministicSemanticAnalyzer implements SemanticAnalyzer {
  readonly id = 'deterministic-terminal-v1';
  analyze(observation: TerminalObservation): SemanticObservation {
    return analyzeTerminalObservation(observation);
  }
}
