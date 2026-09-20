# Execution contract for the remaining batch

Status: planning rules, 19 September 2026. [Root roadmap](../../roadmap.md) owns sequence and milestone status. This document defines how to begin, verify and close a checkpoint without inventing certainty or growing the product accidentally.

## Before starting a checkpoint

Record its ID, one user-visible result, current baseline, exact acceptance cases, touched public contracts, owner/reviewer, required native hosts, prerequisites and exclusions. Link the triggering real task or documented hypothesis. Estimate implementation, verification and ongoing maintenance separately after the pilot; avoid precision unsupported by measurements.

Record dependency states explicitly: available, implemented-but-unverified, externally blocked, or unnecessary. A host that cannot run is an evidence gap. A failed test is a result. Neither becomes a pass because an agent completed its turn.

Limit implementation to one reviewable behavior per change. Preserve unrelated user changes. Do not invent release commits, artifact URLs or dates to fill a template. Proposed commands remain visibly proposed until implemented and tested.

## Evidence record template

Use a dated Markdown record with bounded machine-readable attempt data when repetition needs it. Reuse existing trial/report structures; do not create a new public product schema simply to manage this campaign.

| Field | Required content |
| --- | --- |
| Identity | Checkpoint/case/attempt ID, UTC start/end, operator and review status |
| Provenance | Source commit, dirty status or patch hash, executable SHA-256, embedded version, build toolchain/flags; archive hash if applicable |
| Target | Exact project/version/commit/package hash, target runtime and license source |
| Environment | OS/version/architecture, CI image identity, locale/terminal dimensions, setup recipe; no secret environment values |
| Inputs | Spec, fixture, baseline and oracle revisions/hashes; known-good/bad patch identity |
| Expectation | User task, expected runner status/category/step, independent postcondition and expected cleanup |
| Observation | Actual statuses, timings, resolved artifact references, postcondition result, cleanup result, actual skip/block reason |
| Disposition | Pass, detected intended defect, unexpected failure, false pass, blocked, skipped, or not applicable; issue/review reference |
| Reproduction | Exact safe commands and prerequisites, known limits, whether external resources are required |

Do not put command arguments, private file contents or terminal secrets into a public ledger. Commands in public recipes use synthetic inputs. Hash public fixtures and known binaries; do not persist hashes of secrets as supposed anonymization. Retained target state is local by default and never auto-uploaded.

## Status rules and gate ownership

Engineering owner prepares evidence. The repository maintainer reviews the contract/scope and release boundary; the same person may perform both roles, but that is operator review, not independent user validation. A1 owns outside usability/adoption. Agents can produce work but cannot manufacture independent participants.

- Completed: all required cases and outputs are evidenced for the declared boundary.
- Deferred: optional branch rejected with reason, workaround, revisit trigger and remaining limitation.
- Blocked: mandatory case lacks prerequisite or has unresolved failure; name a concrete next action.
- Excluded: an application/host/workflow is outside the declared support set, visible in the denominator and support table. An exclusion cannot erase a regression in previously supported behavior.

Close conditional branches with an explicit decision rather than a fake implementation checkbox. Stop at the checkpoint's acceptance boundary unless continuation was authorized. Optional ideas discovered while fixing a bug go to the decision register.

## Failure severity and release consequences

| Severity | Example | Required response |
| --- | --- | --- |
| Blocker | False pass, lost/corrupted baseline, deleting outside owned state, unbounded hang/output, managed tree left running, unsafe evidence-path escape | Stop qualification for affected behavior, reduce case, fix and rerun relevant native gates; no feature-budget exemption from correctness |
| High | Wrong screen for a claimed flow, supported archive/action unusable, report cannot show captured failure, erroneous exit category | Fix before claiming that release path; retain failed evidence and support limitations |
| Medium | Confusing diagnostic, cumbersome setup, excessive runner overhead with correct result | Repair in selected authoring/hardening slice if it serves admitted task; otherwise explicit backlog |
| Low/optional | Additional theme, format, package channel, unrelated protocol, requested convenience | Defer with trigger; cannot extend the pre-adoption batch by default |

A target defect is not automatically a Playtestr defect. A correctly detected seeded defect passes the harness's expectation while the Playtestr test still exits nonzero. Preserve both outcomes; never relabel a failed product test as passed in its original report.

## Verification appropriate to the change

| Change | Minimum checks |
| --- | --- |
| Planning/docs only | Local links/anchors, status/source consistency, no future-as-shipped commands, diff whitespace |
| Parsing/spec/schema | Table-driven valid/invalid/boundary cases, no-launch sentinel, schema parity, old-format regression, CLI diagnostic |
| PTY/input/VT/lifecycle | Real PTY/native target, correct screen/input, exit/hang/flood/cancel/cleanup, race detector for concurrency/lifecycle changes, manual example |
| Workspaces/filesystem | Independent state invariant, no-follow/link cases per host capability, partial failure, ownership marker, retained-state and cleanup errors |
| Reports | v1/v2 documents, hostile/missing/large evidence, bounds and atomic preservation, actual browser/offline checks for rendered output |
| Installer/release | Source action and immutable public action separately, exact archive/executable, checksum/layout/version/path precedence, corrupt/interrupted cases, extracted binary and downloaded-byte smoke |

Run repository commands with an explicit recorded exit code. Do not rerun the entire expensive campaign after every documentation edit; use the invalidation rules below. Do not weaken product deadlines for instrumented tests.

Record required test-level pass/fail/skip events as well as command status. Exit zero does not prove that required tests executed. Missing prerequisites, filtered-out tests and platform skips remain gaps until resolved or explicitly reviewed as inapplicable. The [operational checklists](operational-checklists.md) cover current installer skips and concrete first commands.

## Evidence invalidation and reuse

| Change since passing evidence | Required rerun |
| --- | --- |
| Runner code, dependency, compiler, embedded version or build flags | New executable identity; native source gates and final frozen-byte qualification for affected advertised hosts |
| Target binary/runtime/fixture/spec/oracle | Affected workflow-host cells and their controls/repeats; changed baseline requires independent review |
| Terminal contract or snapshot normalization | Every affected application/terminal corpus cell plus representative unchanged families; explicit migration |
| Packaging only, identical executable SHA-256 | Package-layout/extraction/public-download/installation gates; byte-identical executable campaign may be cited |
| Installer implementation | Installer source/native failure paths and public pinned-action checks; unchanged runner behavior evidence may be cited |
| Pure documentation/demo edit | Links, command/version parity and relevant presentation checks; rerun any changed executable walkthrough |

Qualification results are keyed to immutable identities, not “latest” or a branch name. A new version string produces different bytes; do not claim prerelease tests directly prove a rebuilt stable executable. R6 defines the final version choice before the long campaign.

## Handling unavailable resources

Continue independent docs, fixture design and available-host checks. Record missing compiler/runtime/native host, exact command to run later, and who owns obtaining evidence. A WSL session is Linux evidence with that environment label, not macOS or native Windows evidence. Do not replace native verification with mocks, cross-compilation or a configured workflow.

Publishing/pushing/outreach follow repository authorization rules. Prepare concrete reviewable artifacts first. A pending external action is pending; elapsed time is neither permission nor a successful release. No new service spend is assumed by test budgets.

## Closing record

Summarize what changed, why, exact validated boundary, unresolved risks/exclusions, required docs/schema updates, cost measured, and the next checkpoint. Update the root roadmap and link evidence; never rewrite failed historical attempts away. A planning document can be internally consistent and rigorous, but only execution and later users validate its assumptions.
