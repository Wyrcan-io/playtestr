# Implement runner readiness through ten new adversarial project journeys

Prepared 16 October 2026. **Prompt only; not invoked.** Creating, reading or linking this file does not start implementation, acquisition, hosted execution or publication. When the user explicitly invokes it, carry out the engineering and validation scope below. Preserve earlier campaigns and their limitations.

## 1. Mission and completion boundary

Implement the missing deterministic runner experience while testing ten genuinely new open-source CLI/TUI applications as their maintainers would. Work sequentially: learn one real workflow, expose weaknesses, reduce failures, make general Playtestr repairs, verify them, then advance. Treat a plausible-looking green result as something to challenge.

This combines the priorities in [16 - runner stability and usability](16-runner-stability-and-usability.md):

1. R0: freeze observable requirements, issues, supported capabilities and accounting.
2. R1: ship public same-execution file/directory assertions, recording, review, maintenance and diagnosis.
3. R2: improve and measure the documented first-use and maintenance routes; prepare genuine beginner-study materials.
4. R3: investigate historical intermittent failures, resolve in-scope defects and qualify a precise native compatibility boundary.
5. R4: complete the first ten **new-project** packages in the expanded runner-readiness campaign, plus the old-project migration checks required by R1.
6. R5: build and privately qualify the exact candidate archives and their installation/documentation experience against this batch.

Ten new projects do **not** finish the 100-project program. Private candidate qualification does **not** authorize publishing a release. Agent walkthroughs do **not** establish human beginner usability. Report each of these gates separately. P3/P4, billing, paid infrastructure, marketing and outreach remain deferred.

Execute all independently achievable work across project boundaries when invoked. Do not stop after a design, scaffold, first project, local-only pass, a few green repetitions or a report describing unimplemented repairs. If a genuine external block remains, finish independent work and leave its exact gate open. Bounded investigations may end in an honest unresolved disposition; never loop indefinitely or invent evidence to declare success.

## 2. Read the controlling context and inspect the checkout

Read applicable `AGENTS.md`, [README](../../README.md), [roadmap](../../roadmap.md), [planning index](README.md), and:

- [Runner-first plan](16-runner-stability-and-usability.md), [customer journeys](02-customer-journeys.md), [deterministic authoring](03-deterministic-authoring.md), [security/data](07-security-and-data.md).
- [Project campaign protocol](08-real-project-validation.md), [milestones](09-delivery-milestones.md), [quality/release](10-quality-and-release.md), [risks](12-risks-and-decisions.md), [templates](14-execution-templates.md), [candidate discovery](15-candidate-discovery.md).
- [Recording](../recording.md), [workspaces](../workspaces.md), [spec v1](../spec-v1.md), [spec v2](../spec-v2.md), [report v1](../report-v1.md), [report v2](../report-v2.md), [snapshots](../snapshots.md), [failure reports](../failure-reports.md), [generated workflows](../generated-workflows.md), [terminal compatibility](../terminal-compatibility.md), [platform support](../platform-support.md), [development](../development.md).
- [Earlier ten-project results](../validation/ten-project-user-pass/README.md), [latest adversarial report](../validation/ten-new-project-adversarial-pass/final-report.md), [limitations](../validation/ten-new-project-adversarial-pass/limitations.md), [usability assessment](../validation/ten-new-project-adversarial-pass/usability-assessment.md), and [evidence/storage policy](../validation/README.md).
- [Previous adversarial execution prompt](ten-new-project-adversarial-validation-prompt.md), as historical procedure rather than a command to overwrite or repeat its campaign.

Inspect actual implementation, schemas, recorder, terminal/process boundaries, acceptance helpers and CI workflows. Record branch/HEAD, staged and unrelated edits, toolchains, available native architectures and source-versus-published capabilities. Preserve unrelated work. Old runner qualification at `5f8867a` is historical evidence, not automatic qualification of the current or future binaries.

Some old raw evidence is ignored and archived locally. Inspect its index and extract only necessary files into an owned directory inside Playtestr. Do not expand the former 40 GB tree. Missing evidence means an unverified claim, not permission to manufacture a successful replacement. Ordinary development tests and fresh CI must work without the author's historical archive.

## 3. Authority and filesystem boundary

When invoked, this prompt authorizes scoped Playtestr implementation, regression tests, documentation, primary-source research, reviewed public target acquisition/builds, synthetic fixtures, bounded validation, private candidate packages and deletion of this campaign's owned temporary files.

**Do not modify or delete anything outside the Playtestr workspace.** On the local machine the allowed root is `C:\Users\abhir\OneDrive\Documents\playtestr`. On a hosted runner use only that job's Playtestr checkout and explicitly owned descendants. Resolve the root at runtime; do not copy the Windows absolute path into portable fixtures.

- Read/execute installed tools where needed, but put newly created target homes, temporary directories, package caches, build caches, venvs and downloads under owned campaign roots. Override relevant tool paths per process; verify where prerequisites write. Do not install globally or alter user Git, shell, package-manager, registry or compiler configuration.
- Preserve existing `.tools`, `.cache`, Git history, earlier evidence and shared prerequisites. An ignored path is not automatically disposable. Never run blanket `git clean`, destructive resets or history rewrites.
- Use existing applicable commit/push authorization on the approved branch; this file grants no independent blanket remote mutation permission. Standard GitHub-hosted native Linux/macOS/Windows validation is the repository's preferred route. Prepare, execute, monitor and retrieve scoped workflow evidence under applicable authorization; missing local devices are not a reason to abandon native checks.
- No paid runner, account, budget increase, release, public tag, deployment, license change, upstream fork, outreach or GitHub issue/discussion/PR mutation is authorized here. A generated workflow run is not a real PR test. Do not create PRs to fill a checkbox without specific permission for that action.
- Targets and build scripts must be reviewed and trusted. Use synthetic data, offline paths and local-only services. PTYs, subprocesses and managed directories are not security sandboxes.
- No host disk filling, global load generation, clock changes, broad permission changes or killing unrelated processes. Track owned PIDs/process groups and stop only those. Use explicit safe failure injection instead of exhausting the user's machine.

Choose routine architecture, target, scenario and repair decisions autonomously within this boundary. Keep the shipped runner deterministic and AI-free. Do not add LLM dependencies, autonomous application exploration or framework/target-specific core branches.

## 4. Create campaign records before execution

Use a new namespace:

- Curated source-controlled material: `docs/validation/runner-readiness-ten-project-pass/`.
- Temporary applications, raw attempts, collections, caches and candidate archives: `artifacts/runner-readiness-ten-project-pass/`.
- Small reusable acceptance code: the existing appropriate test packages or `scripts/acceptance/`, using parameterized roots instead of hardcoded old-campaign paths.

Create an index, requirements/findings register, candidate ledger, scenario/host declarations, resource forecast, attempt schema, compatibility matrix and resume checkpoint. Do not mark declared tests executed.

Every requirement/finding records ID, user-visible behavior, severity, first evidence, affected layers/hosts, exact acceptance, fix/disposition, regression evidence and requalification impact. Map every limitation from the previous campaign to a new test, implementation slice or explicit residual-risk decision.

Use separate counters for:

1. New projects screened, attempted, development-admitted and final-archive-qualified.
2. Old projects revalidated under the new public assertion contract.
3. Runner-readiness admissions toward 100, deduplicated across campaign IDs.
4. Complete paid-product launch admissions, which remain zero for this runner-only work.
5. Unique scenarios, product controls, real target faults, repetitions, retries and native project/host cells.

Persist attempts before launch with unique IDs. Record candidate/binary, target pin/build, contract/fixture hashes, host/architecture, phase, variation seed, status, duration, resource observations and cleanup. Use one synchronized writer or separate immutable streams merged with validation; test concurrent records and interrupted writes. Preserve first failures and reject malformed/incomplete evidence. Never overwrite a failed attempt with its successful retry.

## 5. Sequence the work as vertical slices

| Stage | Work | Exit before advancing |
| --- | --- | --- |
| A | Baseline, issues, storage controls, candidate screening | Requirements, bounds, actual baseline and diverse feasible pins recorded |
| B | Small R1 public vertical slice with deterministic fixture | Record/review/export/replay catches a real wrong saved file in the same execution; clean and failure paths tested |
| C | First two new projects | Complete all project gates; expand R1 only for measured general needs; simplify first use |
| D | Projects three through eight | One repository at a time; fix and requalify affected earlier cases; investigate R3 in bounded batches |
| E | Reserved projects nine and ten | Freeze a provisional candidate first; evaluate transfer to new workflows, recording all consumed holdouts and repairs |
| F | Prior-project migration, final source freeze and native packages | Required old cases migrate; public formats/docs align; all candidate archives built once and checksummed |
| G | Final archive-based project/native matrix and audit | All final evidence binds to exact candidate bytes, controls and cleanup; no mixed-version qualification |

Use real user-visible increments; do not build several speculative frameworks before the first runnable file assertion. Project discoveries can refine the implementation before final freeze. Any late change invalidates the affected evidence and archive identity; rebuild and restart the affected final series explicitly.

## 6. R1: public same-execution saved-state assertions

Write a concise architecture decision before implementing syntax. Decide public spec/report versions, exact action semantics, limits, path resolution, checkpoint timing, recorder controls, expected-byte storage, maintenance and compatibility. Do not preemptively select a version number without inspecting existing consumers.

Minimum public primitives:

- A regular file exists and has the exact reviewed bytes.
- A declared path is absent.
- A directory exists or is empty.
- A bounded exact directory-entry set detects unexpected/missing entries when required by actual workflows.

Inspect the current execution's managed workspace at the declared step or after an observed target exit, **before cleanup**. A second target/recorder execution, retained folder after a different run or external successful probe cannot satisfy the public runner's state assertion. Prove invocation/workspace identity in tests and reports without exposing sensitive contents.

Specify whether each condition polls and how reads handle changing files. Keep reads, waits and traversal bounded by both per-action and whole-run budgets; respect cancellation. Partial/inconsistent observations cannot produce success. Do not promise atomic whole-directory capture while an application is writing. A correctness assertion is not a durability/fsync guarantee.

Exact bytes are the default. Empty files, trailing newline, CRLF/LF, UTF-8, binary NUL bytes and same-length corruption must remain distinguishable. Any optional normalization must be explicit, reviewed, independently tested and justified by a real requirement. No implicit timestamp removal, broad ignore patterns or baseline regeneration to conceal a defect.

Resolve only selected relative paths within the declared managed root. Reject absolute, drive-relative, UNC/device, parent-traversal, NUL, ambiguous Windows stream/reserved-path and unsupported path forms as appropriate to the public contract. Reject linked ancestors, symlinks, junctions/reparse points, special files and wrong types. Use no-follow/handle protections where the platform supports them; test path replacement during observation and state the remaining trusted-target race boundary honestly. Include pre-execution validation and runtime checks when paths can change after launch. Never read an outside path to demonstrate an escape: use owned inside-workspace canary destinations.

Bound assertion count, expected/observed bytes, directory depth/entry count, individual reads, aggregate evidence and duration. Missing, wrong type, wrong bytes, extra entries, unreadable, oversized, timeout, target exit, cancellation and cleanup errors need accurate distinct diagnoses. Define actual handling of unreadable paths on privileged hosts; a mock permission exception is not proof of native permissions.

Users select expected output paths. Do not scan arbitrary project/home trees for baselines. Preview candidate file contents safely, including control/binary bytes, with explicit size limits and review. Keep unreviewed or unselected file contents out of reports, HTML, replay data and logs. Review synthetic canary persistence in every output format. Do not claim blanket redaction of a target's visible terminal output.

Update parser, schema, runner, recorder/replay, machine/HTML reports, examples, migration and help together. Older tools must reject unsupported new formats before target launch; existing v1/v2 tests retain their contract. Generic screen snapshot updates must not silently approve file expectations. Selected file-baseline updates must preserve unrelated bytes and survive failed/interrupted writes without corrupting approved data.

Do not add arbitrary shell assertion hooks or target/database/Git adapters to evade this feature. For unsupported structured outcomes retain separately labeled independent checks without claiming they are a shipped general oracle.

## 7. R1 acceptance and the earlier ten projects

Before using the feature as a campaign oracle, calibrate it independently with known correct, missing, wrong-type, subtly corrupted and oversized state. Include a fixture whose screen says success while the saved bytes are wrong. The ordinary public `playtestr test` invocation must fail nonzero in that same run, and restoring only the target must pass unchanged expectations.

Test file create/edit/copy/rename/delete, hidden/extra entries, nested/empty directories, Unicode/spaced paths, concurrent append/truncate/replace, read errors, deadline boundaries, output flood during a file wait, cancellation, natural/nonzero exit and cleanup. Permission/link/reparse variations run on their actual applicable native hosts. Pure parser tests and mocked filesystem errors supplement real filesystem/PTY execution.

Reacquire the previous ten adversarial applications sequentially at their recorded pins: Cookiecutter, Copier, lf, Superfile, Helix, Glow, Broot, Yazi, Ranger and nnn. Preserve original reports. Migrate representable saved outcomes to public same-run assertions, retaining independent probes only as calibration. Re-run all representable old scenarios, their state-corruption/recovery controls and affected authoring routes on their previously qualified hosts. Do not convert formerly unqualified Windows paths into passes without evidence.

Keep migration counts and any runner-readiness re-admissions separate from the ten **new** projects. Required old-project migration can add unique runner admissions only when the complete expanded admission contract is actually satisfied; a migrated assertion alone earns no admission. Do not repeat old standalone state probes as a substitute for migration.

## 8. Select ten genuinely new projects for useful risk diversity

Inventory all previous completed project/corpus identities first. Exclude previously credited applications and forks/renamings of the same product. Known exclusions include Gum, fzf, micro, LazyGit, gdu, VisiData, LiteCLI, Harlequin, npkill, create-vite and the ten applications named above; inspect the actual records for additional exclusions.

Research primary upstream GitHub/readme/license/build/platform sources at execution time. Screen at least **twenty** candidates before acquiring the first target, choose ten plus at least five workable reserves, and preserve all screening decisions. Record canonical owner/repo, immutable revision, license, implementation language, terminal stack/interaction model, documented host support, meaningful workflow opportunities, setup risks, dependencies, expected storage and safe disposal.

The selected ten must include:

- At least four implementation-language families and four terminal interaction/framework families; no one family dominates more than half the set.
- At least four full-screen TUIs and three prompt/selector/wizard applications; categories can overlap.
- At least eight applications with useful file/directory outcomes representable by the new public assertions.
- At least five application categories, with deliberate coverage of behaviors beyond another nearly identical file browser or scaffolding wizard.
- All ten on native Linux and each on at least one additional upstream-supported native host; across the ten, at least five Windows and five macOS qualifications.

Reject targets requiring production secrets, uncontrolled services, undistributable fixtures, unsupported core input/protocols or excessive prerequisites. Prefer offline flows. A necessary loopback-only synthetic service needs owned ports/processes/data, readiness, time/output caps and verified teardown.

A project must support twenty worthwhile distinct scenarios and three genuine regression controls to be admitted. Do not count `--help`, theme choices or trivial repeated selections as breadth. An unsuitable target may be replaced with preserved reasons; a Playtestr defect must be fixed or remain a blocker, not hidden by replacing its target.

Reserve projects nine and ten after metadata screening. Do not build their workflow tests or tune the runner on them until the provisional candidate is frozen. A reserved project that drives a repair becomes a development project; retain it and its first failure, disclose lost holdout status, and use a reserve if making a fresh-transfer claim. Never erase difficult holdouts from the record.

## 9. Measure a straightforward user route on every project

First attempt the public documentation with an exact candidate binary in a clean task-owned directory. No prepared Playtestr spec, undocumented command, private API, custom Python wrapper or internal schema edit may manufacture the first useful test. Task-owned upstream fixtures/setup are allowed and must be described as such.

The route is: install/check version -> launch recorder -> drive useful target actions -> choose meaningful screen and relevant file checkpoints -> preview/review -> replay fresh -> export -> ordinary CLI run -> diagnose a seeded failure -> selectively maintain an intended change -> replay -> generate the ordinary free CI workflow.

The first supported flow must require **no handwritten JSON**. File-baseline review remains explicit: Playtestr can capture actual bytes, but the maintainer decides whether those bytes are correct. Explain this in ordinary language. Do not promise automatic discovery of all expected behavior, coverage or correctness.

Freeze these engineering usability targets before attempts:

- At most five Playtestr shell invocations and twenty recorder controls to the first reviewed ordinary test after target availability. Define and record the exact starting/ending milestones and count repeated invocations after errors.
- No unexplained hang; ordinary failures name the failed expectation, expected/observed category, evidence location and concrete next action.
- Within three documented diagnostic shell commands, an operator can identify the failed step and a useful next action.
- Selected maintenance visibly reviews the intended screen/file change, preserves all unrelated expectations and passes normally afterward.
- Moving the retained package to a fresh owned path with spaces/Unicode works without hidden absolute paths, credentials or warm-machine state.

For each project retain command/control counts, target interactions, manual edits, documentation jumps, assistance, first errors, setup/build/download time, active operator intervals and interruptions. Separate initial from repaired routes. Automated replay elapsed time is not human authoring time; agent wall time is not evidence of beginner speed. Warm/cold caches and prior knowledge must be disclosed.

Also exercise the technical-maintainer route: explicit environment policy, meaningful manual spec authoring/edit, suite selection, suffix rerecord, selected screen and file updates, machine/HTML report, relocation and generated workflow. Technical flexibility must not be a prerequisite for the beginner route.

Implement measured general CLI/docs/recorder improvements and repeat the affected fresh-start routes. Do not retain a cumbersome workaround and label it easy. Leave unmet targets visible.

Prepare task sheets, synthetic fixtures, consent/observation instructions and forms for at least five real unfamiliar participants with differing technical experience. Proposed human targets remain first reviewed replay within fifteen active minutes after target availability and seeded-failure diagnosis within ten. Do not recruit/contact anyone without specific authorization. If no participants exist, finish the engineering campaign and mark human usability **unmeasured**; it cannot be closed by an agent persona or invented stopwatch.

## 10. Twenty meaningful scenarios per new project

Before authoring tests, declare at least **eight normal and twelve distinct edge/adversarial scenarios** per project: at least **200 distinct real-project scenarios** across the ten. Each needs an ID, user risk, preconditions, actions, positive readiness evidence, expected terminal/exit/file outcome, exact checkpoint, host applicability, resource budgets and exclusion rationale.

Normal scenarios must span materially different useful tasks: a nondefault selection, successful search/filter/open, real edit/save or generation, another state-changing task, safe cancellation, restoration/reopen, navigation across nested/long content and clean completion where applicable. Tailor these to actual application behavior rather than forcing every app into the same template.

Select twelve or more distinct project edge cases from relevant risks, extending the list when discovery justifies it:

1. Empty input/data and no-result recovery.
2. Invalid or boundary-length input, visible rejection and correction without restarting.
3. Duplicate/ambiguous labels or stale initial text that could fool an anchor.
4. Cancel before confirmation and cancel after unsaved changes, proving unchanged state.
5. Small supported viewport, repeated resize and semantic correctness after redraw.
6. Long content, scrolling/wrapping, off-screen selection and return to a known item.
7. Supported Unicode, combining/wide text and spaced/Unicode paths at declared contract boundaries.
8. Rapid versus ordinary supported input, repeated controls and bounded supported paste.
9. Delayed readiness/output under a controlled bounded condition, with no arbitrary sleeps used as proof.
10. Missing, wrong-type, unreadable or read-only owned resource with accurate error/recovery.
11. Pre-existing/dirty state and deterministic fresh-workspace behavior.
12. Unexpected target exit/crash, exit before checkpoint or cancellation during a meaningful operation.
13. Child/subcommand transition where the application genuinely has one; observe return and cleanup.
14. Wrong saved bytes or unwanted extra file behind an otherwise successful screen.
15. Partial save/rename/delete, boundary-size file or unsaved-change preservation.
16. Failure evidence or maintenance path with missing/corrupt artifacts and accurate refusal.

The twelve cases must represent distinct user risks, not twelve strings entered into one field. Product/helper controls, mutation executions and repeated seeds are counted separately and cannot fill this quota. Unsupported actions are qualification boundaries rather than mandatory application features.

Include at least four meaningful combined-risk cases per project within those twelve: for example resize during delayed redraw followed by save; cancellation after editing with pre-existing files; a successful screen plus a partial write and unexpected exit; or relocation with Unicode paths and selected baseline maintenance. Choose combinations the real application supports. Add a small risk-based interaction table so features that pass independently are also exercised together, without attempting an unbounded Cartesian product.

Read the captured screens and inspect intended semantics. A key being sent is not proof of an action; a highlighted row is not proof it was opened; a banner is not proof of readiness; a successful screen is not proof of saved data. Use specific post-transition evidence and the public state assertions.

## 11. Genuine regressions, false-green controls and holdout faults

For each new project demonstrate at least **three distinct real target faults**, detected by unchanged reviewed tests and followed by exact restoration: at least **thirty distinct target faults**.

- One changes a meaningful terminal interaction/state transition.
- One changes another outcome, cancellation behavior, exit/error path or state transition.
- For every stateful project, one preserves a success-looking screen while writing wrong/missing/extra persisted state. This can be the third fault, but the persisted corruption must be real.

Use minimal reviewed patches in the licensed pinned upstream source and rebuild normally, or a genuinely relevant supported target configuration fault. Preserve the patch and actual mutated source/binary identity. Missing executables, fake screen wrappers, broken expectations and harness-only failures are not genuine target faults. If no safe patch is feasible, a reproducible historical good/bad target pair can substitute with explicit evidence and unchanged expectations; otherwise leave admission open.

Declare one of the three faults per project after freezing its reviewed tests, without adding a special expected string to catch that exact mutation. This is a held-out fault, not an independent human red-team review. If unchanged tests miss it, record the false green, identify the absent general requirement, strengthen authoring/assertions and retest. Retain the original miss; the repaired control loses untouched holdout status.

For state corruption, prove ordinary public runner failure in the **same corrupted execution**, with unchanged reviewed file expectations. A separate probe may independently confirm corruption but cannot supply runner acceptance. Restore only target source/configuration, rebuild, confirm identities, and pass unchanged tests. Track mutation and restoration runs separately from ordinary repetition counts.

In each false-green control, retain evidence that the relevant screen checkpoints passed and the public saved-state assertion actually rejected the corrupt outcome. A run that fails earlier because the target did not start is not evidence of state-corruption detection. Where both an assertion and teardown fail, preserve both outcomes and keep the overall result nonzero.

Calibrate every oracle type with independently constructed correct, subtly wrong, missing and applicable wrong-type state. Expected values must come from reviewed fixtures/specification or an independent derivation, never the faulty output function. Unsupported databases/indexes/structured state remain explicitly outside file assertions unless separately designed and implemented for a measured general need.

## 12. Product control matrix: deepen the existing coverage

Review and rerun the previous campaign's **88 declared controls** with explicit per-host applicability, supersession or justified unsupported status. An old test name/green summary is not current execution evidence. Do not lower the old scope to a smaller convenient headline number.

Add at least **thirty distinct new controls** focused on the new public state, recorder, migration, archive and storage contracts. Do not count renamed duplicates, seeds, OS copies or assertion values as distinct failure modes. If an old control already covers a proposed new requirement, reuse its ID and choose a genuinely uncovered risk for new credit.

The matrix must cover these families with actual tests, expected failure behavior, host identities and evidence IDs:

| Family | Required depth |
| --- | --- |
| Lifecycle | Natural zero/nonzero exits, unexpected exit, EOF/drain ordering, output then crash, quiet hang, timeout and cancellation |
| Descendants | Child/grandchild persists, output-handle retention, stubborn process, recorder interruption, confirmed tree termination and separate cleanup errors |
| Output/resources | Flood before/during/after checkpoint, near/over caps, bounded read/capture/artifact sizes, controlled contention, no runaway retries |
| Readiness | Stale/ambiguous anchor, partial redraw, output across resize, disappearing/reappearing state, empty selection, no positive evidence |
| Input/VT | Supported controls and paste, malformed/split UTF-8/VT, wrap/scroll/alternate screen, supported width behavior, resize/input ordering and unsupported rejection |
| Parsing/compatibility | Strict fields/versions, invalid values, old/new schema rejection before launch, mixed suite/report versions, migration and preserved older contracts |
| Managed state | Exact/empty/binary bytes, missing/wrong type, extra/hidden entries, nested/empty directories, concurrent writes/replacement, limits and cancellation |
| Path boundaries | Traversal, absolute/drive/UNC forms, Windows aliases/streams, symlink/junction/ancestor swaps, Unicode/case, special files and safe refusal |
| Recording/review | Select/preview/approve state, stale candidate, rejected candidate, replay export equivalence, no silent scan, bounded draft and unsupported controls |
| Maintenance | Selected screen/file update, unrelated hash preservation, old baseline survives interrupted/error writes, explicit state review, relocated baselines |
| Reports/privacy | Accurate red result and exit code, useful bounded diagnostics, HTML escaping, malformed/missing evidence, no unreviewed file/canary persistence |
| Candidate/install | Checksum/archive identity, binary-only clean install, paths/permissions, documented offline behavior, upgrade/rollback and workflow pin parity |
| Harness/storage | Concurrent/truncated ledger handling, provenance mismatch, missing artifact, dedup/restore integrity, byte/count cap and verified owned cleanup |

Use real PTYs, native filesystems and deterministic owned helpers for terminal/lifecycle/state behavior. Table-driven tests fit pure logic. Fault injection can prove bounded error handling but must disclose limits, such as simulated ENOSPC versus an actually full volume. No harmful host experiments.

Add bounded seeded fuzz/property testing for changed parsers/path validation, file expectations, VT chunking or report decoding where it can expose meaningful invariants. Record corpus/seed, explicit time/iteration budget and minimized failures. Fuzzing supplements declared acceptance and real applications; it does not replace them or become an unbounded hunt.

## 13. Historical intermittent failures and compatibility

Investigate the original Windows wizard timeout, earlier macOS readiness/exit0 incident and later helper exit8 separately. Preserve the known reduced heartbeat publication repair without claiming it explains unlogged historical branches.

For each unresolved incident record original evidence availability, source/helper identity, hypotheses, discriminating experiments and an investigation budget. Start with three native batches of fifty repetitions of the affected reduced control, instrumented/uninstrumented as relevant. Use deterministic scheduling where possible, bounded output chunking/resize/load variations and monotonic observations. A missing old archive is a limit on original-cause claims.

Do not increase product deadlines or add silent retries to obtain green. Later success demonstrates only the exercised schedule. Classify as proven product fix, proven fixture/harness fix, target/environment limit or unreproduced residual risk. A critical/high unresolved failure in a promised core flow blocks stable qualification; it does not require endless repetition.

Revisit Superfile and Glow on Windows at the recorded pins with bounded original-path reproduction. If Playtestr has a general defect, fix and qualify it. If the pinned upstream path remains racy/unsupported, keep that exclusion; Linux/macOS success or patched upstream input does not qualify unmodified Windows behavior.

Maintain a feature x OS x architecture matrix distinguishing supported, unsupported and unqualified. Qualify actual common keyboard, redraw, resize, lifecycle, state and supported Unicode paths. Mouse, clipboard, plugins, terminal replies, arbitrary graphemes/styles and network services need specific evidence or explicit exclusion. Avoid turning every conceivable terminal feature into an implementation requirement.

## 14. Fix and requalify before advancing

For every failure: preserve first evidence -> classify ownership/severity -> reduce -> state acceptance -> implement the smallest general repair -> prove before/after -> run relevant native/race checks -> requalify affected earlier cases -> continue.

False pass, data loss, unintended file exposure, unsafe cleanup, unbounded process/output or misleading successful result blocks affected admission. Fix product defects in the proper Go boundary. Fix test/oracle errors honestly without labeling them product improvements. Documentation alone cannot close an implementation defect.

No target-name switches, framework adapters, hidden environment exceptions, blanket timing padding, automatic baseline acceptance or broad output stripping. Larger ideas go into a measured backlog unless needed for the current public promise.

Use `gofmt`, useful wrapped errors, bounded goroutines/reads/waits, synchronized shared state and explicit cleanup. Run race checks after lifecycle/concurrency changes. Regressions must exercise observable behavior and fail before the relevant fix. Apply full appropriate Go tests/vet, public examples and real recorder routes; avoid repeatedly broadening checks without new changes/failures.

Track the dependency impact of each change. Development passes on older binaries do not transfer to newer ones. A final product/build-input change requires new candidate archives and a clearly identified replacement final series. Preserve abandoned/failing final series and their denominators.

## 15. Native-host matrix and rigorous repetitions

All ten new projects run on native Linux; each additionally runs on at least one supported native OS. Across the batch obtain at least five Windows and five macOS qualifications: at least **twenty project/host cells**. Existing repository core/control checks execute on all three native OS families. Name the exact actual architecture; cross-compilation is build evidence only.

All twenty or more declared scenarios must qualify in each admitted project/host cell. Explicit portable variants may preserve the same semantics. A missing required host/case leaves that cell open; do not quietly count a partial cell or replace required native evidence with WSL. WSL remains useful labeled exploratory evidence.

On the final archive binaries run at least **twelve fresh-state executions per scenario per qualified host**, with a predeclared schedule such as:

- Four ordinary runs, including cold and warm owned target setup with costs separated.
- Two supported viewport/path variants with reviewed semantics.
- Two supported input/readiness schedule variants.
- Two bounded contention/output-timing variants.
- Two repetitions of the highest-risk supported boundary for that scenario.

Adapt the schedule to genuine applicable risks before execution. If a variation changes expected semantics, declare a separate contract variant; do not rewrite expectations mid-series. Identical retries are not new variants.

The minima imply **2,400 primary Linux ordinary executions** and **4,800 ordinary executions across twenty cells**, before old-project migration, product controls, mutations and recoveries. Additional cells/cases increase counts. These are resource forecasts and accounting minima, not universal reliability percentages.

Retain all attempted runs and first failures. A failed final repetition rejects the affected series until diagnosed and requalified; eventual success is not a zero-failure sample. Predeclare and record any justified budget change before its new series, preserving the original failure and unchanged correctness criteria.

## 16. Exact archives, installation, migration and free CI

Build versioned private candidate archives from frozen source/inputs on each claimed native architecture, using existing packaging conventions. Build once per platform, checksum, extract inside owned paths and use those exact extracted binaries for final project qualification. Record per-platform source/build/binary/archive identities; different native hashes are expected, untracked builds are not.

Exercise source-free non-administrator installation from the archive, version/help, spaces/Unicode paths, ordinary executable permissions, fixture setup, first recording, screen/file failure/recovery, report generation and uninstall/cleanup. Test documented checksum verification with a deliberately corrupted owned archive. Do not silently download a replacement binary and call the original archive qualified.

Test compatible old specs/reports, unsupported-version refusal before launch, intentional upgrade/rollback, selected maintenance and preservation of old approved expectations. State target-runtime requirements separately from Playtestr's standalone binary installation. With prerequisites cached, prove supported local record/test/report operation without application-level network access; do not change system firewall settings or claim OS-level network isolation.

Use the delivered free workflow to build the real target, run tests, preserve failure evidence and recover in an owned harness. Inspect actual jobs, run conclusions and retained artifact bytes. Pin the candidate route correctly; do not generate a workflow pointing to an older download that lacks recording/state features. Hosted workflow execution is not proof of a real same-repo/fork PR event journey.

Keep stable releases untouched. Align candidate-specific docs, migration notes and capability tables with the tested archives without claiming unpublished features exist in old downloads. Prepare a reviewable publication packet if useful; release/tag publication requires separate explicit authorization and later public-download verification.

## 17. Storage and resource limits: prevent another 40 GB accumulation

Plan and measure storage before acquiring applications. Only **one application repository** is active locally at a time, including old-project migration/final reacquisition. The same project may execute on isolated native hosts. Keep source, binaries, dependencies and caches inside its owned root; remove them after verified evidence capture and termination before acquiring the next project.

Default campaign limits:

| Resource | Bound |
| --- | --- |
| Total newly created local campaign storage | 6 GiB across all this campaign's roots; forecast and monitor before acquisition/extraction/build/collection |
| One active target including dependencies/build caches | 4 GiB; screen out impractical candidates rather than silently exceeding it |
| Retained local evidence and candidate packages | 2 GiB total, with raw/compacted inventories and no duplicate history |
| Curated material added to Git | 25 MiB total; small reports/contracts/fixtures/patches, no raw run dumps |
| Retained raw/compacted evidence per new project | 64 MiB across hosts; first failures prioritized, unique payloads deduplicated |
| Old-project migration evidence | 32 MiB per old project; count within the same total retained cap |
| One synthetic scenario workspace | 64 MiB and a declared file/entry count |
| Acquisition/build command | 20-minute wall budget with bounded output and owned process-tree cleanup |
| Ordinary scenario | 120-second whole-scenario ceiling, step budgets at most 30 seconds unless measured and predeclared |
| Intentional hang | Prefer 1-5 second product budget; independent harness ceiling 30 seconds including bounded shutdown |
| Harness command output | 4 MiB default; explicit cap plus useful truncation metadata |
| Owned contention worker | At most ten seconds, explicitly bounded process count and workload |
| Scenario concurrency | One per host by default; declare hosted job cap and total minute forecast before dispatch |

Monitor storage during long builds/downloads as well as at milestones. Enforce command/output/generated-data bounds; a periodic inventory is not an operating-system quota or proof of an exact peak. Stop the growing operation safely before its budget is exhausted, preserve the failure and release owned expendable data. No automatic paid capacity expansion or storage-limit increase. Record host storage separately; downloading all hosted trees locally is unnecessary.

Prevent duplication at its source:

- Store canonical source/spec/fixture provenance once per content identity. Attempts reference hashes, not full copied historical manifests.
- An Actions artifact contains that job's new bounded evidence and required canonical inputs, never the whole `docs/validation`, `native`, identity store or accumulated attempts ledger.
- Retrieve selected files/stream bounded archive members. Do not repeatedly expand complete multi-host historical artifacts to collect one report.
- Serialize compact attempt metadata; retain first failure details and summaries for repeated passes. Deduplicate identical screens/payloads with a verified reference map. Preserve enough metadata to reconstruct all counts and identify every outcome.
- Keep bulk raw evidence under ignored campaign paths. Update narrow ignore rules if needed; never force-add an entire collection to Git. Verify a fresh source checkout runs ordinary tests without local raw history.
- Before deleting expanded retained evidence, produce a bounded archive/index, verify compressed integrity, file/path coverage and hashes or byte equality of preserved payloads, and test selected restore inside the workspace. References must resolve without omitted dictionaries or expired remote artifacts. Do not deduplicate merely by trusting an unverified filename.

If limits cannot retain necessary failure evidence, stop affected acceptance, compact safely and document the exact storage conflict. Do not discard first failures, hashes or ledger rows to satisfy a budget, and do not grow the user's machine silently.

## 18. Per-project execution and deletion checklist

For each new project, then each old-project migration/final reacquisition:

1. Verify canonical owned root, immutable source/license and reviewed build hooks; create ownership and resource records.
2. Acquire/build with local caches and synthetic environment; distinguish setup failures from runner failures.
3. Attempt and measure the documentation-only first-use route before using private harness shortcuts.
4. Declare risk/scenario/host/variation tables; author and review meaningful screen/file expectations.
5. Exercise diagnosis, suffix rerecord, selected screen/file maintenance, relocation and free workflow.
6. Execute scenarios, real target faults, false-green controls, oracle calibration and restoration with all attempts retained.
7. Reduce/fix general defects, test before/after, and requalify affected earlier cases/hosts.
8. Obtain actual native evidence, inspect outcomes and finalize bounded retained recipes/reports/hashes.
9. Confirm owned target/descendant/service termination and successful managed-state cleanup.
10. Verify retained evidence/restore ability; remove only this task's checked source, binaries, dependencies, caches and temporary downloads; confirm absence before advancing.

Before recursive deletion, resolve absolute paths and verify they are owned descendants of the campaign root, never workspace/root/Git/shared toolchain/earlier evidence. Reject unknown junctions/reparse points; unlink an owned link without following it only after validating its ownership. On Windows use native PowerShell `Remove-Item -LiteralPath` with checked paths in one shell end to end. Do not enumerate paths in one shell and hand generated deletion commands to another.

All cleanup stays inside Playtestr. A failed teardown remains an open cleanup gate; do not claim removal or delete live state to conceal a process leak.

## 19. Deliverables and independent audit

Retain a concise public index and reports plus a bounded ignored audit package containing:

- Requirements/finding dispositions and a readable coverage matrix with actual evidence IDs.
- Candidate decisions/reserves, exact pins/licenses/platform sources and selection/substitution history.
- Per-project scenario contracts, tiny synthetic fixtures, reviewed baselines, minimal licensed fault patches, build/reacquisition recipes and environment policies.
- R1 design/migration notes, public parser/schema/recorder/report changes, before/after regressions and old-project migration results.
- First-use/maintenance/diagnosis measurements, raw counting definitions, confounders, general improvements, study materials and real human status.
- Original red outcomes, true faults/misses/restorations, unchanged-contract hashes and public same-execution state proof.
- Frozen candidate source/build/archive/binary identities, actual native runs/jobs/architecture, bounded artifact retrieval and retention receipts.
- All-attempt accounting, final-series boundaries, exact distinct/repetition/host counts and failure denominators.
- Historical reliability dispositions, feature/host compatibility, unsupported cases and remaining blockers.
- Storage high-water observations with measurement limits, dedup/archive verification, restore check and confirmed per-project teardown.

Validate the auditor against deliberately incomplete/tampered synthetic evidence: missing run, wrong binary, duplicated project, mismatched contract, absent fault restoration, state proof from another invocation, partial host series, missing first failure and unsafe/incomplete cleanup. Each must reject qualification. Audit actual evidence rather than trusting a helper's `complete: true` field.

Verify retained/public file hashes survive fresh checkout line endings, executable modes, Unicode paths and empty fixture directories. Public links must resolve to tracked material; ignored evidence paths must be labeled local-only instead of presented as public downloads. Never force-add raw evidence to make links appear valid.

Run appropriate Go tests/vet/native race checks, public examples, recorder/state acceptance, harness/auditor checks, workflow validation, documentation links and whitespace checks. Record actual commands/outcomes/skips. A configured workflow or skipped platform test is not a successful native run.

## 20. Exact completion gates and honest handoff

The scoped **engineering campaign** can complete only when:

- R1 exists in the public runner/recorder/reports with format migration, same-execution proof and accurate failure/cleanup behavior.
- Ten new independent projects meet the eight-normal/twelve-edge minima, native cell matrix, three real faults each, applicable public state-corruption controls and first-use/maintenance assessment.
- Required old-project representable assertions are migrated and revalidated, with unsupported outcomes explicitly separated.
- Existing product-control scope is preserved and at least thirty genuinely new controls execute with correct applicability; every changed public/lifecycle/state path has appropriate native regression evidence.
- The final archive binaries pass the full declared new-project matrix, at least twelve fresh executions per scenario/cell, actual fault/restoration checks and applicable old-project migration/control matrix. No stale binary can supply final credit.
- In-scope actionable defects are repaired and requalified. No unresolved critical/high promised core-flow defect is hidden by an exclusion or green retry.
- Exact candidate installation/migration/free-CI results, native identities, all attempts, compact evidence and confirmed workspace-only cleanup pass audit within storage bounds.
- Human usability, 100-project breadth, historical residual risks and public publication have their true separate statuses.

An external missing participant or unapproved publication does not stop independent engineering. Report those gates as unmeasured/not authorized; do not call the entire roadmap, stable release or launch complete. A genuine blocker preventing a required engineering gate keeps the affected campaign acceptance open, with a concrete reproducer and next action rather than an invented admission.

Update the runner-first roadmap/index with actual evidence, measured effort, new runner admission counts and the next 30/60/80/100 stages. Do not mark all of R4 or final 100-project R5 complete from this batch. Do not begin paid integration, release or marketing automatically afterward.

During execution send meaningful visible progress at least once per minute and persist a resume checkpoint after every project and material fix: current candidate, active case, verified counts, new finding, next action, storage and open gates. Continue across routine milestones without requesting decisions already delegated by the user. Resume from records after interruptions without rerunning completed work unnecessarily.

The final handoff must answer, with exact evidence: **What did we implement? What useful workflows and adversarial failures did the actual candidate detect? Which false greens did we find? What became simpler? Which exact native paths passed? What remains unmeasured or unsupported? How much storage remains, and were all owned targets removed?**

Never equate project counts, repetitions, an agent's persona or a green summary with exhaustive investor/user coverage, zero flakiness, autonomous semantic discovery, beginner readiness, commercial readiness or passive income.
