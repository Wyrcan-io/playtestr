# Planning guide

The root **[roadmap.md](../../roadmap.md)** is the single source of truth for completed releases/sprints, open verification gates, and step-by-step execution order. Do not maintain a competing sequence here. Updated 19 September 2026 after the deeper planning audit.

## Read before implementation

| Document | Owns |
| --- | --- |
| [Root roadmap](../../roadmap.md) | Current milestone/release status, dependency order, next action and pre-adoption finish line |
| [Product focus](product-focus.md) | Target developer job, differentiation hypothesis, feature budget and outcome targets |
| [Execution contract](execution-contract.md) | Checkpoint entry/exit, evidence, severity, test obligations and invalidation rules |
| [Operational checklists](operational-checklists.md) | First native commands, skipped-test gates, reader compatibility and failure scenarios |
| [Decision register](decision-register.md) | Chosen tradeoffs, unresolved decisions, backlog admission and risks |
| [Competitive/user survey](../research/competitive-user-survey-2026-09-19.md) | Public-source findings, confidence and market/usage unknowns |
| [Benchmark protocol](competitive-benchmark.md) | Matched tasks, exact metrics, fair comparisons and claim boundaries |
| [Validation program](validation-program.md) | Case/run counting, native scope, campaign budgets, state checks and qualification |
| [120-workflow catalog](corpus-catalog.md) | Concrete proposed tasks and expected results; not executed support claims |
| [Planning audit](planning-audit-2026-09-19.md) | Multiple review passes, corrected flaws and remaining uncertainties |

## Remaining engineering plans

- [Sprint 10](sprints/10-terminal-compatibility.md): one compatibility family selected from reduced real-project evidence.
- [Sprint 11](sprints/11-real-project-corpus.md): five pilots, admission, deep application cases and frozen-byte repetition.
- [Sprint 12](sprints/12-authoring-and-focused-assertions.md): complete recipes and diagnostics; one conditional input or focused-assertion extension.
- [Sprint 6](sprints/06-failure-reproduction.md): ordinary handoff instructions first; manifest only if demonstrated necessary.
- [Sprint 13](sprints/13-native-ci-and-release-hardening.md): early existing native gaps, integrated hardening, fair comparison and freeze preparation.
- [Sprint 14](sprints/14-demos-and-release-kit.md): three reproducible stories, accessible watch-to-run path and release kit.
- [R6](release/06-qualified-release.md): freeze, qualify, publish when instructed, verify public bytes.
- [A1/A2](release/07-maintainer-adoption.md): independent adoption after engineering/R6, commercial discovery only after repeat use.

Identifiers are retained for existing links; they are not a numeric execution order. Root roadmap resolves phases such as 13-A0 before 11 discovery and R6-F before 11-C repetitions. Conditional branches can close with a justified deferral, but essential correctness failures cannot.

## Existing implementation and historical plans

[Original sprint record](../sprints.md) preserves Sprints 0–9 engineering history. Sprint [5](sprints/05-suites-and-ci-results.md) and [7](sprints/07-failure-diagnosis.md) are published prerelease capabilities. Sprint [8](sprints/08-ci-adoption-and-installation.md) and [9](sprints/09-repeatable-workspaces.md) are locally implemented with remaining native/publication evidence. Do not rebuild them.

Historical release plans: [R1](release/01-release-candidate.md), [R2](release/02-installation-walkthrough.md), [R3 technical](release/03a-windows-linux-project-trials.md), [R3b](release/03b-trial-findings-and-candidate-readiness.md), [R3c](release/03c-cross-stack-validation.md), [R4](release/04-stable-release.md), [R5](release/05-public-presentation.md). [R3 participant protocol](release/03-real-project-trials.md) is supporting material for A1, not active recruitment.

## Maintenance rule

A status claim belongs in root roadmap with its evidence link. Exact run output belongs in a dated record. Public behavior belongs in its versioned contract. Research conclusions belong in the dated survey. Avoid duplicating mutable facts across these layers. At every milestone review links, minimum runner versions and next-step wording together.

No push, publication, outreach or service spend is implied by a planning document. Prepare reviewable artifacts within the authorized task. Go remains the core language; real PTYs prove process/terminal behavior. Documentation-only edits use consistency/link/diff checks rather than a claimed new runtime test result.
