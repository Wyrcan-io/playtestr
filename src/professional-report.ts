import { writeArtifactBundle, type ArtifactWriteResult } from './artifacts.js';
import type { BenchmarkResult } from './benchmark.js';
import type { CampaignFileV1 } from './campaign.js';
import type { AgentContribution, AutonomyResult } from './orchestrator.js';
import type { InputAction, Replay, TargetManifest } from './types.js';

export interface ProfessionalReportV1 {
  version: 1;
  generatedAt: string;
  target: {
    id: string;
    compatibilityKey: string;
  };
  campaign: {
    id: string;
    revision: number;
    totals: CampaignFileV1['totals'];
    createdAt: string;
    updatedAt: string;
  };
  summary: {
    observedStates: number;
    observedTransitions: number;
    observedMechanics: number;
    milestones: number;
    completionRoutes: number;
    hiddenRoutes: number;
    findings: number;
    reproducedFindings: number;
    cleanupFailures: number;
  };
  mechanics: CampaignFileV1['world']['mechanics'];
  milestones: string[];
  objectives: CampaignFileV1['world']['objectives'];
  completionRoutes: InputAction[][];
  hiddenRoutes: InputAction[][];
  findings: CampaignFileV1['findings'];
  contributions: AgentContribution[];
  benchmark?: BenchmarkResult;
  limitations: string[];
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function createProfessionalReport(
  manifest: TargetManifest,
  campaign: CampaignFileV1,
  options: { autonomy?: AutonomyResult; benchmark?: BenchmarkResult } = {},
): ProfessionalReportV1 {
  if (manifest.id !== campaign.targetId) throw new Error('Professional report target mismatch');
  if (options.autonomy && options.autonomy.targetId !== manifest.id) throw new Error('Professional report autonomy target mismatch');
  if (options.benchmark && options.benchmark.targetId !== manifest.id) throw new Error('Professional report benchmark target mismatch');
  const cleanupFailures = options.autonomy?.episodeRecords.filter(record => !record.report.cleanup.confirmedExited || record.report.cleanup.error).length ?? 0;
  return clone({
    version: 1,
    generatedAt: new Date().toISOString(),
    target: { id: manifest.id, compatibilityKey: campaign.targetCompatibilityKey },
    campaign: { id: campaign.id, revision: campaign.revision, totals: campaign.totals, createdAt: campaign.createdAt, updatedAt: campaign.updatedAt },
    summary: {
      observedStates: campaign.world.states.length,
      observedTransitions: campaign.world.transitions.length,
      observedMechanics: campaign.world.mechanics.length,
      milestones: campaign.world.milestones.length,
      completionRoutes: campaign.world.completionPrefixes.length,
      hiddenRoutes: campaign.world.hiddenPrefixes.length,
      findings: campaign.findings.length,
      reproducedFindings: campaign.findings.filter(finding => finding.reproduction?.quorumMet).length,
      cleanupFailures,
    },
    mechanics: campaign.world.mechanics,
    milestones: campaign.world.milestones,
    objectives: campaign.world.objectives,
    completionRoutes: campaign.world.completionPrefixes,
    hiddenRoutes: campaign.world.hiddenPrefixes,
    findings: campaign.findings,
    contributions: options.autonomy?.contributions ?? [],
    ...(options.benchmark ? { benchmark: options.benchmark } : {}),
    limitations: [
      'Observed state and mechanic evidence is black-box terminal evidence, not source-code coverage.',
      'Absence of a finding does not prove absence of defects or hidden content.',
      'Local PTY execution is not a sandbox and is only suitable for explicitly trusted targets.',
      'Autonomous findings are observed or reproduced; human confirmation remains a separate review step.',
    ],
  });
}

const escapeHtml = (value: unknown): string => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#39;');

const safeMarkdown = (value: unknown): string => String(value)
  .replace(/[\r\n]+/gu, ' ')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;');

const actionText = (actions: readonly InputAction[]): string => actions.length
  ? actions.map(action => `${action.key}${action.waitMs === undefined ? '' : ` @${action.waitMs}ms`}`).join(' → ')
  : '(initial state)';

function htmlList(values: readonly string[]): string {
  return values.length ? `<ul>${values.map(value => `<li>${escapeHtml(value)}</li>`).join('')}</ul>` : '<p class="muted">None observed.</p>';
}

export function renderProfessionalReportHtml(report: ProfessionalReportV1): string {
  const findingRows = report.findings.map(finding => `<tr><td><code>${escapeHtml(finding.signature.slice(0, 12))}</code></td><td>${escapeHtml(finding.severity)}</td><td>${escapeHtml(finding.kind)}</td><td>${escapeHtml(finding.evidenceLevel)}</td><td>${finding.occurrenceCount}</td><td>${escapeHtml(finding.messages.join(' / '))}</td></tr>`).join('');
  const mechanicRows = report.mechanics.map(mechanic => `<tr><td>${escapeHtml(mechanic.id)}</td><td>${mechanic.confidence}</td><td>${mechanic.evidenceCount}</td><td>${escapeHtml(mechanic.sources.join(', '))}</td></tr>`).join('');
  const routeList = (routes: readonly InputAction[][]): string => routes.length ? `<ol>${routes.map(route => `<li><code>${escapeHtml(actionText(route))}</code></li>`).join('')}</ol>` : '<p class="muted">None observed.</p>';
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>Playtestr report — ${escapeHtml(report.target.id)}</title>
<style>:root{color-scheme:dark}body{font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:auto;padding:2rem;background:#0c1117;color:#dce6ef}h1,h2{color:#fff}section{margin:2rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem}.card{background:#151d27;border:1px solid #2c3948;border-radius:8px;padding:1rem}.value{font-size:1.7rem;font-weight:700}table{border-collapse:collapse;width:100%;display:block;overflow:auto}th,td{text-align:left;padding:.55rem;border-bottom:1px solid #2c3948;vertical-align:top}code{color:#9fe3bf;word-break:break-all}.muted{color:#8fa1b3}.error{color:#ff9b9b}</style></head>
<body><header><h1>Playtestr report</h1><p><strong>${escapeHtml(report.target.id)}</strong> · campaign ${escapeHtml(report.campaign.id)} revision ${report.campaign.revision}</p><p class="muted">Generated ${escapeHtml(report.generatedAt)}</p></header>
<section><h2>Executive summary</h2><div class="grid">
${Object.entries(report.summary).map(([name, value]) => `<div class="card"><div class="value">${value}</div><div>${escapeHtml(name)}</div></div>`).join('')}
</div></section>
<section><h2>Observed mechanics</h2><table><thead><tr><th>Mechanic</th><th>Confidence</th><th>Evidence</th><th>Sources</th></tr></thead><tbody>${mechanicRows || '<tr><td colspan="4">None observed.</td></tr>'}</tbody></table></section>
<section><h2>Milestones</h2>${htmlList(report.milestones)}</section>
<section><h2>Completion routes</h2>${routeList(report.completionRoutes)}<h2>Hidden routes</h2>${routeList(report.hiddenRoutes)}</section>
<section><h2>Findings</h2><table><thead><tr><th>Signature</th><th>Severity</th><th>Kind</th><th>Evidence</th><th>Occurrences</th><th>Message</th></tr></thead><tbody>${findingRows || '<tr><td colspan="6">No executable findings observed.</td></tr>'}</tbody></table></section>
<section><h2>Limitations</h2>${htmlList(report.limitations)}</section>
</body></html>\n`;
}

export function renderProfessionalReportMarkdown(report: ProfessionalReportV1): string {
  const lines = [
    `# Playtestr report: ${safeMarkdown(report.target.id)}`,
    '',
    `Campaign **${safeMarkdown(report.campaign.id)}**, revision ${report.campaign.revision}.`,
    '',
    '## Summary',
    '',
    ...Object.entries(report.summary).map(([name, value]) => `- ${name}: ${value}`),
    '',
    '## Findings',
    '',
    ...(report.findings.length ? report.findings.map(finding => `- ${finding.severity}/${finding.kind} (${finding.evidenceLevel}, ${finding.occurrenceCount} occurrence(s)): ${safeMarkdown(finding.messages.join(' / '))}`) : ['No executable findings observed.']),
    '',
    '## Completion routes',
    '',
    ...(report.completionRoutes.length ? report.completionRoutes.map(route => `- ${actionText(route)}`) : ['None observed.']),
    '',
    '## Limitations',
    '',
    ...report.limitations.map(limitation => `- ${safeMarkdown(limitation)}`),
    '',
  ];
  return lines.join('\n');
}

export async function writeProfessionalReport(
  report: ProfessionalReportV1,
  artifactRoot: string,
  maxBytes = 10_000_000,
): Promise<ArtifactWriteResult> {
  const replays: Record<string, Replay> = Object.fromEntries(report.findings.map(finding => [finding.signature, finding.replay]));
  return writeArtifactBundle(artifactRoot, {
    'report.json': `${JSON.stringify(report, null, 2)}\n`,
    'report.html': renderProfessionalReportHtml(report),
    'summary.md': renderProfessionalReportMarkdown(report),
    'replays.json': `${JSON.stringify({ findings: replays, completionPrefixes: report.completionRoutes, hiddenPrefixes: report.hiddenRoutes }, null, 2)}\n`,
  }, maxBytes);
}
