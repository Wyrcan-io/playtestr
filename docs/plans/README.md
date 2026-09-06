# Release and post-MVP delivery plans

Status: planning only. These documents do not implement features, publish releases, or authorize outreach. Proposed commands and formats are design targets, not current CLI capabilities.

The original Sprints 0–4 delivered the MVP. The next four release/adoption milestones make that MVP accessible and test whether independent developers can use it. Sprints 5–10 are proposed development milestones; start each only after reviewing the evidence from the previous milestone. No calendar deadline or future platform claim follows from a sprint number.

## Release and adoption sequence

| Order | Plan | Observable outcome |
| --- | --- | --- |
| R1 | [Publish the first release candidate](release/01-release-candidate.md) | A developer can download a versioned, traceable prerelease. |
| R2 | [Verify installation from the published assets](release/02-installation-walkthrough.md) | A new user reaches a passing test using the downloaded binary and written instructions. |
| R3 | [Trial three to five independent projects](release/03-real-project-trials.md) | Maintainers use Playtestr for a real regression and provide actionable evidence. |
| R4 | [Publish stable v0.1.0](release/04-stable-release.md) | A bounded, documented release is backed by installation and adopter evidence. |

R1 includes internal extracted-archive checks before publication. R2 verifies the actual public download path afterward. R3 requires real participants; internal fixture runs cannot substitute for adoption. R4 can ship without waiting for Sprint 5 if its gates pass. A feature needed to unblock a trial is either a small release fix or a separately planned sprint, never an unrecorded expansion of release scope.

## Development sequence

| Sprint | Plan | Primary user value | Start gate |
| --- | --- | --- | --- |
| 5 | [Suites and CI results](sprints/05-suites-and-ci-results.md) | Run a growing test directory and find each failure. | Trial evidence of multi-spec or CI friction. |
| 6 | [Portable failure reproduction](sprints/06-failure-reproduction.md) | Reproduce a CI failure with the right local inputs and version checks. | Suite evidence layout is stable; a CI-to-local reproduction case exists. |
| 7 | [Local failure diagnosis](sprints/07-failure-diagnosis.md) | Understand the first failing step without decoding JSON by hand. | Reproduction metadata exists; two diagnosis tasks are recorded. |
| 8 | [CI adoption and installation](sprints/08-ci-adoption-and-installation.md) | Add a pinned runner to a real repository without custom download plumbing. | Stable assets exist; two adopters demonstrate setup friction. |
| 9 | [Repeatable test workspaces](sprints/09-repeatable-workspaces.md) | Test stateful setup flows without polluting or reusing the user's project state. | A real stateful CLI trial demonstrates contamination or setup difficulty. |
| 10 | [Terminal compatibility that users need](sprints/10-terminal-compatibility.md) | Correct one documented rendering/protocol gap affecting adopted apps. | Reproductions and a bounded compatibility corpus identify the chosen gap. |

Sprints 9 and 10 extend the earlier outline, which named only Sprints 5–8. The known Unicode layout limitation makes terminal compatibility a useful candidate for Sprint 10; real application evidence selects the actual scope. If it blocks adoption sooner, move it earlier with an explicit dependency review.

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
