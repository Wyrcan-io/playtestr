# 16 — Runner stability and usability before paid integration

Planning decision: **16 October 2026**. The user moved runner stability, useful saved-state assertions, simple onboarding and broad real-project validation ahead of P3/P4. This document defines that work; it does not start implementation, download projects, run a campaign, publish a release or authorize outreach.

Current baseline: source candidate `74f80f2`, with runner inputs qualified at `5f8867a`. The [latest engineering report](../validation/ten-new-project-adversarial-pass/final-report.md) covers ten projects, 130 scenarios and 21 project/host pairs. Its saved-state probes and prepared authoring measurements retain their original limits. Existing published archives do not contain all current-source features.

## Order and scope

Work in this order:

1. R0: freeze the runner promise and turn current evidence gaps into tracked acceptance cases.
2. R1: implement public saved-state assertions and their recorder/report experience.
3. R2: simplify first use, maintenance and diagnosis; run fresh-start usability trials.
4. R3: investigate intermittent failures and qualify the supported terminal/platform boundary.
5. R4: validate 100 distinct projects against the complete runner experience, with general repairs and requalification.
6. R5: qualify exact downloadable candidate archives and installation/documentation parity.
7. Reassess runner readiness, then proceed to P3 paid review integration and P4 commerce when invoked. Full-product validation and commercial launch qualification still follow those phases.

R1–R3 proceed in small vertical slices; relevant fixes return to affected earlier cases. Do not finish 100 old-contract demonstrations before delivering the assertion and authoring experience those projects must validate. Build internal candidate binaries for R2/R4; R5 is final distribution qualification, not the first time installation is tested.

P3/P4 are deferred, not prerequisites for this runner campaign. Existing paid-product requirements remain active for an eventual paid launch.

“100” means **100 distinct independently maintained applications** for breadth, with repetitions reported separately. The latest batch already exceeds 100 executions. Neither 100 executions nor 100 projects proves universal correctness.

## R0 — A precise supported promise

Create a requirement/issue ledger before new execution. Each entry records severity, observed symptom, exact evidence, affected hosts, owner layer, intended acceptance and current disposition: implemented/qualified, open blocker, or explicitly unsupported. Preserve historical first failures.

The runner promise is deterministic regression testing of developer-selected trusted CLI/TUI workflows. Developers record actions, select meaningful checkpoints and review expectations. There is no AI dependency, automatic whole-application specification discovery or security sandbox.

Acceptance: every item in the latest [limitations](../validation/ten-new-project-adversarial-pass/limitations.md) has a concrete next test, implementation slice or supported-scope decision. “Everything stable” is not a test case; pass/fail criteria must be observable.

## R1 — Saved-state assertions in the shipped runner

### Minimum useful behavior

Add first-class assertions for a regular file's existence and exact reviewed bytes, a path's absence, and a directory's existence or emptiness. Support a bounded exact directory-entry assertion where it is needed to detect unintended extra files. Cover creation, editing, copy, rename and deletion through those general primitives.

Assertions must inspect the **same running test's managed workspace**, at the declared checkpoint or after observed target exit, before teardown. A second recorder execution cannot establish what the original execution saved. Distinguish a missing file, wrong type, wrong contents, unexpected entry, read error and timeout. Preserve cleanup errors independently.

Use exact byte comparison by default. Any optional text/newline normalization must be an explicit reviewed contract with native tests, not an invisible change that hides corruption. Do not add arbitrary shell assertion hooks, database adapters, Git-specific logic or target-name branches as a shortcut. More structured assertions need a measured requirement and their own small design decision.

### Safety and public formats

- Resolve assertions relative to an explicit managed workspace; reject absolute/escaping paths, linked ancestors, symlinks, junctions/reparse paths and unsupported file types. Test Windows path/case behavior explicitly.
- Bound assertion counts, bytes, entries, reads and waits. Declare limits before execution; oversized/unreadable state fails visibly. Handle concurrent writes and process exit without returning success from an incomplete observation. Make no claim of atomic whole-filesystem capture.
- Never scan a home directory or automatically collect arbitrary generated files. Users select output paths. Treat contents as potentially sensitive; preview and approve candidate baselines, bound evidence, and avoid putting unreviewed contents in logs or reports.
- Choose the public spec/report version in an architecture decision before implementation. Existing strict v1/v2 consumers must not silently ignore new assertions. Update parser, schemas, runner, reports, examples, migration and older-tool rejection together.
- Generic snapshot updates must not silently approve saved-state changes. Define explicit selected maintenance and review for file expectations.

### Simple authoring

Extend the recorder so a user can choose an output file/path, preview the candidate expectation and include it in the exported test. A successful simple flow must require no handwritten JSON. Explain that captured actual bytes are a candidate baseline, not proof they are semantically correct. The user reviews the intended result; the tool checks it deterministically thereafter.

### Acceptance

Reduced controls must fail before each relevant fix. Exercise correct bytes, subtly wrong bytes, missing/wrong-type paths, unexpected/hidden entries, empty directories, large/unreadable files, linked ancestors, Unicode/spaced paths, timeout and cleanup on applicable native hosts. A target that renders success but writes wrong data must make the public runner fail nonzero in that same execution. Restoring the target passes unchanged expectations.

Requalify all ten latest project fixtures using public assertions where their outcomes are representable, replacing separate campaign-only probes as the acceptance mechanism for those outcomes. Keep independent probes as calibration where useful. If a workflow needs an unsupported structured-state oracle, label the gap; do not market it as covered by the new file feature.

## R2 — First use and maintenance without insider knowledge

Define one documented route: install an exact candidate binary → record a meaningful trusted workflow → choose screen and relevant file checkpoints → review → replay fresh → diagnose a deliberate failure → update only an intended change → replay again → generate the free CI workflow.

Start from clean task-owned directories, without prepared Playtestr specs or undocumented helper commands. Include space/Unicode paths and an ordinary supported non-administrator installation. Record target prerequisites/build effort separately, while retaining the total elapsed journey; never hide required setup in a warm-cache claim. Exercise install/help/error messages and recovery on all advertised native hosts.

Use at least ten fresh-start journeys, including the eight projects whose prior human-authoring interval was unmeasured. An agent may conduct documentation-only engineering trials and identify friction. It must not relabel those trials as human or independent beginner measurements.

Provisional engineering targets, frozen before trials:

- No handwritten JSON or knowledge of PTY internals for the first supported useful flow.
- At most five Playtestr shell commands and twenty recorder controls for that flow; target interaction and installation/build commands are accounted for separately.
- No unexplained hang; failures identify the failed expectation, useful evidence and a concrete next action.
- Selected maintenance preserves unrelated expectations; relocation and ordinary CI use need no hidden maintainer setup.

For a genuine beginner assessment, prepare a task sheet and observation form for at least five consenting people unfamiliar with Playtestr, with differing technical experience. Give them the candidate and public docs, record all assistance, abandonment and first errors, and measure installation, authoring and diagnosis separately. Proposed targets: first reviewed replay within fifteen active minutes after the target is available, and diagnosis of the seeded failure within ten. Small-sample results are formative, not population guarantees; every observed serious blocker needs a general repair and a fresh trial.

Preparing the private study materials is allowed. Contacting or recruiting anyone requires specific user authorization. If no participants are available, continue all independent engineering work and leave human usability **unmeasured**; a beginner-readiness claim remains blocked. Never fabricate a timer or replace people with agents to close that gate.

## R3 — Reliability and a bounded compatibility promise

### Historical intermittent failures

Investigate the original Windows wizard timeout, the earlier macOS readiness/exit0 failure, and the later helper exit8 separately. The [late fixture repair](../validation/ten-new-project-adversarial-pass/core/macos-stubborn-late-failure/manifest.json) proves a heartbeat publication bug in a reduced checkpoint; it does not establish every original hosted branch's cause.

Preserve raw first failures. Capture serialized outcomes, bounded final screens, readiness observations, input/resize/drain order, helper errors and cleanup results with monotonic timing. Do not record ambient secrets. Use the original pinned sequence and one controlled variation at a time: instrumented/uninstrumented execution, output chunking, resize timing, fresh/warm state and bounded contention. A deterministic reduced schedule is preferable to hoping a race appears again.

Before each investigation declare a resource/time budget and repeat schedule; start with three separately reported native batches of fifty repetitions for an affected reduced control, adjusting only with a recorded reason. No automatic product retries or deadline increases to obtain green. Successful repetitions bound observations; they do not establish a cause or guarantee a failure rate.

Disposition must be evidence-based: proven product repair; proven fixture/harness repair; documented environment/target limitation; or unreproduced with explicit residual risk. An unresolved critical/high issue in a promised core flow blocks stable qualification. If evidence cannot support classification, keep the candidate prerelease and retain the open blocker rather than run indefinitely or declare the incident fixed.

### Compatibility

Build a feature × OS × exact host/architecture matrix with supported, unsupported and unqualified states. Preserve the existing [terminal contract](../terminal-compatibility.md). Cover common advertised keyboard navigation, input, redraw, resize, exit, cleanup and supported Unicode paths with real PTYs and representative applications.

Prioritize failures in common promised workflows. Do not require every mouse, clipboard, plugin, terminal-reply or emoji protocol before a narrow release; either implement a measured requirement with native coverage or visibly exclude it from the offer. Reject unsupported authoring input clearly where detectable. Never silently drop actions, strip meaningful output or broaden snapshots to obtain compatibility.

Reproduce Superfile and Glow Windows findings at their recorded pins. Decide whether a general Playtestr fix is warranted, a normally supported target configuration works without weakening assertions, or those exact paths remain unsupported. Do not patch upstream input behavior and claim unmodified Windows compatibility. A planned wider terminal feature is not qualified until its exact path runs successfully.

## R4 — 100-project runner campaign

Maintain a new **runner-readiness** ledger, starting at **0/100 admitted under this expanded contract**. Existing projects can be re-admitted only after satisfying the new public saved-state, authoring, host and candidate requirements. Do not discard their old evidence or count them as new discoveries. Keep the complete paid-product campaign's counter separate at 0/100 until its App/commerce gates exist.

Reuse [08](08-real-project-validation.md) for canonical identities, screening, language/UI/category diversity, native-host distribution, safe setup, fixtures, resource forecasts, fault preservation, holdouts and deletion. For this runner ledger, free CI and provenance apply; the paid App approval requirement does not apply. That exception does not qualify a paid workflow.

Per admitted project:

1. Pin/review trusted source, setup, license, native hosts and ownership before execution.
2. Author at least five useful normal and five distinct edge scenarios, including recorder export/replay and maintenance. Declare platform variants rather than silently skipping cases.
3. Assert rendered state and exact exits; use the new public same-execution assertions for declared file outcomes. Calibrate every used oracle against wrong and missing state. Separate unsupported structured outcomes visibly.
4. Detect at least two real target behavior regressions with unchanged reviewed tests, including a terminal-green saved-data fault where applicable; restore exact source and expectations and prove recovery.
5. Run ten fresh final executions per scenario and qualified host with a predeclared variation schedule. Store original failures and retry denominators separately.
6. Qualify native Linux plus at least one other upstream-supported native OS per project. Across 100 aim for at least thirty Windows and thirty macOS qualifications. Freeze category/host feasibility after screening; any required reduction needs a visible scope decision before admission.
7. Run the ordinary delivered free build/test/report workflow in an owned harness. Revalidate real same-repo/fork event behavior in a small specifically authorized synthetic integration matrix, without creating PRs in upstream projects. Per-project Actions execution must not be called a real PR journey when it is not one.
8. Confirm termination and remove owned application sources, binaries and dependencies; retain compact evidence, recipes and hashes.

Screen reserves first, then advance through 10 → 30 → 60 → 80 → 100. Freeze twenty reserved projects for late assessment; if inspection or a fix consumes one, label it and record its replacement. No maintainer outreach is necessary to test trusted open source.

A new defect triggers reduction → general fix → before/after regression → affected earlier requalification → continued campaign. Maintain development-admitted and final-frozen-qualified counters separately. R5 artifact qualification must cover all accepted scenarios; material runner/build changes invalidate final identities. Historical passes never silently transfer to changed bytes.

## R5 — Downloads match the tested product

Prepare versioned candidate archives from frozen source/build inputs on each claimed native architecture. Keep the existing stable release unchanged. Build once, checksum, extract and run the actual candidate binaries through installation, first-use, saved-state failure/recovery, migration and the final qualified project matrix. Development binaries or cross-compilation do not qualify those archives.

Exercise upgrade/rollback, old spec/report compatibility, source-free binary installation, paths/permissions, help text, examples, generated workflow pinning and offline operation. Ensure the website, README, download labels and capability table describe the same candidate. Unpublished features cannot appear as capabilities of older downloads.

Complete private artifact and installation qualification before requesting publication. An exact prerelease publication, if later authorized, must be followed by download/checksum/install verification from the actual public URLs. A stable label requires the runner gates, honest human-usability status and closure of blocking reliability issues. This plan itself authorizes no release, tag publication or deployment.

## Completion and reporting

Publish a runner-readiness decision with exact candidate identities, actual native runs, 100 project packages, distinct scenarios, repetitions, real faults, same-execution state checks, human/agent measurement boundaries, failure dispositions, exclusions and cleanup receipts. Retain all immutable evidence; fix missing hash/publication coverage without rewriting historical manifests. Bound metadata growth and avoid duplicating whole historical ledgers in each retained result.

The decision distinguishes:

- **Runner engineering readiness:** the supported local/free-CI contract is qualified on exact artifacts.
- **Beginner usability:** directly observed in the stated human sample, or still unmeasured.
- **Commercial readiness:** remains unqualified until P3/P4 and later full-product gates pass.

No arbitrary completion percentage, universal compatibility, zero-flake guarantee, automatic semantic coverage or passive-income claim follows from this campaign. Re-estimate effort after R1 and the first fresh-start journeys; the old paid-roadmap forecast does not include this expanded pre-P3 program.
