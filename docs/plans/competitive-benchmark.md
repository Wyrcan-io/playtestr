# Bounded comparative evaluation

Status: completed on Linux amd64 for the admitted C1-C3 cells; see the
[dated measurement record](../validation/sprint-13-c-competitive-2026-09-22.md).
Owner: maintainer acting as benchmark operator. Independent preference remains
an A1 question. The [research survey](../research/competitive-user-survey-2026-09-19.md)
describes capabilities; this protocol tested selected workflows.

## Questions to answer

1. Can a new maintainer get a useful real-process test with less setup and less custom glue?
2. Does the test catch the intended defect, with a result that is accurate and easy to diagnose?
3. Can the flow be repeated and maintained without weakening assertions or hiding flakes?

Do not attempt to prove Playtestr is the best terminal automation platform. Compare the same job and name where alternatives are a better fit.

## Participants and scope

Begin with Playtestr, Atago, a pinned Microsoft tui-test beta matching its documentation, and Termlens. Record exact distribution/version/commit, host, runtime, dependency locks and retrieved documentation date. A Rust test library and a standalone runner have different integration costs; keep those costs visible instead of pretending they offer identical installation models.

Choose one native host actually supported by all admitted tools for the first comparison. Broaden only if setup succeeds and the task stays comparable. No inferred Windows support for a tool tested only on Linux. Framework TestBackend/Pilot tests are complementary references for fast in-process testing and do not enter real-PTY runtime rankings.

## Three matched tasks

| Task | Real user outcome | Seeded failure | Scope guard |
| --- | --- | --- | --- |
| C1 selection | Select a named second record and confirm exact result | Reviewed source defect selects first record | Same data, keys, initial geometry and intended output; no mouse requirement |
| C2 stateful setup | Correct invalid input and write exact config from fresh state | Reviewed source defect writes old value despite success text | Each tool may use idiomatic external state check; count its glue and verify oracle |
| C3 resize/redraw | Open modal, resize, dismiss and return to correct main state | Reviewed source defect leaves stale modal or hides required control | Same meaningful text readiness and result, not arbitrary fixed sleeps |

Use a small open deterministic target with source patches and a real third-party case from the corpus. Repository-owned targets simplify identical defect injection, but those alone cannot substantiate cross-project usability. Keep fixture/target provenance in the result. A snapshot-baseline edit tests mismatch mechanics and cannot stand in for the seeded target defect.

## Fair setup and experiment sequence

1. Record the task and expected outcomes before implementing tool-specific tests. Freeze the ground-truth patch and independent check.
2. Install each tool using its documented route; retain failures and prerequisites. Allow a bounded, recorded debugging session of up to one operator working day per tool for all three initial tasks. If still blocked, publish the exact blockage and pause that comparison rather than distort the task.
3. Implement idiomatic tests using project examples. Record corrections and assistance. Do not tune only Playtestr or handicap alternatives with sleeps where they support condition waits.
4. Run clean setup, known-good, known-bad and recovered once. Missing intended detection excludes timing comparison until diagnosed; it remains a visible correctness result.
5. Run 30 fresh process attempts per admitted tool/task/host cell with a fixed alternating/randomized execution order. Keep cold setup, warm execution and first launch separate. Disable automatic retries or record every initial attempt independently.
6. Run one matched hang, cancellation and output-flood fixture per tool/host with agreed budgets. Observe process identities and survivors; do not infer cleanup from process-list names alone.
7. Export exactly the evidence a maintainer normally receives. Time operator diagnosis with familiarity caveat; later A1 uses fresh tasks and alternating tool order.
8. Review every loss, unsupported case and changed test before drafting any comparison claim.

An initial Linux-only comparison of four tools and three tasks has 12 cells and 360 repeated executions if all are admitted. It is separate from the 3,000-run Playtestr release qualification; do not double-count it or automatically multiply across three hosts. Set actual setup/campaign cost after the first task.

## Measurement sheet

| Metric | Operational definition | Interpretation limit |
| --- | --- | --- |
| Installation effort | Commands, prerequisites, elapsed cold install, failure/repair attempts | Network and target runtime availability affect time |
| First useful test | Start authoring after prerequisites; stop only when correct target passes and seeded defect fails correctly | Operator familiarity bias; not independent onboarding proof |
| Maintenance surface | Tool-specific files, meaningful authored lines, helper scripts and dependency pins | Fewer lines are not automatically clearer or safer |
| Runtime | Launch-to-result duration, fresh process, same target/budgets | Separate target waits; in-process comparisons excluded |
| Detection | Correct pass, intended failure, wrong failure, false pass, unsupported | Counts and exact controls more useful than one composite score |
| Diagnosis | Correct explanation from normal report/logs, elapsed time and assistance | Matching failure signature is not proof of same root cause |
| Rerun effort | Commands, context reconstruction, manual edits, missing prerequisites | Do not silently copy private cached state for one tool |
| Resource cost | Peak process-tree memory/CPU with measurement method, output and evidence bytes | Platform instrumentation differs; only matched measurements compared |
| Cleanup | Managed processes gone within agreed budget after exit/cancel/hang/flood | Respect and disclose each tool's process/session contract |
| Repeat outcomes | All initial attempts by class, median and tail observation | 30 samples are exploratory; tail percentiles are imprecise |

Record raw values and support boundaries. Report detection rate only for the selected mutations, not general bug coverage. Treat timeout/bounded failure as failure outcomes, not conveniently fast performance results. For small samples show ranges and individual outliers alongside medians; avoid spurious decimal precision.

## Publication and decisions

Prepare a factual comparison page with procedure, runnable examples, exact pins, limitations and raw sanitized outcome ledger. No stars, market-share claims, synthetic ratings, selective cherry-picking or universal fastest/best badge. A missing feature can be the reason a tool is unsuitable for a task, but cannot be scored as a measured runtime defect.

If Playtestr is slower or more cumbersome, identify the smallest task-specific improvement within the feature budget, or recommend the other tool for that job. A disappointing benchmark alone does not justify a language rewrite. If results are inconclusive, say so and carry the question to A1 rather than adding features until a chart looks favorable.

Refreshing competitor versions after the freeze creates a separate comparison revision. Do not quietly use new alternative docs with old binaries. Publication itself remains a separate authorized action; this protocol prepares evidence and drafts.
