# Playtestr roadmap

Updated 19 September 2026. **This file is the authoritative status and execution order.** Detailed plans live in [docs/plans](docs/plans/README.md). Historical evidence remains in its original dated records. This is a planning audit of checkout `2a1fcfc` and repository records, not a new remote CI run or execution of the proposed test campaign.

Product goal: a developer installs one runner, writes a short terminal interaction, catches a meaningful regression, and understands the failure quickly. Protect correctness and simplicity while increasing real-project depth. Maintainer recruitment/adoption starts after the engineering batch and qualified release below.

## Read the status correctly

| Label | Meaning |
| --- | --- |
| Implemented | Behavior exists in source; says nothing by itself about other hosts or released binaries |
| Locally verified | Exact local checks are recorded; native evidence applies only to the named host |
| Natively verified | Exact OS/architecture path ran; a workflow configuration or cross-compile is insufficient |
| Published and verified | Versioned public assets were downloaded and checked; see their own evidence |
| Adopted | Independent maintainer ran/reviewed the flow, with later reuse recorded separately |
| Planned / conditional | Not implemented by this planning work; conditional work may be explicitly deferred |

Engineering completion, publication and adoption are separate dimensions. An unchecked human gate does not undo a completed release; a successful local test does not close a missing native/public-asset gate. No independent adoption is established in the reviewed records.

## Published runner releases

| Release | What it delivered | Recorded verification | Remaining limitations / use |
| --- | --- | --- | --- |
| [v0.1.0-rc.1](docs/releases/v0.1.0-rc.1.md) | First packaged MVP: spec/report v1, PTY actions, assertions, snapshots, bounded execution | Three native package paths and later downloaded-asset checks; source `1dde372` | Historical Linux `/dev/tty` defect; not a recommended basis for new full-screen coverage |
| [v0.1.0-rc.2](docs/releases/v0.1.0-rc.2.md) | Controlling-terminal fix, improved disappearance/redraw synchronization and failure capture | Three native package/public-install paths; source `583352a`; separate real-app evidence | Exact workflow exclusions remain in trial records |
| [v0.1.0](docs/releases/v0.1.0.md) | First stable MVP, published 12 September | Three native package/public-install paths; source `4ed8884`; nine-app refresh separately scoped | Latest stable in reviewed records; no directory-suite, HTML-report or workspace promise from this version |
| [v0.2.0-rc.1](docs/validation/sprint-5-engineering-2026-09-15.md) | Sprint 5 directory suites, preview, summaries and isolated evidence | Source `ea2e77f`; release run `35096743871`; public-install run `35120830130`; three native hosts | Prerelease, not stable v0.2.0; participant acceptance pending |
| [v0.3.0-rc.1](docs/releases/v0.3.0-rc.1.md) | Sprint 7 offline HTML reports plus prior suite work, published 18 September | Source `7cf64af`; release run `35288218202`; public-install run `35288555826`; three native hosts | Latest prerelease in reviewed records; does not contain later spec-v2 workspaces |

Exact hashes and run links belong to the cited records. Local tags corroborate identities but do not themselves prove publication. The annotated v0.1.0 tag object differs from its peeled source commit; use the source commit above for code provenance. No stable v0.2.0/v0.3.0 or released workspace version is claimed.

## All sprints: completed, existing and planned

| Sprint | Delivered behavior | Status and evidence | Still to do |
| --- | --- | --- | --- |
| 0 | Baseline, repository/language decisions, menu proof | Implemented; [delivery history](docs/sprints.md), [Go decision](docs/language-decision.md) | No restart or rewrite |
| 1 | Exact process outcomes, unexpected exit detection | Implemented; incorporated into MVP releases; [history](docs/sprints.md) | Maintain regression coverage |
| 2 | Budgets, cancellation, output caps, managed tree cleanup, explicit environment | Implemented; incorporated into MVP releases; [history](docs/sprints.md) | Preserve documented process-escape boundaries |
| 3 | Rendered text snapshots, diffs, transactional updates and terminal fixtures | Implemented; incorporated into MVP releases; [history](docs/sprints.md) | Selected cell-width/protocol limits remain |
| 4 | Formats, packaging, native matrix, Gum trial, licensing | Implemented and published; [platform evidence](docs/platform-support.md) | New releases must requalify their own bytes |
| 5 | Serial suites, deterministic listing and useful evidence layout | Implemented, natively/publicly verified in v0.2.0-rc.1; [record](docs/validation/sprint-5-engineering-2026-09-15.md) | Independent CI adoption in A1 |
| 6 | CI-to-local failure handoff | **Conditional, not implemented**; [plan](docs/plans/sprints/06-failure-reproduction.md) | First prove whether ordinary rerun instructions suffice |
| 7 | Offline failure diagnosis | Implemented, natively/publicly verified in v0.3.0-rc.1; [record](docs/validation/sprint-7-engineering-2026-09-18.md) | Independent diagnosis timing in A1 |
| 8 | Setup-only exact-version GitHub Action | Implemented, Windows local verification; [record](docs/validation/sprint-8-engineering-2026-09-18.md) | Native Linux/macOS action checks, verified immutable public action revision, real upgrade |
| 9 | Fresh bounded workspaces, spec/report v2, v2 HTML rendering | Implemented, Windows local verification; [record](docs/validation/sprint-9-engineering-2026-09-19.md) | Native Linux/macOS workspace checks and release-byte verification |
| 10 | One evidence-selected terminal compatibility improvement | **Planned, conditional on reduced case**; [plan](docs/plans/sprints/10-terminal-compatibility.md) | Select from corpus; no universal Unicode promise |
| 11 | Deep real-project validation corpus | **A0/A1 complete; B/C planned**; [checkpoint](corpus/README.md), [plan](docs/plans/sprints/11-real-project-corpus.md) | Five pilots, 120 admitted workflows, 300 risk cases, 15 defect controls and 3,000 frozen-byte repeats |
| 12 | Easier first-test authoring | **Planned**, optional extension separately gated; [plan](docs/plans/sprints/12-authoring-and-focused-assertions.md) | Three recipes, ten diagnostics, then one justified input or focused-assertion family |
| 13 | Native evidence, integrated hardening and fair comparison | **Planned**, starts with existing S8/S9 gaps; [plan](docs/plans/sprints/13-native-ci-and-release-hardening.md) | Early native triage, three-host verification, benchmark and freeze preparation |
| 14 | Reproducible demos and release kit | **Planned**; [plan](docs/plans/sprints/14-demos-and-release-kit.md) | Three real stories, accessible watch-to-run path, final frozen-byte captures and accurate release materials |

Sprint numbers are durable identifiers, not chronology: 7 shipped before 6, and 11 discovery precedes 10 selection. Do not rebuild implemented suites, HTML reports, the setup action or report-v2 rendering.

## Completed release and presentation milestones

| Milestone | What is complete | What is open |
| --- | --- | --- |
| [R1](docs/plans/release/01-release-candidate.md) | First native candidate packaging/publication | Historical defects remain documented, not erased |
| [R2](docs/plans/release/02-installation-walkthrough.md) | Automated public-asset installation checks | Independent unassisted walkthrough moves to A1 |
| [R3 technical campaign](docs/plans/release/03a-windows-linux-project-trials.md) | Lazygit/Lazydocker/K9s operator testing and discovered defects | Not maintainer adoption; host/release distinctions preserved |
| [R3b](docs/plans/release/03b-trial-findings-and-candidate-readiness.md) | Candidate repairs and rc.2 technical closure | Historical exclusions remain visible |
| [R3c](docs/plans/release/03c-cross-stack-validation.md) | Nine-app Python/Rust/Node campaign; 18 intended Windows/WSL cells, 54 frozen primary attempts | Not 54 distinct workflows, native macOS app coverage or nine adopters |
| [R4](docs/plans/release/04-stable-release.md) | v0.1.0 stable publication and technical verification | Human post-publication handoff now belongs to A1 |
| [R5](docs/plans/release/05-public-presentation.md) | Website/docs implementation and local browser/build checks; [validation](docs/validation/public-presentation-2026-09-12.md) | Full deployed-route/settings audit, native written walkthrough and manual screen-reader gaps in that record are not closed by a homepage smoke; carry to 14/R6 |
| [R3 independent trials](docs/plans/release/03-real-project-trials.md) | Protocol and templates only | Deferred to A1; no qualifying independent use claimed |

## Execute next, in this order

The table is a dependency chain. A completed checkpoint produces the stated evidence and then stops for review; work explicitly authorized across checkpoints can continue. Read the linked plan and [execution contract](docs/plans/execution-contract.md) before implementing. Research, tests and draft assets are allowed; pushes, public releases and outreach retain their explicit-action boundaries.

| Step | Checkpoint | Concrete action | Exit evidence / what it unlocks |
| --- | --- | --- | --- |
| 1 | **13-A0: existing native gaps — completed 2026-09-20** | Audited S8/S9, repaired the Unix installer diagnostic contract, and ran enforced focused checks on Windows amd64, Linux amd64 and macOS arm64 | [Current-source evidence table](docs/validation/sprint-13-a0-native-gaps-2026-09-20.md) and passing native/complete terminal runs |
| 2 | **11-A0: five pilot workflows** | Admit five small representative flows from the [catalog](docs/plans/corpus-catalog.md), one each for selection, state change, prompt validation, resize/redraw and fresh-workspace behavior | Real commands, independent expected results, first baseline outcomes and measured setup/run cost |
| 3 | **11-A1: corpus contract** | Freeze the 15-project candidate roster and 120 workflow intents; inventory existing focused tests; specify state checks before workspace deletion | Admission matrix, exact pins for admitted cases, 300-case coverage mapping, prioritized blockers; no requirement to implement all 120 before fixing a blocker |
| 4 | **10: one compatibility family** | Reduce the most serious terminal blocker and fix it behind the existing terminal boundary | Independent expected cells, failing-before/passing-after application case, unchanged lifecycle bounds; or documented deferral if no qualifying case |
| 5 | **12-A: authoring** | Complete three recipes and ten concrete diagnostic improvements/checks | Clean-environment pass/bug/recovery, useful prelaunch errors, measured operator friction |
| 6 | **12-B: optional extension** | Choose one input family OR focused text assertion only if two distinct admitted flows still require it | Minimum version/schema/migration plus negative controls; otherwise explicitly defer |
| 7 | **6: handoff decision** | Reproduce a corpus CI failure using ordinary spec/revision/fixture/report instructions | Recipe sufficient → close as deferred; demonstrably missing context → implement only the bounded manifest branch |
| 8 | **13-B/C: integrated hardening and comparison** | Finish native gaps after changes; verify current reports/action source; run bounded fair comparisons and adversarial checks | Three-host engineering evidence, comparison task results, no open correctness blockers |
| 9 | **11-B: application depth** | Complete 120 admitted workflows across 15 projects and the 300 focused-case map; prove 15 known-bad/recovered controls | Full outcomes, postconditions, host exclusions and unchanged reviewed baselines |
| 10 | **13-D + R6-F: candidate freeze** | Choose candidate version, freeze source/schema/fixtures, build once per host, package and hash executable/archive | Immutable candidate identities available before expensive qualification; not public publication |
| 11 | **11-C + R6-Q: frozen-byte qualification** | Run the full admitted matrix and 3,000 repeats using those candidate executable hashes | Complete attempt ledger, no unexplained false results/leaks, honest exclusions; execute once and reuse valid evidence by hash |
| 12 | **14: demos and release kit** | Capture three pass/defect/recovery stories and verify watch-to-run instructions using the frozen candidate | Reproducible assets, accessible presentation, accurate versions and draft announcements |
| 13 | **R6-P: publication** | Present the complete kit; after explicit publication instruction, publish immutable runner assets and appropriate action revision | Public URLs and tags tied to frozen artifacts; no replacement of existing assets |
| 14 | **R6-V: downloaded verification** | Download public bytes on each advertised host, compare hashes, execute representative pass/failure/recovery and the pinned action | Verified public release and supported install route; real old→new runner pin upgrade where applicable |
| 15 | **A1: independent adoption** | Now recruit five consenting maintainers, observe first use, participant CI and later reuse | Separate genuine user outcomes, timings, assistance and dropouts; no operator substitutes |
| 16 | **A2: commercial discovery** | After repeat use, evaluate paid support/onboarding; hosted history only with concrete paid-pilot demand | A decision backed by payment/value/cost evidence, or explicit no-build decision |

Unavailable native hosts do not prevent independent local recipe/design work. They remain hard blockers for the associated native/release claims and must be resolved before step 10 freezes the supported release boundary. No green status is inferred from waiting or configured CI.

## Release strategy from here

One coherent next feature release is planned; its number is selected at R6-F from the actual version/migration audit. Do not create a version for every sprint, rename already published tags, or assume prerelease publication means stable promotion. A necessary correctness hotfix to an existing release can interrupt the sequence with a narrow patch scope and its own qualification; optional features cannot.

The candidate is built before the long campaign. If source, embedded version, compiler/dependencies or build flags change, affected executable hashes and qualification are invalidated. A docs/archive-only change can retain executable evidence only if bytes match and packaging/install checks rerun. Stable promotion under a different embedded version requires a new build and the evidence policy in [R6](docs/plans/release/06-qualified-release.md); no label-based shortcut.

Sprint 14 may draft stories earlier, but final captures use the qualified behavior. Public demo URLs are checked after publication. The setup action and runner are independently pinned; lack of an unrelated future release does not hold the finite adoption batch open forever. See R6 for the genuine upgrade path versus a still-open longitudinal check.

## Quality and scope commitments

- Target 15 independently maintained applications, 120 distinct meaningful workflows, 300 distinct risk cases and 3,000 repeated process executions. These measures are separate and **planned, not completed**. The [validation program](docs/plans/validation-program.md) defines counts, budgets and qualification.
- Include Linux amd64, macOS arm64 and Windows amd64 evidence for claimed native paths. Application support is per version/workflow/host, not per language or framework logo.
- A passing screen is insufficient for a state-writing task. Validate exact Git/file/DB state at the right lifecycle point; preserve original fixtures and confirm cleanup.
- No new feature solely to match a competitor. The [feature budget](docs/plans/product-focus.md) allows one selected compatibility family and one conditional authoring/input/assertion family; failure-manifest work requires its own measured exception.
- No recording engine, AI auto-healing, SDK collection, service orchestration, cloud dashboard, automatic retries or parallel runner in this batch.
- Conditional deferral is a recorded scope decision, not “implemented.” False passes, destructive cleanup and unbounded execution cannot be deferred into claimed support.
- Stop adding pre-adoption sprints at Sprint 14/R6. Optional requests go into the [decision register](docs/plans/decision-register.md); real independent validation comes next.

## Immediate next implementation task

Sprint 11-A0/A1 is complete at its admission boundary; continue with **Sprint
10's compatibility-family decision**. Reduce an actual blocker from the five
pilots and implement one narrow family only if the entry evidence qualifies.
Otherwise record the evidence-backed deferral and proceed to Sprint 12-A. The
13-A0 [native-evidence table](docs/validation/sprint-13-a0-native-gaps-2026-09-20.md)
remains the current three-host source evidence. Do not run the 3,000-repeat
campaign until candidate bytes are frozen, and do not contact maintainers yet.

The [operational checklists](docs/plans/operational-checklists.md) provide current focused test commands, required skip detection, reader/version checks and concrete responses when execution hits a blocker.

Update this file at each checkpoint with exact evidence, remaining blockers and the next action. Keep historical notes intact. [Planning audit](docs/plans/planning-audit-2026-09-19.md) explains corrections made during this deeper review.
