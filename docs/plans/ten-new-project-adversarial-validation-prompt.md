# Execute ten NEW project journeys, adversarial stress tests and usability repairs

Prepared and explicitly invoked 10 October 2026. **Execution in progress; completion is not claimed.** [Execution evidence](../validation/ten-new-project-adversarial-pass/README.md) records actual status. Creating, linking or reading this reusable file does not independently invoke another campaign. When the user explicitly invokes it, execute the complete scope below, diagnose failures, implement general repairs, retest and finish all ten projects. Do not stop after selecting repositories, making a harness, obtaining a few green runs or writing a report.

## 1. Objective and standard of evidence

Act as a skeptical technical evaluator who wants to find reasons that Playtestr cannot be trusted. Also act as a developer with basic terminal/Git knowledge who wants a straightforward first test without understanding PTYs, terminal emulation or Playtestr internals.

Select ten independently maintained open-source interactive CLI/TUI repositories not previously credited as completed Playtestr project trials. Exercise useful normal work, distinct boundary cases, deliberate application regressions, misleading-success behavior, recovery, and realistic authoring/diagnosis friction. Implement every actionable in-scope Playtestr repair before accepting an affected project. Keep the runner deterministic and AI-free.

The first pass established 33 selected scenarios and 330 final repetitions. This pass must expand **different behaviors and failure modes**, not simply increase the repetition count. Green tests are insufficient when an assertion checks the wrong state, an external wrapper conceals a broken user journey, artifacts omit the cause, or cleanup leaves processes running.

Minimum execution contract:

- Ten new distinct repositories, selected after screening at least fifteen candidates and retaining at least five reserves.
- At least **five useful normal scenarios and five distinct edge/adversarial scenarios per accepted project**: at least **100 distinct project scenarios**. Extra cases are encouraged when evidence justifies them; trivial cosmetic variations do not count.
- At least ten fresh-state final executions per applicable scenario and qualified host. This supplies at least **1,000 primary-host executions**, plus separately counted additional native-host runs.
- At least two different real application regressions per project, with unchanged-contract detection and restoration: at least twenty regression controls. At least one state-corruption/false-success control for every project with saved state.
- At least forty distinct campaign-wide product failure controls, with a traceable coverage matrix. Variants of one input do not become forty failure modes. Required PTY/lifecycle/input controls execute natively on Linux, macOS and Windows where the operation exists.
- Native Linux execution for all ten projects; every project also qualifies on at least one other native OS. The batch includes at least five macOS and five Windows project qualifications: at least twenty project-host pairs, with additional overlaps counted honestly.
- A first-use, maintenance and failure-diagnosis assessment for every project, separate from engineering-only adversarial controls.
- Final qualification on one frozen Playtestr source/build identity, followed by confirmed removal of task-owned application source, builds, dependencies and caches.

These are admission minima, not a proof of 100% coverage. Publish a requirements/failure-mode matrix and explicit unknowns. Repetitions check stability; additional projects check diversity; neither is a percentage of all possible user behavior.

## 2. Controlling context and baseline

Read applicable `AGENTS.md`, [README](../../README.md), [roadmap](../../roadmap.md), [planning index](README.md), and these documents before execution:

- [Customer journeys](02-customer-journeys.md), [deterministic authoring](03-deterministic-authoring.md), [security/data](07-security-and-data.md), [campaign protocol](08-real-project-validation.md), [milestones](09-delivery-milestones.md), [quality/release](10-quality-and-release.md), [risks](12-risks-and-decisions.md), [execution templates](14-execution-templates.md), [candidate discovery](15-candidate-discovery.md).
- [Recording](../recording.md), [generated workflows](../generated-workflows.md), [v1 specs](../spec-v1.md), [v2 specs](../spec-v2.md), [workspaces](../workspaces.md), [snapshots](../snapshots.md), [terminal compatibility](../terminal-compatibility.md).
- [First ten-project results](../validation/ten-project-user-pass/README.md), [machine ledger](../validation/ten-project-user-pass/ledger.json), [findings](../validation/ten-project-user-pass/findings.md), [Windows reproduction evidence](../validation/ten-project-user-pass/windows-wizard-reproduction.json), [P0–P2 acceptance](../validation/p0-p2-2026-10-07.md).

Inspect actual code, branch, dirty/staged files, tool versions, public release versus source-candidate capabilities, available hosts and existing CI authorization. Preserve unrelated edits. The earlier frozen runner was `53561e6cbef4c80a25893c2f25be5a0979442103`; its evidence/helper commit was `c744f062d4fe1d6e20dfa98c84163af3aa26be74`. They are historical anchors, not a substitute for measuring the current checkout.

Read and audit the existing `scripts/acceptance/user_*.py`, removal scripts, public recorder and CI evidence helpers. Reuse sound functionality, but fix weak assumptions before relying on their output. Validate the harness independently; a harness's success message cannot prove its own cleanup, bounds or state oracle.

Do not overwrite the first pass or its failed attempts. Keep this batch separate. This is another early reliability/usability portion of P5, before P3/P4. Paid integration, billing, production infrastructure, commercial launch and the full-product 100-project campaign remain outside scope. Complete-product credit remains **0/100** until the campaign's actual admission requirements are met.

## 3. Authorization and safe operating boundary when invoked

The invoked task authorizes local research, public-source acquisition, ordinary reviewed build prerequisites, synthetic state, bounded local/hosted validation, general Playtestr implementation/tests/docs, and deletion of this task's owned temporary applications after evidence/process checks. Decide routine project, scenario, fixture and implementation choices autonomously; do not require the AFK user to design the tests.

Use the applicable session authorization for commits and pushes on the approved working branch. Use standard GitHub-hosted Actions for required native hosts when local devices are unavailable, as specified by repository instructions. Workflow preparation, authorized execution, monitoring and artifact retrieval are part of completion. Do not ask the user to acquire Linux/macOS hardware. No paid runners, budget increases, accounts or services without their separate authorization.

This prompt does not authorize outreach, upstream modification, releases, deployments, new forks, issues, discussions or PRs. Previous approval for two P0–P2 acceptance PRs is not approval for more. Use existing permitted workflow routes; if a remote permission is genuinely missing, complete independent work and record the exact unfinished gate. Never claim a configured workflow was executed.

Run only reviewed trusted targets with synthetic data. PTYs, subprocesses and temporary workspaces are **not sandboxes**. No production directories, personal credentials, user home scans, arbitrary external destinations, real repository remotes, signing keys or uncontrolled services. Review build hooks/license before execution; disable unnecessary hooks only through explicit documented setup, with the effect recorded.

Faults must be confined to owned processes and task paths. No global disk filling, host resource exhaustion, system clock changes, broad ACL changes, global package installs or killing unrelated processes. Restore any task-local permission changes in a bounded cleanup path. A canary uses conspicuous fake data, never a real secret.

## 4. Select new projects for failure diversity

First inventory previous completed project reports/corpora, including the first ten: Gum, fzf, micro, LazyGit, gdu, VisiData, LiteCLI, Harlequin, npkill and create-vite. Exclude previous credited repositories, forks/clones of those repositories, framework demos, tutorials and dependencies counted as applications. A previous project may be reacquired for repair verification but earns no new-project credit.

Search current primary GitHub/readme/license/build documentation. Screen at least fifteen candidates **before** acquiring the first target. Record URL, exact immutable revision, license, maintained/archived status, implementation language, terminal stack/style, prerequisites, documented supported hosts, fixture feasibility, risks and reason selected/rejected/reserved. Metadata alone is not evidence that a workflow works.

Choose at least four implementation languages, including at least one outside the previous Go/Python/TypeScript mix, and four terminal stacks or interaction models. Include at least four full-screen TUIs, two prompt/wizard/selector CLIs, and five applications with inspectable stateful outcomes. Categories may overlap. At least three selections should exercise substantially different behavior from the first pass, such as long scrolling/pagers, nested interactive modes, terminal subprocesses or local multi-file operations.

Select enough upstream-supported Windows/macOS applications to meet the native matrix. Do not satisfy diversity using unusable targets or make unsupported platform claims. Do not select applications merely because their demos are easy. Each selected project must offer five worthwhile normal and five distinct boundary workflows with positive evidence. Reject an unsuitable candidate with a concrete reason and no credit; retain failures caused by Playtestr and repair them instead of replacing the target to hide the defect.

Prefer offline workflows. A synthetic local service is allowed only when necessary: loopback-only address, owned port/process/state, explicit readiness, no credentials, bounded traffic/startup and verified teardown. Do not introduce external accounts to make a candidate work.

## 5. Establish limits before execution

Use these default per-case/per-target bounds; a measured exception must be written into the recipe **before** the affected run and cannot weaken a failing correctness assertion:

| Resource | Bound / treatment |
| --- | --- |
| Acquisition/build/install | Twenty-minute command deadline; record prerequisite/network/cache failures separately from Playtestr failures |
| Normal scenario | At most 120 seconds total; explicit step deadline at most 30 seconds; investigate actual readiness before changing it |
| Deliberate timeout/hang probe | Prefer 1–5 second product budgets; harness wall deadline at most 30 seconds, followed by bounded cleanup verification |
| CPU contention | Owned bounded worker, at most ten seconds per run; no global stress utility |
| Independent state command | Ten-second wall deadline, 4 MiB captured-output cap, explicit nonzero handling and process-tree cleanup |
| Output flood | Stop at declared product cap plus a bounded overshoot; cap harness capture independently; never keep draining without a deadline |
| Generated filesystem data | Explicit file-count/size limits; default at most 64 MiB of synthetic fixture/state per scenario |
| Target storage | Default at most 4 GiB task-owned checkout/build/dependency storage; monitor before proceeding |
| Raw evidence | At most 128 MiB per project; preserve useful first-failure evidence and a truncation record before compacting |
| Processes/jobs | Explicit concurrency and owned PID/process-group tracking; default one scenario at a time |

Work on **one application repository at a time**. Native jobs for that same project may execute on different isolated hosts; they may not leak fixtures or state into one another. Delete the target after its report and process checks before starting the next repository. Final requalification reacquires exact pins sequentially.

Choose deterministic seeds/orderings and record them. Small/large fixture variants must remain bounded and preserve intended semantics. Do not rename identical retries as timing variation. Do not invent onboarding duration for an interrupted stopwatch.

## 6. Two user-experience tracks per project

### A. Basic developer: documented path

Begin in a clean disposable directory with empty application config/HOME/temp and an explicit documented Playtestr install route. Separate upstream application's build/setup cost from Playtestr's cost. Run `--version` and follow the public quick start without private runner APIs, undocumented flags, editing implementation code or a custom operator wrapper that manufactures a successful first test.

Source-only capabilities must use a clearly documented source-candidate build; do not pretend an older published archive contains them. Record compiler/install prerequisites as friction. Do not publish a release merely to satisfy this task.

Complete: install/check version → select one important flow → record → inspect candidate → replay → save → ordinary test → intentionally fail → understand evidence → repair/rerecord → ordinary passing test. The common path should not require handwritten JSON, a bespoke Python script, knowledge of VT sequences, editing internal schemas, or reverse-engineering output directories. Real application build/fixture requirements remain explicit; they do not disappear because a harness hides them.

Use the following provisional usability gates and measure them honestly:

- First successful simple test: at most five shell-level Playtestr commands after target prerequisites, and at most fifteen minutes of active operator time excluding upstream build/download and clearly recorded interruptions.
- First simple flow: at most twenty recorder-control operations; count target interactions separately. Explicit review is required and does not count as a problem merely because it is human work.
- Ordinary failure diagnosis: within three documented shell commands, identify the failed step, expected/observed outcome, usable evidence location and a next action. Never display a green summary when readiness, evidence or execution failed.
- Intentional maintenance: one named expectation, visible change review, selected update/rerecord and normal rerun; no bulk acceptance or editing hidden cache files.
- Help/errors distinguish target build failure, spec error, assertion mismatch, timeout, target exit, cancellation, cleanup failure and unsupported capability in plain language. Paths/commands should be copyable on that host.

Measure commands, recorder operations, active elapsed time, documentation jumps, manual edits, undocumented discoveries and recovered mistakes. Explain misses, make general in-scope CLI/docs/onboarding repairs and repeat the affected route. A project cannot pass this track by relabeling complex setup as easy. If a provisional target remains unmet, record the exact unresolved UX gate rather than claim simple onboarding.

This is a constrained **operator assessment**, not a blinded beginner study. Do not claim independent users, satisfaction, adoption or measured usability for nontechnical people. Prior operator knowledge and warm caches are confounders and must be disclosed.

### B. Technical maintainer/evaluator

Exercise strict manual JSON authoring, explicit environment/fixture policies, suite selection, report generation, baseline maintenance, supported CI setup and diagnosis of intentional failures. Move the retained test/fixture package to a different synthetic checkout path, including spaces/Unicode, and replay without hidden machine-local dependencies.

Every project must demonstrate primary-flow suffix rerecord, one meaningful manual spec edit, selected baseline maintenance, an ordinary failing-and-passing CLI invocation, and a generated/inspected workflow. Run workflow-equivalent commands on each claimed host. A direct Actions run is hosted execution; it is not a real PR journey unless an authorized real PR was used.

## 7. Design useful normal workflows and adversarial project cases

For every project, write a scope table **before** authoring specs. Each case gets an ID, user risk, exact actions, positive terminal evidence, independently observable state where relevant, prerequisites, host applicability, expected exit/failure category, time/output bounds and exclusion rationale.

Five normal scenarios should span different useful outcomes. Examples include navigating/opening a nondefault item, searching a real noninitial result, changing and saving state, canceling a destructive action, and completing another important application-specific workflow. A wizard's five cosmetic selections are not five workflows. Include natural exit and meaningful resize/Unicode where supported.

Five or more project edge cases must cover different risks, such as:

- Empty/no-result input versus normal data; recovery back to a valid result.
- Invalid or boundary-length input with visible rejection; correction without restart.
- Cancel/escape at two distinct stages, including after unsaved edits or a destructive confirmation; prove preserved state.
- Repeated resize/small supported viewport, long content/scrolling or wrapping; assert a semantic outcome after resize.
- Duplicate labels/stale initially visible content; show selection/readiness cannot accidentally pass on the old state.
- Delayed redraw/readiness under a bounded supported delay or external load; rapid and ordinary input sequences, including paste when supported.
- Missing/unreadable synthetic resource, controlled application crash/exit, or owned descendant interruption with a bounded accurate outcome.
- A stateful operation claiming success while exact disk/index/database state differs; prove the independent oracle rejects it.

Not every application supports every example. Choose relevant cases and do not force undefined Unicode/style/mouse behavior into a success claim. Campaign-wide product controls below complement these **actual application cases** and are accounted for separately. A helper-only case cannot fill the ten real-project scenario quota.

Read every captured screen and compare it with intended state. A typed command is not proof it executed; a highlighted item is not proof it was selected; a success message is not proof data was saved; substring presence is not proof the expected row/cell was rendered. Use specific captions, result cells, cursor/state transitions and independent final state.

## 8. Mandatory product failure-mode matrix

Create `coverage-matrix.json` and a readable counterpart before running controls. Assign distinct requirement IDs, severity, acceptance/rejection behavior, test layer, real app/helper association, applicable native hosts and actual evidence IDs. Map at least forty **distinct** controls across every family below. Existing tests may be reused only if reviewed, executed on the candidate and linked to the actual requirement; a configured test name is not evidence.

| Family | Required investigations and controls |
| --- | --- |
| Lifecycle and observation | Natural zero exit; declared exact nonzero; unexpected nonzero; exit before checkpoint; quiet live hang; output followed by crash; EOF/exit race; bounded shutdown |
| Descendants and interruption | Child/grandchild persists after parent exit; descendant retains output handle; stubborn descendant; target interruption; runner/recorder cancellation; interrupted export; verify actual termination and workspace removal where supported |
| Resource/output boundaries | Flood before first step; flood during assertion; flood during idle; near-cap success versus over-cap failure; truncated/malformed output; bounded capture/artifact sizes; scoped CPU contention |
| Readiness and false passes | Already-satisfied/stale checkpoint; ambiguous anchor; incomplete redraw; disappearing then reappearing state; fast startup versus delayed startup; absent assertion without positive precondition; wrong-state success-looking screen; suite with no selected tests |
| Input | Empty/spaced/quoted argv; Unicode text; literal versus named controls; Enter versus CtrlJ; repeated key events; rapid sequences; bounded paste; unsupported key/input rejection; interrupted/incomplete sequence |
| Terminal state | Alternate-screen enter/leave; scrolling/wrap; erase/redraw; cursor location; repeated resize while output arrives; split UTF-8/VT writes; malformed/incomplete VT; wide/combining text within documented contract |
| Specs and paths | Malformed JSON; unknown/version-invalid fields; invalid dimensions/durations; NUL values; invalid executable; missing fixture/snapshot; traversal/absolute-path misuse; symlink/junction escape; relative cwd and moved checkout |
| Workspaces and environment | Fresh copied fixture/HOME/temp; dirty-state contamination; executable modes and CRLF/LF; read-only owned file/directory; missing prerequisite; explicit inheritance/rejection; no real home/config reliance |
| Snapshots and maintenance | Genuine mismatch; reviewed row range excludes actual relevant change; invalid/out-of-bounds range; resize changes range validity; selected update; failed update leaves previous baseline intact; interrupted multi-file export; no silent overwrite |
| Reports and user-facing results | Accurate process/failure/cleanup categories and exit codes; useful final screen; missing/corrupt report or evidence; report-root/path handling; HTML escaping of hostile synthetic text; summary cannot become green without valid results; selection/hash/version mismatch |
| Synthetic confidentiality | Conspicuous fake canary input/environment; inspect prohibited persistence in reports/logs/snapshots/replays; distinguish explicitly approved visible fixture content from secrets; reject or clearly document unsupported redaction promises |

Test promised behavior against the actual public contract. For intentionally unsupported VT queries, mouse/style/grapheme cases or environment modes, demonstrate safe bounded behavior/rejection and document the exact capability boundary. Do not turn every imaginable feature into an implementation requirement or label undefined behavior supported.

Pure validation/serialization uses table-driven tests. PTY, VT observation, keys, resize, timing, exit and cleanup use real terminal sessions and deterministic owned helpers on native hosts. Mocks alone cannot establish process/terminal behavior. Writer fault injection is allowed for bounded deterministic write-error/rollback tests; pair it with real temporary-file behavior, and disclose when it does not prove a genuinely full disk. Never fill the user's disk to obtain ENOSPC.

At least one actual application per applicable failure family should complement reduced helpers where safely possible. Stress controls stay small and diagnosable; no unbounded random fuzzing. Bounded fuzz/property campaigns must record seed/corpus, time/iteration limits and minimized failures; they supplement and do not replace explicit required cases.

## 9. Mutations, independent state and oracle calibration

For each project introduce two different minimal temporary faults in actual target behavior: one observable behavior/state-transition defect and one different outcome/error/exit/state defect. Use supported configuration when it genuinely changes tested behavior, otherwise a reviewed licensed source patch and ordinary rebuild of the pinned application. Preserve pristine source separately from the intentional defect and record actual changed binary/module/tree identity.

Keep the reviewed spec, baseline and fixture contracts unchanged for each negative/restoration pair. Preserve the original first red report, its category/step and actual screen. Assert the fault changed the real selected behavior; a missing executable, deliberately damaged assertion or fake-screen wrapper is not application-regression proof. Restore original bytes/configuration, rebuild and prove all affected scenarios recover. Never repair an accidental regression by accepting its snapshot.

For every stateful application also introduce actual persisted-state corruption while its UI still looks successful: wrong saved bytes, missing record, wrong commit/index, undeleted directory or altered generated file. Check the state before teardown using bounded independent probes. Do not infer state from the target's success message or reuse the target's own rendering function as the oracle.

Independently calibrate every oracle type with known correct state, actual wrong state, missing state and applicable nonzero/timeout/flood behavior. Verify execution/read location corresponds to the current fresh workspace. Derived expected manifests must come from reviewed pristine pinned inputs or separately constructed expectations, not the same faulty code path under test. Explicitly distinguish campaign-only probes from public Playtestr features.

Intentional expectation maintenance is separate: demonstrate an explicit intended input/configuration change, ordinary mismatch, visible review of the changed meaningful state, update only the named expectation and normal rerun. Preserve unrelated spec/baseline bytes. Small reviewed row regions must still detect changes to the asserted result; broadening/excluding a region to conceal a defect fails admission.

## 10. Stability, variation and native-host qualification

After each scenario's first successful reviewed replay, run exploratory repetitions from fresh state, retaining all attempts. On the final candidate, execute ten repetitions per scenario/qualified host with a predeclared schedule: normal runs, bounded contention and supported readiness/data/order variations. Do not change intended outcomes mid-series. Stable expectations need no update between repetitions.

Run the primary matrix on native Linux; WSL may supply explicitly labeled local exploratory evidence but does not fulfill the required hosted/native Linux matrix by itself. Execute every selected project on its additional upstream-supported native Windows/macOS host. Across the batch reach ten Linux, at least five Windows and at least five macOS qualifications, with every project represented on at least two native hosts.

Use the same frozen Playtestr source and reviewed contract wherever portable. Explicit platform differences need justified versioned variants and separate identities/counts. Cross-compilation is build evidence; it is not execution. A platform-specific unsupported case cannot be silently omitted from a claimed host qualification. If selection cannot meet the matrix, show the exact unresolved gate; do not relabel Linux/WSL results as native Windows coverage.

Run changed core input/terminal/lifecycle paths through actual native Linux/macOS/Windows checks, including race checks. Revisit the historical Windows wizard timeout using its retained sequence and bounded instrumented variations. Preserve its original first failure; no causal-fix claim without a reproducer that fails before and passes after an identified fix. New repeat successes remain evidence, not a diagnosis.

No automatic retries conceal flaky outcomes. Record pre-fix, post-fix and final qualification denominators separately. A failed final repetition pauses affected admission; retain it, investigate, repair and start a clearly labeled new affected series. Do not average a defect away or call eventual green zero failures.

## 11. Fix, simplify and requalify before advancing

Classify findings: Playtestr defect, harness/oracle defect, UX/docs friction, target behavior, unsupported capability, platform limitation or setup/environment prerequisite. Give severity, concrete reproduction, expected/observed behavior, first evidence, ownership, general fix/exclusion and affected-case list.

Critical/high false-pass, data-loss, secret-persistence, runaway process/output, inaccurate green check or common core-flow defects block affected acceptance. Implement the smallest coherent general repair at the parser, terminal session, runner, CLI, artifact writer or documentation boundary. Preserve Go as the local core; no AI, target-name switches, framework adapters, hidden environment exceptions, automatic semantic inference or arbitrary output stripping.

Every repair needs a regression that fails before the fix and exercises observable behavior afterward. Lifecycle/concurrency changes require actual PTYs and race checks. Strict public format changes update validation/schema/examples/migration documentation together. Useful UX improvements need direct before/after evidence, not just a prettier message asserted in a unit test.

After a general change, identify and requalify affected earlier cases/projects/hosts. Reacquire exact sources in owned directories and delete again. Different runner binaries must not inherit old qualification. Keep first failures; deadline changes, fixture corrections, test-authoring mistakes and assertion-scope decisions are explicit and never disguised as product fixes.

Larger useful ideas go into a measured backlog/ADR unless necessary to satisfy an existing promised deterministic workflow. No speculative service, new paid feature or unrelated redesign. If blocked by an external prerequisite, retain the block and continue independent work; never fabricate ten admissions or mark the overall task complete with missing required gates.

## 12. Sequential execution cycle for each project

1. Acquire reviewed pinned source/license into an owned disposable directory; record trusted setup/build hooks, hashes, timings and native-host recipe.
2. Run and measure the basic documented first-use route before relying on engineering shortcuts. Explore the actual application and declare scope/risk/host tables.
3. Record/review/export five normal and five edge cases with meaningful checkpoints. Inspect every baseline and independently verify state before teardown.
4. Exercise rerecord, manual maintenance, relocation, generated workflow and diagnosis on a real deliberate failure. Repair general onboarding friction and repeat the route.
5. Run project scenarios, relevant campaign-wide controls, both actual target regressions, state-corruption calibration and restoration. Preserve every first failure and contract identity.
6. Implement in-scope product/harness/UX repairs with reduced regressions; run appropriate tests and recheck affected earlier projects/hosts.
7. Execute the qualified native-host matrix and repetitions; inspect actual successful/failed jobs and retrieve bounded evidence. No configured-CI claims.
8. Close report with counts, scope, first failures, repairs, UX measurements, native identities, exclusions and residual risks. Verify copied evidence/hashes.
9. Confirm target/descendant/service termination, clean temporary state and safely remove task-owned application/runtime/cache paths before selecting the next active project.

After the tenth project, freeze the final runner source/builds and rerun **all one hundred or more admitted project scenarios** on their recorded qualified hosts, with ten fresh repetitions each, real negative/restoration controls and relevant final state verification. If a late repair changes behavior, invalidate and rerun affected final evidence instead of publishing a mixture of old runner versions.

## 13. Retained evidence and exact accounting

Create a new `docs/validation/ten-new-project-adversarial-pass/` tree and ignored `artifacts/ten-new-project-adversarial-pass/`. Preserve the prior campaign. Retain only tiny synthetic fixtures, reviewed specs/baselines, licensed minimal patches, locks/setup recipes, compact useful reports/screens, hashes and ledgers. No upstream checkout, application binary, dependency tree or downloaded archive in retained documentation.

Required package:

- Index with actual conclusions, exact source/runner identities, selected revisions/licenses, platform matrix, findings and limits.
- Candidate/reserve ledger created before first acquisition; exclusions and substitutions preserved.
- Coverage matrix linking each distinct requirement to applicable real-app cases, reduced controls, native evidence and exclusions.
- Per-project scope tables, source/build/reacquisition recipes, final specs/baselines/fixtures and explicit environment policy.
- UX ledger: route/commands/operations, stopwatch boundaries, confounders, friction, before/after repairs and unresolved gates.
- All-attempt accounting: unique run IDs, phase/source/host/case, pass/fail/cancel/setup-blocked status, first-failure category/step, seed/variation, duration and cleanup result.
- Genuine defect/restoration and state-oracle calibration identities, unchanged contract hashes, independent expected-state derivation and selected-update review.
- Actual native run/job/artifact IDs, source identities, successful steps, retrieval hashes and retention limits. Hashes do not make expired artifacts retrievable.
- Findings/severity/disposition register, general fix commits, affected requalification list, remaining constraints and confirmed cleanup record.

Distinguish unique projects, unique normal cases, unique edge cases, product fault controls, mutation controls, repeated executions and project-host pairs. Do not count helpers as external projects, repeated seeds as new requirements, retries as independent scenarios or unexecuted workflows as hosted evidence.

Begin append-only attempt preservation before the first run; do not repeat the earlier loss of overwritten passing retries. Preserve the first failure before any rerun/update. Separate mechanically passing but semantically rejected tests from accepted coverage. Record truncation/compaction and keep enough durable evidence to understand the failure after remote artifacts expire.

Preserve exact spec/baseline/fixture/license/patch bytes and verify their recorded hashes against the Git index/retained checkout. Review CRLF/LF, executable permissions, Unicode filenames, synthetic empty directories and symlink handling; reproducibility must survive a fresh checkout on the claimed host. Do not retain secrets or raw ambient environment dumps. Fake canaries are explicitly labeled.

## 14. Deletion and teardown

Track ownership at acquisition/install, including canonical workspace/root, application/revision and exact native runtime/cache paths. Before recursive deletion verify the resolved absolute target is an owned descendant of the intended temporary root, never the root, workspace, Git metadata, user project or unrelated link destination.

Confirm relevant processes/services/descendants are stopped; inspect evidence and hashes before removal. Unlink only verified owned links without following them; reject unknown reparse points/junctions. On Windows use native PowerShell `Remove-Item -LiteralPath` and path verification in one shell end to end. Do not enumerate paths then send them to another shell for deletion.

Remove task-created application sources, binaries, native venvs, task dependency caches and archives after acceptance/evidence capture. Preserve Playtestr, its compiler, pre-existing shared caches, unrelated edits/worktrees and earlier evidence. Check actual absence after removal. A failed teardown means incomplete cleanup; do not claim success or delete live state to hide it.

## 15. Completion gates and handoff

Run applicable full Go tests/vet, repository native race checks, public examples, actual recorder acceptance, helper/oracle failure controls, workflow syntax/context validation, documentation links and Git whitespace/hash checks. Test the user-visible install/help/diagnosis route on each claimed host. Avoid broad repeat checks when no new changes or failures justify them; final qualification itself remains mandatory.

Completion requires all ten new journeys and scenario minima, forty distinct failure controls, twenty actual target regressions, applicable state-corruption controls, required native matrix, final frozen-source repetition evidence, resolved actionable in-scope defects, documented UX gate outcomes, append-only counts and confirmed deletion. Remaining external blocks or missed gates must keep the affected project/batch unaccepted; do not issue a congratulatory completion claim.

Commit/push only within existing applicable authorization. Verify actual CI before claiming success. Update the planning status to distinguish this completed early hardening/usability pass from remaining P3/P4/full-product P5. Do not begin paid integration or launch automatically after this batch.

Communicate meaningful progress at least once a minute while working: current behavior, finding, general repair and verified outcome. Make routine decisions yourself and continue across project boundaries. Final handoff identifies exact runner/source, ten upstream pins, useful tested workflows, distinct failure-mode coverage, actual native outcomes, UX friction/improvements, unresolved risks, retained paths and removed applications.

The final conclusion must answer: **What is now demonstrably trustworthy? What could still break? How straightforward was the documented user route? Which advertised claims remain unsupported?** Never say this batch covers everything a user or investor could try. Publish the actual evidence and limits, not a made-up coverage percentage or commercial-readiness claim.
