# Sprint 13: trust the installed runner and its evidence

Status: 13-A0/A1, B, C and D completed. A0/A1/B passed on Windows amd64, Linux
amd64 and macOS arm64; C is an intentionally Linux amd64 matched comparison.
The setup-action expansion passed its exact-commit three-host workflow gate;
see the [A1 evidence record](../../validation/sprint-13-a1-integrated-hardening-2026-09-21.md)
and [B record](../../validation/sprint-13-b-setup-action-2026-09-21.md).
The [C comparison record](../../validation/sprint-13-c-competitive-2026-09-22.md)
contains the 360-attempt ledger, controls, costs and adversarial results.
Owner: Playtestr maintainer/release owner. Integrated A1/B/C follow corpus
discovery and any selected 10/12/6 implementation. [Root roadmap](../../../roadmap.md)
owns sequence. Finish existing engineering boundaries before adding features.

User result: an exact installed runner behaves as documented on its advertised host, preserves diagnosis for failure, and can be upgraded without corrupting tests or state.

## A0: surface existing native gaps early

Inspect the actual setup action at `setup-playtestr/action.yml`, its installer/integration tests, the workspace implementation and current report rendering. Inventory recorded host results before running anything. Source inspection and existing S9 evidence already establish v2 HTML support; do not propose a replacement renderer.

Use the [operational checklists](../operational-checklists.md) for initial commands and required test events. Installer tests can skip when PowerShell is absent: a green `go test` exit alone is insufficient. Record native filesystem privilege skips explicitly and resolve required proof before claiming support.

Run focused current-source installer/workspace/report checks on available native hosts and prepare missing jobs. Every row names commit, OS/architecture, command, expected result, observed exit, artifact and remaining gap. An unavailable host remains blocked; independent pilot/recipe work can continue. No publication is needed just to design or locally exercise these checks. Any remote push/dispatch requirement remains an explicit external action.

Acceptance: Windows results refreshed when code changes require it; Linux/macOS source paths either actually verified or have concrete outstanding jobs. Prioritize real native lifecycle/installer defects before convenience features. This checkpoint is an evidence inventory and early repair gate, not a claim that all three hosts are available in the current environment.

## A1: close integrated native and contract gaps

Run current-source tests, vet, relevant manual examples and concurrency/lifecycle race checks on Linux amd64, macOS arm64 and Windows amd64. Record exact OS image, toolchain, commit and exit statuses. Missing race compiler is a missing prerequisite, never a pass. WSL evidence remains separately identified.

Exercise current spec/report v2 workspaces on every claimed host: fresh copies, retained failures, prior-state contamination, links/junctions, interrupted runs, descendant cleanup, output flood and deletion failures. Review v1 compatibility and mixed-suite behavior.

Verify the existing `playtestr report` v2 integration on each native host and later candidate bytes. `internal/report/html.go` already accepts v1/v2; `TestRenderHTMLReportV2WorkspaceOutcome` and the S9 walkthrough cover local behavior. Add only missing meaningful cases, such as mixed suites and separate setup/cleanup failures. Preserve v1 rendering, atomic output and distinction between target, workspace, cleanup and artifact outcomes.

Acceptance: frozen supported contracts agree across CLI/help/schema/docs and exact native paths; known unsupported behavior remains explicit. Positive and deliberate-negative evidence is available from the same commit.

## B: finish Sprint 8 installation engineering

Prepare an immutable action revision and test the source action on the three mapped native hosts, with exact runner pin, checksum/archive checks, fallback archive route and offline-next-step execution. Cover corrupt checksum, wrong member/platform, partial download, failed extraction, preexisting conflicting binary, path quoting and bounded cleanup.

Publication remains R6's explicitly authorized action. After publication, R6 verifies the immutable public action revision and downloaded bytes. A later real runner release must exercise upgrade behavior; keep that longitudinal gate open if no second suitable release exists. Do not manufacture releases to check a box or describe a local simulation as a public upgrade.

## C: measure comparisons and resource limits

Execute the [detailed benchmark protocol](../competitive-benchmark.md), grounded in the [research survey](../../research/competitive-user-survey-2026-09-19.md#fair-comparison-protocol). Start with one shared task across Atago, Microsoft's matching beta, Termlens and Playtestr before expanding to three. Record unsupported cases and setup burden without forcing a dishonest common denominator. Use the same host and target versions for comparable runs.

Run at least 30 fresh executions per admitted tool/task/host comparison cell; this is exploratory comparison, separate from Playtestr's 3,000-run qualification campaign. Test hang/cancel/flood cleanup using observable process identities and matched budgets. Preserve all attempts and resources. Pre-adoption diagnosis times are operator-biased; independent preference waits for A1.

Profile runner overhead separately from target build/download/startup and intentional waits. Establish budgets from baseline measurements, investigate regressions, and do not relax product limits to pass instrumentation. Capture slow-host and high-output behavior. Publish favorable and unfavorable outcomes with methodology; no universal winner badge.

## D: adversarial evidence and release rehearsal

Run the validation-program risk matrix, including hostile report text, missing/large evidence, traversal/aliases, canceled staged baseline updates, stale artifacts, report-write errors, permission failures and environment privacy. Inspect retained artifacts for synthetic secret sentinels; targets can print secrets, so do not claim automatic redaction without evidence and an explicit contract.

Manual rehearsal: install a development rehearsal archive into a path with spaces, run a mixed v1/v2 suite containing pass, expected nonzero and intentional failure, export the report, inspect cleanup, and rerun recovery. This archive precedes the R6-F freeze and is not final qualification evidence. Test the failure exit code, not just file existence.

After Sprint 11-B depth and these checks close, hand the actual source/schema/fixture/build inputs to **R6-F**. Build and package the candidate with its final qualification version before Sprint 11-C repetitions. Sprint 13-D prepares freeze; it does not require the long campaign to have finished already. Public action verification and publication belong to R6-P/V, not this local engineering completion claim.

## Native evidence matrix

Each row needs Windows amd64, Linux amd64 and macOS arm64 result cells; absent evidence is blocked or not applicable with reason, never implicitly green.

| Path | Success proof | Failure proof |
| --- | --- | --- |
| Runner v1 | Existing menu/suite pass, exact expected nonzero | Deliberate mismatch, timeout, cancel, flood and separate cleanup outcomes |
| Workspace v2 | Fresh copy/home/temp; original fixture unchanged | Setup rejection, partial copy cancellation, target-created links, retained failed state, deletion failure where inducible |
| Report v1/v2 | Actual generated documents render and preserve facts | Invalid version/schema, unsafe evidence, missing files, separate setup/cleanup failure, existing output preserved |
| Action source | Exact installed binary/version/hash and PATH precedence | Wrong checksum/member/platform, interrupted/oversized download, no ready outputs on failure |
| Process lifecycle | Natural exit and managed descendants gone | Hung input, early exit, cancel, output cap; documented escape boundary retained |
| Package rehearsal | Native extracted binary in spaced path works | Corrupt archive and invalid member/layout rejected |

All source/native correctness gates required for advertised support close before R6-F. Where one remains unavailable, report the concrete blocker and continue independent work; do not label the candidate ready for that host.

## Exit

- [x] Three native hosts, current contracts and correct report evidence verified.
- [x] Action source validated; public revision and later-release gates clearly separated.
- [x] Fair task comparison and cost measurements recorded with limitations.
- [x] Relevant success/failure/timeout/cancel/cleanup/security-boundary cases pass.
- [x] Frozen candidate checklist and remaining blockers handed to R6.

No package-channel expansion, retry engine, parallel scheduler, hosted report service or CI-vendor SDK is included.
