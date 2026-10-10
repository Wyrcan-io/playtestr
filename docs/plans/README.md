# Playtestr prelaunch planning set

Created 6 October 2026. Originally **plans only**; the user subsequently invoked the P0-P2 execution prompt. P0-P2 now satisfy scoped acceptance in [the dated record](../validation/p0-p2-2026-10-07.md). Later milestones remain plans. The [root roadmap](../../roadmap.md) defines authoritative order and acceptance. Status is supported by the dated execution evidence; planning prose alone is not product completion.

| Document | Owns |
| --- | --- |
| [00 — baseline and decisions](00-baseline-and-decisions.md) | Existing assets, changed direction, limits and unknowns |
| [01 — product and positioning](01-product-and-positioning.md) | Audience, promise, free/paid scope and exclusions |
| [02 — customer journeys](02-customer-journeys.md) | Local, PR, installation, review, subscription and removal flows |
| [03 — deterministic authoring](03-deterministic-authoring.md) | Recorder, checkpoints, readiness, fixtures and formats |
| [04 — GitHub execution and review](04-github-execution-and-review.md) | Actions, provenance, review policy, forks and checks |
| [05 — managed infrastructure](05-managed-infrastructure.md) | Serverless topology, quotas, recovery and capacity |
| [06 — commercial model](06-commercial-model.md) | Pricing, first-sale route, Marketplace, billing and costs |
| [07 — security and data](07-security-and-data.md) | Trust, permissions, tenants, retention and abuse |
| [08 — real-project validation](08-real-project-validation.md) | 100-project admission, controls, holdouts and budget |
| [09 — delivery milestones](09-delivery-milestones.md) | Slices, dependencies, exits, estimates and stop rules |
| [10 — quality and release](10-quality-and-release.md) | Native checks, reliability, final bytes and rollback |
| [11 — launch and operations](11-launch-and-operations.md) | Launch packet, marketing hold and self-service operation |
| [12 — risks and decisions](12-risks-and-decisions.md) | Owners, deadlines, defaults and expansion triggers |
| [13 — source register](13-source-register.md) | Dated provider facts and recheck obligations |
| [14 — execution templates](14-execution-templates.md) | Future slice, project, batch, billing and release records |
| [15 — candidate discovery](15-candidate-discovery.md) | Screening lanes and leads; no compatibility claims |

## Implementation prompt

[Execute P0–P2 fully](p0-p2-full-implementation-prompt.md) was invoked for this completed implementation session and remains the reusable scope/acceptance reference. It references the controlling plans, includes full acceptance gates and bounded internal GitHub validation actions, and directs continuous execution across all three phases. Creating or reading that file does not invoke it; the user must explicitly send/invoke it as the task.

## Authority and maintenance

[Ten-project user validation and general improvements](ten-project-user-validation-prompt.md) was explicitly invoked and is now completed within its early P5 reliability scope. [Results and limitations](../validation/ten-project-user-pass/README.md) record all ten user journeys, general fixes, final qualification and cleanup. The prompt remains reusable; reading it does not start another pass or the complete-product 100-project campaign.

Scope belongs in 01; user behavior in 02; recording in 03; PR trust in 04; quotas in 05; pricing/billing in 06; retention in 07; campaign counting in 08; sequence in the roadmap/09; quality in 10; launch/operations in 11; open decisions in 12. Resolve contradictions before implementation. Numerical thresholds are proposed gates unless explicitly attributed to evidence or a provider source.

The former `docs/plans` and `docs/adoption` trees have been removed from their active locations and retained in [the historical archive](../archive/prelaunch-2026-10-06/README.md), with the old roadmap and sprint record. The user's existing planning-index edits and two untracked prompts are preserved there. Existing `AGENTS.md` edits are untouched.

Two old filenames contain archive pointers only: `corpus-catalog.md` and `wide-character-next-steps-prompt.md`. Frozen machine-readable evidence references those paths, so the pointers preserve provenance without retaining executable old plans or modifying evidence JSON.

Release notes, validation results, research, trials, source and public contracts remain evidence of original work. Relocated links do not change recorded outcomes. [Sprint history](../sprints.md) is an archive entry point, not another roadmap.

The original replacement-plans change authorized documentation only. The later invoked batch separately authorized P0-P2 implementation, scoped commits/pushes and exactly two internal PR journeys; it did not authorize spending, production deployment, releases or outreach. Older deferrals of recording/billing/App work no longer veto the new planned scope. Technical and evidence safeguards still apply.

## Planning review

The planning pass checked local Markdown link targets, whitespace/diffs, numerical consistency, stage dependencies and the boundary between proposed and shipped behavior. The 47 archived documents comparable with the committed baseline retain their prose apart from archive notices and relocated link destinations; the previously edited index and two untracked prompts were preserved separately in the same archive. Runtime tests were not rerun for this documentation-only change. Prices, provider eligibility, final compatibility and independent adoption remain explicitly unproven where noted.
