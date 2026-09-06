# R3 — Trial Playtestr in three to five real projects

Status: planned. Depends on R2's usable installation path. Product outcome: independent maintainers use Playtestr to protect actual terminal interactions and tell us where it helps or breaks down.

## What counts as a useful trial

A qualifying project has an existing CLI/TUI, a named maintainer, a specific regression-prone interaction, and a reason to run the test again. A maintainer writes or reviews a small spec, runs it against their application, and evaluates the evidence from an intentional or known regression.

Internal demos, stars, download counts, and one-off framework hello-worlds do not count as independent adoption. The existing Gum test provides a technical starting point, but it does not represent three independent users.

## Cohort and scope

Recruit three to five consenting projects, with at least two different implementation stacks and a mixture of interaction styles. Candidate workflow types are: a setup wizard that writes configuration; an interactive selector; and a full-screen application with redraw or resize behavior. Framework names such as Bubble Tea, Ink, or Textual are recruitment candidates, not compatibility claims.

Select one useful flow per project initially. Prefer offline/repeatable tasks using synthetic data. Avoid payment flows, production credentials, network-dependent output, and long setup chains for this first cohort. Test on the host the maintainer actually uses; extend platform claims only after exact native runs.

## Checkpoint 1 — Prepare a trial kit

Deliver a short kit with the candidate download, binary-only installation instructions, a small spec example, how to review/update one snapshot, how to save a report, and a problem-report template. Explain trusted-target execution and the possibility of terminal output containing application secrets without burdening the user with implementation detail.

Provide a minimal baseline of how the project currently tests the selected flow: manual steps, existing automation, or no coverage. Ask what specific regression the maintainer wants to catch. This establishes value before proposing features.

Acceptance: a maintainer can attempt the chosen task without reading the runner source. Outreach text is drafted; messages are sent only with authorization to contact those recipients.

## Checkpoint 2 — Select and record each project

For each project record: application commit/version, framework/runtime if relevant, host, selected workflow, setup steps, expected result, initial manual verification, data constraints, and maintainer participation. Pin test inputs and application version for reproducibility while preserving a separate run against the project's current development version.

Agree on what feedback may be published. Private application details and participant names remain private unless permission is provided. Use sanitized reproductions when a bug can be represented without private source.

Acceptance: three qualifying projects are identified with a real flow and a named participant. Do not pre-fill successful adoption metrics before the work happens.

## Checkpoint 3 — Build one regression test together

1. Run the intended flow manually once to establish the expected behavior.
2. Write visible readiness assertions after meaningful input or resize; do not use arbitrary delays as the primary readiness proof.
3. Review the initial snapshot and expected exit policy with the maintainer.
4. Run the spec repeatedly from the same documented starting state.
5. Introduce a small known regression or use a known-bad application revision; confirm the test catches the intended difference.
6. Return to the known-good revision and verify recovery.

Classify problems at the right layer: application nondeterminism, unsupported terminal behavior, spec authoring mistake, runner defect, environment/setup issue, or unclear documentation. Do not make all green results by widening deadlines or updating the baseline blindly.

Acceptance: each trial has a passing good case and a failing bad case whose evidence the maintainer can explain.

## Checkpoint 4 — Test repeated use and CI fit

Have the maintainer run the test on a second working session or later application change. Where practical, run it in the project's CI with read-only repository access and bounded artifact retention. Keep the trial narrow: CI installation can use the documented archive path until Sprint 8 provides a reusable action.

Collect a modest fixed sample, such as ten consecutive local runs of the pinned flow, to expose timing or state issues. Report the denominator, application version, and host; ten passes do not establish statistical reliability across other systems. Preserve any failures rather than adding retries that conceal them.

Acceptance: at least two maintainers voluntarily repeat use after the initial setup. A participant declining continued use is feedback, not a successful retention result.

## Checkpoint 5 — Turn observations into a bounded backlog

For each obstacle, record the user task, reproduction, impact, frequency in the cohort, workaround, evidence, and smallest useful intervention. Use the following policy:

| Priority | Examples | Response |
| --- | --- | --- |
| Release blocker | False pass, surviving process, data loss, unintended sensitive-data persistence, broken installation | Stop promotion; fix and verify in a new candidate if needed. |
| Adoption blocker | Cannot test the agreed flow without extensive custom setup or unsupported rendering | Decide whether a narrow fix fits the candidate or requires a sprint. |
| Repeated friction | Listing specs manually, finding artifacts, reproducing CI context | Feed Sprints 5–8 with actual task examples. |
| Stateful test problem | Config/files from the previous run affect later results | Feed Sprint 9 with a concrete workspace design case. |
| Rendering correctness gap | Wide text, redraw, or terminal query breaks the selected application | Feed Sprint 10 or move that work earlier if it blocks adoption. |
| Speculative request | Broad dashboard or many SDKs without a demonstrated task | Preserve as an idea; do not schedule automatically. |

## Success measures and stop conditions

Target three completed qualifying trials, with two showing repeated use and at least one testing CI integration. Aim for maintainers to author/review their own small spec and identify an intentional failure without a call with the Playtestr author. Record actual time and assistance instead of claiming a target was met without evidence.

If fewer than three projects participate, keep R3 open and reassess recruitment or product fit. If participants repeatedly cannot identify a valuable interaction to test, pause feature expansion and refine the intended user/workflow. Do not replace adoption evidence with additional internal demos.

## Definition of done

- [ ] Three to five project records; at least three complete end-to-end trials.
- [ ] Good/bad application behavior is distinguished in each completed trial.
- [ ] Repeat-use and CI observations recorded, including failures and assistance.
- [ ] Release blockers fixed or stable promotion explicitly held.
- [ ] Ranked backlog has evidence and a small proposed remedy for each accepted item.
- [ ] Permission exists for any names, quotes, or examples intended for public release notes.

Handoff: R4 receives candidate-specific blocker status and adopter evidence. Each later sprint receives actual user stories, not a list of technologies to claim support for.
