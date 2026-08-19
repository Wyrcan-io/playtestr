import { describe, expect, it } from 'vitest';
import { createCampaign } from './campaign.js';
import { createProfessionalReport, renderProfessionalReportHtml, renderProfessionalReportMarkdown } from './professional-report.js';
import type { TargetManifest } from './types.js';

const manifest: TargetManifest = { schemaVersion: 1, id: '<script>alert(1)</script>', command: 'node' };

describe('professional report', () => {
  it('renders canonical evidence as escaped, script-free standalone HTML', () => {
    const campaign = createCampaign(manifest, 'safe-report');
    const report = createProfessionalReport(manifest, campaign);
    const html = renderProfessionalReportHtml(report);
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(html).not.toContain('<script>');
    expect(html).toContain("default-src 'none'");
    const markdown = renderProfessionalReportMarkdown(report);
    expect(markdown).toContain('Observed state and mechanic evidence');
    expect(markdown).not.toContain('<script>');
  });
});
