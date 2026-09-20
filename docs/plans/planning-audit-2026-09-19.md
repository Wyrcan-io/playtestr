# Planning audit and verification passes

Audit date: 19 September 2026. Baseline checkout: `2a1fcfc`, with the previous planning edits preserved. Scope: roadmap, remaining sprint/release plans, code-to-plan facts, evidence provenance, practical test execution and document consistency. This record does not assert that proposed implementation, native jobs or benchmarks ran.

## Pass 1: implementation and release facts

Read README, CHANGELOG, support/release contracts, local tags and recent history, all four Sprint 5/7/8/9 engineering records, existing release records, platform evidence, current report version handling/tests, workflow/action definitions and trial harness entry points.

| Finding | Correction |
| --- | --- |
| Prior roadmap described Sprint 5 mostly as local engineering | Record its v0.2.0-rc.1 publication, three-host verification and exact evidence source |
| v0.2.0-rc.1 was missing from the main release sequence | Include all five recorded runner releases; do not invent stable v0.2/v0.3 |
| Report-v2 HTML was presented as a possible missing implementation | `internal/report/html.go` accepts v1/v2; `TestRenderHTMLReportV2WorkspaceOutcome` and S9 record establish existing local implementation; remaining work is native/frozen-byte verification |
| S8/S9 native/action gaps came late in the plan | Add early 13-A0 evidence closure before feature expansion |
| Published tag object could be confused with source identity | Resolve annotated v0.1.0 to `4ed8884`; source provenance uses peeled commit |
| Existing documentation could be read as current recruiting instruction | Root sequence explicitly defers A1; dated historical records remain labeled historical |
| Strict schemas and optional patch-addition language need a precise reader policy | Q09 requires an explicit old/new reader/document compatibility decision before R6-F; planning does not silently change SUPPORT.md |
| R5's local presentation record still lists external/manual checks | Root status now preserves those open items; Sprint 14/R6 close them rather than treating a homepage smoke as full verification |

Evidence confidence: repository records plus local source/tag inspection. Remote run URLs are cited from records, not freshly rerun or independently re-audited in this planning task.

## Pass 2: dependency and execution feasibility

Trace the plan from first task through adoption, including failure branches, unavailable hosts, artifact ownership and byte identity.

| Finding | Correction |
| --- | --- |
| Full 120-case implementation was effectively required before blocker repair | Split five pilots, thin 120-intent inventory and later depth; first fix follows concrete pilot evidence |
| Expensive repeat campaign preceded definitive candidate freeze | Add R6-F before 11-C/R6-Q; results bind to actual executable hash and embedded version |
| Naive post-run checks cannot inspect deleted successful workspaces | Define external-resource, proven pre-exit adapter and harness-owned cwd options; no new retain-success product feature |
| Installer “later release” could defer the finish line indefinitely | Try same published action with existing v0.3.0-rc.1 and new R6 release; keep genuinely future checks separate if unavailable |
| Old Sprint 6 checkpoints still required an adopter during engineering | Engineering uses operator-owned real-project failure; A1 separately validates independent use |
| Fixed test counts risk shallow padding or runaway CI cost | Stable workflow IDs, distinct risk mapping, pilot cost formula, explicit retention/job caps and qualification ledger |
| Prior real infrastructure trials could disappear from the narrative | Preserve Lazydocker/K9s evidence; optional bounded challenge lane without making Docker/Kubernetes a core prerequisite |
| Final demo acceptance inside qualification could depend on a later sprint | R6-Q only needs draft story inputs; qualified bytes then feed S14/R6-K final captures before publication |

## Pass 3: acceptance, adversarial review and scope

Review each milestone for a meaningful success condition, intended negative, wrong-failure detection, timeout/cancellation/cleanup when applicable, independent oracle, version/migration decision, and stop condition. Review competitor comparison fairness and user-validation timing.

Required outcomes: explicit no-launch invalid-input checks; independently justified terminal expectations; original evidence/baselines preserved; no missing-oracle pass; native host exclusions visible; no claim that retries erase initial failures; no adoption gate inside engineering; no future-as-shipped CLI commands.

Use [execution-contract.md](execution-contract.md) for the common acceptance/evidence rules and [decision-register.md](decision-register.md) for conditional outcomes. Add the 120-intent catalog and bounded benchmark protocol so broad goals have executable definitions. Keep one canonical status/order in root `roadmap.md` instead of maintaining duplicate competing roadmaps.

## Pass 4: mechanical consistency and recheck

After edits, check local Markdown targets and heading anchors, count unique corpus IDs, verify per-project and total workflow counts, check root release/sprint coverage, search stale ordering/current-status wording in active plans, and run `git diff --check`. Repair findings and rerun affected checks. Final command outcomes are reported at completion; this section defines the checks rather than pre-filling successful results.

## Pass 5: operational scenario review

Stress-reviewed unavailable hosts, required tests silently skipped, missing state oracles, unsupported catalog tasks, post-freeze changes, artifact budgets, old readers, public hash mismatch and adoption nonresponse. The [operational checklists](operational-checklists.md) define concrete responses without expanding the product feature budget.

Source inspection found that installer tests skip without PowerShell and on unsupported hosts; plans now require test-level pass/skip evidence. The release workflow still defaults to historical `v0.1.0`; R6 now requires an explicit unused version and a clean immutable release source. The install-smoke workflow exercises a checkout-relative action, so public immutable action verification remains a separate consumer gate. These are planning corrections, not changes to workflow implementation or new native test results.

## Remaining execution uncertainties

- Candidate application tasks must be admitted against actual pinned interfaces; the catalog is proposed intent, not compatibility evidence.
- Native Linux/macOS S8/S9 execution, public action verification and future release bytes require their own actual runs.
- Competitor capabilities come from public documentation; fair task-level runtime results remain to be collected.
- Independent user preference, retention, onboarding time and willingness to pay remain unknown until A1/A2.
- Exact implementation duration and CI cost depend on the five pilots. No use of “flawless” can remove those uncertainties; the plans make them observable and assign resolution points.

## Recorded verification outcomes

- Pass 1 facts rechecked against source: v1/v2 renderer handling, focused v2 rendering test, actual setup-action location, successful workspace cleanup implementation and peeled stable source commit all matched the corrected plan.
- Pass 2 dependency review corrected freeze/repetition order, oracle timing and installer-upgrade sequencing; a follow-up review removed the final-demo/qualification dependency cycle.
- Pass 3 reviewed all eight remaining sprint/release/adoption documents for entry, scope, evidence and exit, and reconciled existing S8/S9/R5 open gates with the root sequence. Optional handoff commands remain explicitly unimplemented.
- Pass 4 first scan resolved 242 local links and verified the 120-case catalog. A release/sprint representation check prompted adding explicit rows for planned Sprints 11–14; the corrected check passed for all five local release tags, all Sprints 0–14 and ordered steps 1–16.
- Catalog verification: 120 unique IDs, 15 project groups, eight proposed tasks per group; all five pilot IDs exist. Planned risk-family allocation totals 300; 10 workflows × 3 hosts × 100 attempts totals 3,000 repeated executions.
- Pass 4 mechanical rerun: 246 local links and five heading anchors resolved across 36 changed/new Markdown files; fenced code blocks balanced; `git diff --check` passed. Active-plan stale recruitment/old Sprint-10 adoption wording search found no outstanding matches.
- Go/PTY/native application tests were not rerun for this documentation-only planning audit. The planned corpus, competitor benchmark, candidate qualification and independent adoption remain unexecuted work, with no new passing runtime claims.

- Pass 5 final mechanical rerun: 255 local links and five heading anchors resolved across 37 changed/new Markdown files; code fences balanced; all 120 catalog IDs remain unique across 15 groups of eight; `git diff --check` passed. Operational scenario review added no product features or runtime coverage claims.
