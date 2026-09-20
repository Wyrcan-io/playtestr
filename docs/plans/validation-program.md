# Real-application validation program

Planned 19 September 2026; none of the new counts below is an execution result. Owner: Playtestr maintainer. Sprint 11 owns corpus construction; Sprint 13 owns native runner/CI verification; R6 owns qualification of frozen release bytes. This is operator engineering work, not maintainer adoption.

Read the [120-workflow intent catalog](corpus-catalog.md), [root order](../../roadmap.md), and [execution contract](execution-contract.md). Start with five pilots, not all 120 implementations. Final full-matrix and repeat evidence is collected only after R6-F freezes embedded version/build inputs/executable hashes. Sprint 11-C and R6-Q share that one qualification campaign.

## Size and accounting

Target **15 independently maintained applications, at least 120 distinct useful workflows, at least 300 focused contract/adversarial cases, and 3,000 repeated real-process executions**. These are complementary measures, not numbers to add into a single coverage claim.

- A workflow has a named user task, starting state, input sequence, readiness condition, independent expected result, and cleanup expectation. Eight meaningful workflows per admitted application gives 120; if a project cannot support eight, replace it or redistribute depth with a written rationale while retaining 15 distinct projects and 120 workflows.
- Host/viewport repetitions do not create new workflows. Baseline and mutated runs do not count as two user tasks. Existing cases count after review; do not duplicate tests simply to hit a number.
- Focused cases span pure validation and real-PTY lifecycle tests. Report unit and PTY totals separately. Table-driven cases need distinct input/risk, not merely duplicate names.
- Repetition target: 10 selected workflows on each of 3 native hosts, 100 fresh-process attempts per workflow-host cell = 3,000 executions. Choose from applications actually supported on that host; no demand that every project run everywhere. Rotate success, stateful, redraw and failure cases; record the composition.
- Counts are capacity targets. If a target is blocked, show the shortfall and rescope explicitly before release. Never silently call excluded cases passing or claim universal compatibility.

## Candidate application roster

Reuse existing reviewed pins/recipes where available. New entries are candidates, not compatibility claims. At checkpoint A, freeze exact versions/commits and hashes, licenses, runtimes, installation commands, offline data, and native host availability. Prefer fresh versions only in a separate upgrade lane.

| Candidate | Reason / proposed tasks | Independent result beyond screen |
| --- | --- | --- |
| Charm Gum | Selector, filter, input validation, confirm/cancel | Selected stdout/exit; no unexpected writes |
| Lazygit | Stage/unstage, diff navigation, commit draft/cancel, resize | Git index/tree/commit and draft/config checks |
| fzf | Filter, accept, no match, cancel, multi-select where supported | Exact selected records and status |
| Posting | Request editing, collections, validation, help, local request | Local deterministic server request log and saved collection |
| litecli | Query, completion, history, invalid SQL, exit | Disposable SQLite database query and file state |
| mitmproxy/mitmconsole | Navigation, filter, detail, help and cancel with offline flows | Fixture integrity and selected/exported flow where supported |
| bottom | Help, filter, modal dismissal, resize, redraw | Expected process exit; fixture/input invariants; avoid live-stat goldens |
| GitUI | Select/stage/unstage/diff/quit | Git index/worktree checks |
| television | Search, select, cancel, Unicode input, resize | Exact selected stdout; source file unchanged |
| npkill | Navigate/filter/dry-run/cancel | Synthetic tree markers/hashes; no real directory deletion |
| create-vite | Wizard choices, invalid entry, cancel, overwrite refusal | Exact scaffold manifest and package fields; no network execution |
| ipm-cli | Theme wizard, invalid type, retry, cancel | Package/CSS file postconditions in disposable fixture |
| micro | Edit, save, undo, search, cancel and resize | Exact saved bytes and unchanged neighbor files |
| tig | History/diff navigation, search, help and quit | Fixture repository unchanged; expected exit |
| taskwarrior-tui | Local task selection/filter/help/edit/cancel | Disposable task export and data invariants |

Eleven entries build on earlier Gum, Lazygit and nine-project cross-stack material; the eight tasks proposed for each still require admission. fzf, micro, tig and taskwarrior-tui are new candidates. Sources/prerequisites begin with the [existing cross-stack recipes](../trials/cross-stack-recipes.md) and [technical campaign](../trials/technical-trial-2026-09.md). Candidate repositories for additions: [fzf](https://github.com/junegunn/fzf), [micro](https://github.com/micro-editor/micro), [tig](https://github.com/jonas/tig), [taskwarrior-tui](https://github.com/kdheepak/taskwarrior-tui). Validate them during implementation before admitting versions. If setup or support makes one unsuitable, select a replacement of comparable interaction diversity and document why. A framework toy may supplement but cannot replace an independently maintained project. Historical Lazydocker/K9s results remain evidence; an optional isolated infrastructure challenge lane is separate from this deterministic offline campaign.

## Workflow design and defect detection

For each application cover meaningful navigation, input/validation, cancel/escape, state/result verification, and resize/redraw where applicable. At least two flows should exercise a failure or rejection meaningful to that application. Verify keyboard paths manually before encoding them; unsupported mouse-only routes remain blocked, not hacked into passing tests.

For every project, prove at least one known-good / known-bad / recovered sequence: **15 defect controls minimum**. Freeze expected baselines. Prefer a reviewed local source patch or known-bad revision with an independently verified defect. Record source license, patch hash, build command, and changes from upstream. An altered expected baseline proves mismatch detection only and cannot count as an application defect. Where a safe mutation is infeasible, use a documented known-bad behavior and keep the deficiency visible until accepted or the target is replaced.

Mutation families: wrong selected item, missing confirmation, reversed validation, canceled operation writing a file, incorrect exit, truncated saved text, lost state, and resize hiding a required control. Expected failure must identify the intended assertion/category; an unrelated crash or timeout is not a successful detection. Check recovery with the original baseline unchanged.

Stateful flows require independent postconditions. Read the Git index, parse the generated config, query the disposable database, or inspect the controlled server log. If the screen passes but the task did not happen, the harness fails and records the screen pass as misleading evidence. Keep target-specific checks outside the core. Harnesses must propagate failure, bound server lifetimes, and clean their own resources.

Successful spec-v2 workspaces are deleted before runner return. Apply the [catalog's oracle-lifecycle design](corpus-catalog.md#state-oracle-implementation-boundary): externally owned isolated resources, a verified pre-exit launch adapter, or a harness-owned ordinary cwd with separately tested v2 cleanup. Never inspect a deleted workspace, force a fake failed run to keep it, or add success-retention to the product merely for test convenience. An oracle timeout, missing result or malformed result is a harness failure, never a pass.

## Admission manifest and result accounting

Use the existing campaign manifest/evidence conventions first. Internal additions are test infrastructure, not new public report contracts. Each admitted ID records project/pin/hash/runtime/license, user task, spec/fixture/baseline/oracle revisions, setup/reset/cleanup ownership, native host status, time/output budgets, sensitivity control, actual attempts and exclusions. Keep application-defect controls distinct from changed-input and changed-baseline controls.

Use two outcome columns: **runner outcome** (passed, failed with category, cancelled, not run) and **campaign expectation** (correct good result, correctly detected intended bad result, wrong failure, false pass, setup blocked, oracle failure). A deliberate bad run still has a failing original runner report. The harness may consider the expected detection successful, but may not rewrite the report to green.

Case changes keep a supersession trail. Record discovery attempts before the final sample separately and preserve them; they are not erased by freezing a cleaner spec. Skips and excluded hosts reduce the supported boundary. Missing tests/resources do not meet the 120-workflow or 300-case targets.

## Focused risk matrix

Target allocation of 300 distinct cases (adjust only with a written coverage rationale):

| Family | Cases | Required dimensions |
| --- | ---: | --- |
| Spec/schema/CLI validation | 55 | Versions, unknown/null fields, invalid actions/keys/durations/dimensions, path and environment names; invalid input launches nothing |
| Process/input/lifecycle | 60 | Exit 0/nonzero/crash, silent/startup timeout, stuck input, flood, Ctrl+C, descendant natural exit/hang, repeated cleanup; real PTYs |
| Render/readiness/resize | 60 | Split bytes/escapes, stale text, delayed/continuous redraw, alternate screen, narrow/wide viewports, selected Unicode family; independently expected cells |
| Snapshots/suites | 40 | Missing/large baseline, transactional update/rollback, selector, collision, ordering, cancellation, empty/invalid selection |
| Workspace/environment/filesystem | 45 | Fresh copies, contaminated prior state, symlink/junction/traversal, permissions, bounds, retained failures, cleanup failure, explicit inheritance |
| Reports/install/artifact handling | 40 | v1/v2, hostile text, missing evidence, alias/path escape, truncation, atomic writes, corrupt/mismatched archive, interrupted download, upgrade |

Use table-driven tests for pure logic; real PTYs and observable process identities for lifecycle. Cover slow/instrumented runners with appropriate test-only deadlines while preserving product budgets. Do not invent impossible OS fault injection; document which cleanup faults can be induced on each host.

## Execution lanes and cost

| Lane | Work | Budget/trigger |
| --- | --- | --- |
| Pull request | Unit/contract checks plus 3 representative app smokes per available native host; change-specific regressions | Initial 15-minute host budget; profile if exceeded, never conceal failures |
| Nightly/scheduled | Full admitted host/workflow matrix, failures, fresh state and artifacts | Initial 60-minute host budget; deterministic sharding in CI harness, runner stays serial |
| Qualification | Full frozen matrix, 3,000-repeat campaign, 15 defect controls, install/upgrade checks | Batch across bounded jobs; estimate cost at checkpoint A and cap each job at 60 minutes |
| Upgrade canary | One changed target/dependency version at a time | Separate results from frozen support matrix; never silently refresh baselines |

Execution times are budgets to evaluate, not measured performance claims. Exact advertised runner hosts: Linux amd64, macOS arm64, Windows amd64. WSL Linux evidence remains labeled WSL and does not prove macOS or native Windows behavior. Admit at least five applications on each host and at least three shared applications across all hosts before the broad campaign gate closes. Unsupported application-host cells are explicit; choose other applications to meet host breadth. No network during a test unless it is the reviewed local harness endpoint; downloads/builds are setup and separately timed.

The PR lane contains representative high-risk cases, not the entire 3,000-repeat sample. Keep scheduled third-party-target jobs distinguishable from product-only regressions so upstream installation failures do not obscure runner correctness. Use pinned cached packages only with verified identity; a cold setup lane proves the recipe can still be obtained. CI job sharding is harness scheduling, not a new runner feature.

## Qualification composition, time and artifact budget

Choose ten distinct workflows per native host across at least five applications. Include selection, real state mutation, fresh workspace, modal/disappearance, resize/redraw, target rejection/expected nonzero and deliberate-negative paths. Record the exact ten IDs and expected result classes before the first sample. Use 100 fresh attempts per workflow-host cell; when bad/good variants share a task ID, label variants without inflating distinct workflow count.

Measure pilot median and slow-tail durations per host plus cold setup/build cost. Estimate serial execution minutes as `sum(attempt_count × measured_seconds_per_attempt) / 60`, then add setup, target builds, uploads and a visible contingency. Example only: 3,000 × 8 seconds is 400 aggregate execution minutes; 3,000 × 30 seconds is 1,500 minutes. These are arithmetic scenarios, not benchmarks or paid-CI prices. Decide sharding/cadence after actual pilot data, keeping each job bounded to 60 minutes. No unapproved paid infrastructure is assumed.

Initial campaign artifact limits: 64 MiB per attempt including report/evidence/logs, and 1 GiB per job before compression; do not enlarge product artifact limits to fill this allowance. Keep a complete compact attempt ledger plus failing evidence and representative successes. If a cap is reached, stop admitting new attempts, retain the ledger and a clear resource-limit result, and split the campaign into another bounded job. Do not silently discard failures to stay under budget. Target state directories are excluded from automatic upload.

Use the current 14-day CI artifact retention for working evidence unless the owner explicitly selects a different policy. Before artifacts expire, preserve a sanitized compact qualification record and the minimum reproducible failure proofs under a documented durable location; mark private/raw expired artifacts unavailable rather than claiming links still work. Demo video/capture assets are separately budgeted in Sprint 14 and do not count as runner diagnostic output.

## Reproducibility and result gates

Record runner commit/version/hash, target version/hash, host/OS release, runtime, fixture/baseline revision, locale, viewport, command, expected result, actual status/category/step, elapsed time, artifacts and cleanup evidence. Avoid environment values, secrets and real user files. Preserve the randomization seed when varying order; use fresh state per attempt. Artifact retention: all failing attempts plus representative successes, a complete compact ledger for every execution, and bounded disk usage with a recorded cap.

Gate: zero unexplained false passes, wrong failure identities, managed process leaks, or destructive cleanup failures. Investigate every unexplained repeated-run failure before qualification. Classify target nondeterminism, setup, runner, harness and infrastructure separately. A retry may help diagnosis but never replaces the first result; quarantined cases retain their issue and reduce declared support.

Report numerator/denominator per workflow and host. Zero failures in a finite sample does not establish zero flakiness; repeated runs may share correlated causes. At 0/100 independent attempts the rough rule-of-three upper bound is about 3%, not a guarantee; do not pool dissimilar cells into a marketing reliability percentage.

Exit record: complete support table, all exclusions and owners, costs, runnable recipes, defect evidence, repeat ledger and remaining limits. R6 reruns selected frozen-asset gates; source results alone never qualify an archive.
