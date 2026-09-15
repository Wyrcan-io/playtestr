# Release and post-MVP delivery plans

Status: R1, the automated R2 boundary, R3b, R3c, R4 stable publication, R5 public presentation, and Sprint 5 engineering are implemented. The last recorded remote website and terminal-test workflows passed at commit `0ec1e2d`; the current Sprint 5 working tree has local evidence only. Independent walkthrough and adoption gates remain open under R2/R3. These documents do not by themselves authorize outreach. Unimplemented commands and formats remain design targets, not current CLI capabilities.

The [September 2026 competitive assessment](../research/competitive-assessment-2026-09.md) was rechecked against the active alternatives' public documentation and repository metadata. Its conclusion stands: the released core is credible, but independent adoption, suite/CI ergonomics, authoring, interaction breadth, and terminal fidelity trail active alternatives. The [product-focus rule](product-focus.md) now governs the roadmap: become the simplest runner teams trust for deterministic CI regression, not a feature-parity terminal automation platform.

The original Sprints 0–4 delivered the MVP. The next four release/adoption milestones make that MVP accessible and test whether independent developers can use it. Sprints 5–10 are proposed development milestones; start each only after reviewing the evidence from the previous milestone. No calendar deadline or future platform claim follows from a sprint number.

## Release and adoption sequence

| Order | Plan | Observable outcome |
| --- | --- | --- |
| R1 | [Publish the first release candidate](release/01-release-candidate.md) | A developer can download a versioned, traceable prerelease. |
| R2 | [Verify installation from the published assets](release/02-installation-walkthrough.md) | A new user reaches a passing test using the downloaded binary and written instructions. |
| R3b | [Resolve findings and validate candidate bytes](release/03b-trial-findings-and-candidate-readiness.md) | Original Windows/Linux application evidence applies to the published candidate. |
| R3c | [Validate nine applications across three ecosystems](release/03c-cross-stack-validation.md) | Three Python, three Rust, and three Node.js applications pass bounded useful workflows. |
| R4 | [Publish stable v0.1.0](release/04-stable-release.md) | A documented stable release is backed by technical and installation evidence. |
| R3, after R4 publication | [Trial three to five independent projects](release/03-real-project-trials.md) | Maintainers review failures, voluntarily reuse tests, and integrate the stable binary into their CI. |
| R5 | [Prepare the public website and documentation](release/05-public-presentation.md) | A newcomer can understand, download, try, diagnose, and find support through a complete evidence-based website. |

Sequence revised 11 September 2026: R1 → R2 → R3b technical closure → R3c nine-application validation → R4 stable publication → R3 independent adoption → evidence-based Sprint 5 selection. Existing plan identifiers are retained for links. R3 adoption no longer blocks initial stable publication and remains incomplete until observed. R4's post-publication handoff closes after the first participant stable run; full adoption remains owned by R3. Technical correctness and installation blockers still block publication. A feature needed to unblock a trial is either a small release fix or a separately planned sprint, never an unrecorded expansion of release scope.

## Completed engineering milestone

| Sprint | Plan | Primary user value | Start gate |
| --- | --- | --- | --- |
| 5 | [Run a small CI suite](sprints/05-suites-and-ci-results.md) | Run an intended test directory serially and find each failed screen safely. | Implemented locally; independent adopter acceptance remains open. |

Sprint 5 stopped at its acceptance boundary. Engineering completion is recorded separately from independent adoption; operator tests do not close adoption gates. Recruitment can continue while the next candidate is evaluated.

The recommended next candidate is the compact failure report in Sprint 7. Keep the existing identifiers for links. Sprint 7 can render existing evidence without Sprint 6. Reproduction follows only if context remains costly to reconstruct. Installation, workspaces, and terminal correctness can move earlier when they block a chosen real flow.

## Conditional follow-ons, not a feature checklist

| Candidate | User value | Required evidence before implementation |
| --- | --- | --- |
| [Failure handoff](sprints/06-failure-reproduction.md) | Clarify the local inputs and identity of one CI failure. | A Sprint 5 CI failure cannot be reproduced locally because required context is unclear. |
| [Readable failure report](sprints/07-failure-diagnosis.md) | Show the failing step, captured screen, diff, and cleanup in one attractive offline view. | Two concrete diagnosis cases and stable artifact paths; independent reviewer results stay separately recorded. |
| [Easier installation](sprints/08-ci-adoption-and-installation.md) | Install an exact runner release through one convenient route. | Repeated installation friction or one blocked willing participant selects an action or one package channel. |
| [Repeatable workspaces](sprints/09-repeatable-workspaces.md) | Make one stateful target flow start from reviewed state. | A real adopted flow is contaminated by prior state and cannot use a simpler documented reset. |
| [Terminal compatibility](sprints/10-terminal-compatibility.md) | Fix one rendering or protocol gap that blocks an adopted test. | A reduced native reproduction identifies one behavior family and independent expected result. |

Keep the installer as its own bounded milestone so suite execution can ship and be evaluated independently. Use the verified archive instructions initially; move installation work forward if those instructions cause abandonment. Convenience is valuable, but maintaining several routes requires evidence and an owner.

Authoring friction is measured in the same trials. If editing the small spec is the main obstacle, select a separate template or validation slice before introducing a recorder, scripting language, or SDK.

## Delivery discipline

- Each sprint plan includes entry evidence, design decisions, checkpoints, acceptance cases, manual demonstrations, risk controls, and an exit record.
- Treat checkpoints as small reviewable changes. Demonstrate and validate each before proceeding; do not write the whole sprint and only then test it.
- A checkpoint is complete when its behavior is evidenced, not when files exist. Stop at the sprint boundary for user testing unless continuation is explicitly requested.
- Use Go for product code. Keep PTY, runner, spec, evidence, and CLI responsibilities separate. Do not extract all packages merely to resemble a future architecture.
- Preserve version 1 inputs and reports. Both published schemas are strict. Adding fields or action meanings needs an explicit compatibility decision, schemas, fixtures, migration notes, and a minimum runner version; it cannot be called harmless because a Go struct accepts it.
- No telemetry by default. Measure onboarding and debugging with opt-in trial notes and local timings. Report sample counts and limitations.
- Every feature that launches a process must retain timeout, cancellation, output-limit, and tree-cleanup guarantees. Evidence inspection alone never launches a target.
- Tests of platform behavior run on the exact advertised OS and architecture. Cross-compilation, successful upload, and a workflow's name are insufficient runtime proof.
- Documentation-only planning does not require rerunning PTY tests. Later implementation must use the checks relevant to each change and observe remote CI after an authorized push.

## How priorities change

At every boundary, review three records: the most frequent user obstacle, the most serious correctness issue, and the actual cost of completing the next proposed slice. Reorder when a concrete blocker has higher value, and record why. If a sprint has no qualifying user case, pause that sprint and improve the existing release using observed feedback.

Release correctness, data loss, leaked sensitive evidence, false passes, and unbounded processes take priority over convenience features. Within convenience work, prefer a task that two independent users struggle with over a broad feature requested hypothetically.

## Deliberately deferred

| Idea | Evidence required before a separate plan |
| --- | --- |
| Parallel execution | Measured suites remain too slow after profiling; workspaces and external resources can be separated safely. |
| Automatic failure minimization | Reproduction is stable and a precise failure identity exists; users regularly spend time shrinking long specs. |
| GIF/video recording | Frame-based diagnostics fail a real debugging task that timed playback would resolve. |
| Styled visual snapshots | Users need to detect styles independently of the existing text contract and accept reviewed visual baselines. |
| More package managers | Measured demand for the next channel and a maintainer able to keep versions synchronized. |
| Broad framework matrix | A named application/version/workflow justifies each additional runtime and fixture. |
| Cloud accounts, PR bots, hosted reports | Sustained local usage and a concrete collaborative need; no prerequisite for any sprint here. |
| Autonomous game exploration | Remains a Gametestr concern, outside these plans. |

## Evidence and estimates

Use dated evidence files for execution results, separate from these plans. Record commit, binary version, target version, host, command, expected outcome, actual result, and relevant artifacts. Published artifacts must map to the commit that produced their exact bytes.

Estimate a sprint after its first contract checkpoint. If it no longer fits a small demonstrable milestone, split it at the last useful behavior rather than dropping failure tests. The later plans are detailed to expose dependencies and choices, not to commit to implementing every future idea in the next two or three months.
