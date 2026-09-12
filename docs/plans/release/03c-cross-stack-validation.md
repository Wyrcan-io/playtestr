# R3c — Validate nine real applications before stable

Status: complete, 12 September 2026. Nine applications, 18 intended Windows/WSL Linux cells, and 54/54 frozen primary attempts are recorded in the [cross-stack validation record](../../trials/cross-stack-validation-2026-09.md). Owner: Playtestr maintainer. Depends on the completed technical evidence in [R3b](03b-trial-findings-and-candidate-readiness.md). R4 accepted this technical entry, refreshed the nine workflows against stable bytes, and published v0.1.0; independent [R3 adoption](03-real-project-trials.md) now follows.

## Outcome and boundary

Demonstrate that the downloaded release candidate protects useful interactions in three Python, three Rust, and three Node.js applications. Find runner defects, misleading assertions, and excessive authoring effort before stable publication. Nine repositories is the fixed initial scope; language count alone is not the acceptance criterion.

Use nine distinct, existing applications with real user tasks. Framework examples, forks of the same application, generated demo programs, and three front ends exercising the same underlying program cannot fill multiple slots. The existing Go campaign and IPython experiment remain valid historical evidence; neither is silently counted as a new completed trial. IPython may fill one Python slot only if selected and rerun against this plan's full acceptance boundary.

This work produces small specs, external oracles, sanitized recipes, and evidence. It does not introduce SDKs, a new spec language, general plugin APIs, hosted infrastructure, or Sprints 5–10. Target runtimes may differ; Playtestr's core stays Go. Human reviews, reuse, and participant-owned CI remain separately measured after stable.

## Checkpoint 1 — Select useful applications

Start with the private approved repository list without copying identities, permission details, or contact information into public files. Verify the current official repository, released versions, license, installation path, runtime requirements, and upstream Windows/Linux support when execution starts. Record source URLs and retrieval date. Do not infer current versions or frameworks from memory.

The following are selection slots, not claims about selected repositories. Choose concrete repositories during the selection checkpoint and freeze the roster before the full campaign. Record why each task matters and how it differs from other slots.

| Slot | Preferred interaction | User task | Independent evidence | Distinct behavior to exercise |
| --- | --- | --- | --- | --- |
| PY-01 | Textual-style full-screen application | Open synthetic data, filter/select a result, inspect detail, return | Known fixture record and selected content; exported result if supported | Focus, modal closure, redraw, resize |
| PY-02 | prompt-toolkit-style interactive application | Edit input and execute a command that writes a small result | Exact output file bytes or structured value | Line editing, completion/history if integral, Unicode input |
| PY-03 | A different Python interaction or terminal backend | Transform/export a tiny table or complete a configuration task | Parsed export/configuration with exact expected fields | Validation, cancellation, persisted settings |
| RS-01 | Ratatui/Crossterm-style full-screen application | Navigate/search a fixture and select a known result | Fixture identity and selected data; file output if available | Alternate screen, selection, help and resize |
| RS-02 | Rust interactive file/content tool | Edit or save one synthetic file | Exact bytes plus unchanged neighboring fixture files | Paths with spaces, save/cancel, input modes |
| RS-03 | Rust selector/prompt application | Select among known choices and accept/cancel | Exact selected value or generated configuration | Prompt completion, natural exit, cancellation |
| JS-01 | Ink-style Node.js application | Complete a wizard using synthetic inputs | Exact generated configuration or file tree | Multi-step prompts, validation, back navigation |
| JS-02 | Node.js full-screen application with a different backend | Search/navigate local fixture content and open detail | Known selected content or exported result | Focus, redraw, resize, clean exit |
| JS-03 | Node.js interactive selector or command application | Choose a local fixture item and produce a result | Exact output/result file | Keyboard navigation, cancellation, process wrappers |

Prefer at least two terminal interaction implementations per ecosystem where practical. A specific framework is a selection preference, not a gate that justifies using an irrelevant toy. Prefer offline tasks without accounts, external services, or live changing data. Favor applications usable natively on Windows and Linux. If a preferred framework cannot provide an eligible application, document the substitution and retain three useful repositories for that ecosystem.

Each selection record includes: trial ID, private permission reference where applicable, public repository URL only if publication is allowed, task, runtime/framework evidence, upstream host support, install commands, likely fixture/oracle, and estimated setup cost. Inspect installation scripts before running them during implementation. Missing permission for a proposed external action does not authorize outreach or remote writes.

Timebox initial feasibility to approximately 45 minutes per candidate. Permit one focused follow-up of similar size if it can resolve a specific prerequisite. Then either qualify, mark blocked, or replace with a reason. Retain rejected candidates and failures in the ledger. Do not replace a target simply because it exposed a Playtestr defect. Select at most one reserve per ecosystem initially; avoid an endless repository search.

Exit: nine eligible application records, three per ecosystem, each with a concrete task and observable result. Repository names need not be public if permission does not allow association.

## Checkpoint 2 — Freeze provenance and the host matrix

Start with publicly downloaded `v0.1.0-rc.2` and verified checksums. For each target freeze the release/commit, archive or source checksum, dependency lock where available, runtime version, configuration, locale, dimensions, and installation method. Use the latest suitable stable application release verified at selection time; record a reason for an older pin. Do not automatically upgrade dependencies halfway through the campaign.

Plan Windows amd64/ConPTY and Linux amd64/Unix PTY for each of the nine applications: 18 intended cells. WSL Linux results must be labeled WSL Linux, not native Windows or every Linux distribution. macOS real-app testing is outside this campaign; retain its existing native runner/package/install checks.

Every cell has one status: planned, setup-blocked, upstream-unsupported, running, passed, failed, or accepted narrow limitation. WSL running a target is not proof of its Windows support. Prefer a replacement before roster freeze when Windows support is absent. If no suitable dual-host application exists, keep a useful Linux application only with an explicit scope decision in the handoff: all nine must execute on at least one eligible host, and all intended supported cells must complete. Never report 18/18 if fewer ran. An unexplained failure on an upstream-supported host remains a failure.

Record binary hashes per host, source revision, and report locations. A checkout build can diagnose a defect but cannot replace final downloaded-candidate evidence.

## Checkpoint 3 — Prepare isolated fixtures and one manual baseline

Allocate per-target/per-host directories for installation, configuration, fixtures, and attempts beneath the ignored trial root. Use virtual environments for Python, local package installations/locked dependencies for Node.js, and pinned binaries or a separate build directory for Rust. Avoid global configuration changes and ambient personal accounts. Record toolchain prerequisites separately from the standalone Playtestr binary.

Use tiny synthetic data with a unique marker, spaces in at least one path, and a known Unicode value where the task supports it. Snapshot the initial file manifest or relevant hashes before mutation. Define an exact reset procedure and restrict cleanup to verified resolved paths beneath the trial root.

Run the intended task manually once on each supported host. Record actual keys, focus, expected result, clean-exit method, and relevant resize behavior. No automated failure becomes an upstream defect merely because a manual baseline is missing. If manual interaction cannot run in available infrastructure, record the missing comparison and avoid unsupported attribution.

Do not require Docker or Kubernetes for these local application tasks. If a selected workflow truly needs a service, justify it before setup, use dedicated synthetic resources, and follow existing ownership checks. Never restart host services or inspect unrelated containers to unblock a trial.

Exit: repeatable setup/reset, working manual baseline, and known external result for each eligible cell.

## Checkpoint 4 — Implement a narrow acceptance slice per application

Complete the first useful flow before adding edge cases. Target roughly 5–20 meaningful spec steps; justify longer flows. Prefer positive readiness after input, modal-disappearance checks, and bounded state polling over fixed sleeps. Reuse [trial recipes](../../../trials/recipes.md) and the existing harness where applicable.

| Acceptance case | Required proof | Failure classification |
| --- | --- | --- |
| Primary useful task | Intended result, accurate runner status, natural exit where appropriate | Runner result and independent result recorded separately |
| External postcondition | Exact output/state when task mutates; read-only tasks use a unique known fixture/result identity | Screen pass with wrong external state fails overall |
| Intentional fault | One controlled missing/changed fixture or invalid input fails at the intended assertion/result | Label fixture faults accurately; launch failure is not regression detection |
| Recovery | Restore only controlled state; same spec passes again | Preserve the failed attempt and recovery separately |
| User cancel/invalid input | Correct cancellation or validation behavior; no unintended file/state changes | Do not equate application cancel with runner cancellation |
| Runner cancellation | Cancel after positive target readiness; bounded runner result and descendant cleanup | Keep cleanup outcome separate from initiating failure |
| Fresh second session | Recreate/reset configuration, rerun task, verify result | Operator repeatability, not voluntary participant reuse |
| Relevant terminal behavior | Full-screen: 120x40 → 80x24 → 120x40 with assertions and clean exit; prompts: meaningful line editing and Unicode | Unsupported size/backend limitation must be explicit |

Each application needs a small known-good → bad → restored behavior experiment. Fixture faults demonstrate assertion sensitivity but do not prove application-regression detection. In addition, choose one application per ecosystem for a reversible, user-visible source mutation or documented known-bad revision. The bad binary must launch and fail at the intended behavior with the same spec and oracle. Keep source changes in separate target checkouts, preserve patch/build hashes, and never attribute a synthetic mutation to upstream.

Reuse the existing deterministic release fixtures for timeout, output flood, and descendant cleanup. Do not force every unrelated application to manufacture all those behaviors. Add an application-specific case when its flow exposes a relevant gap such as an editor/helper child or long-running command. All processes, reads, polls, reports, and cleanup remain bounded.

## Checkpoint 5 — Repeat with honest denominators

Once a cell's spec and reset are settled, freeze them and perform three consecutive primary attempts with an independent result check each time. This yields 54 planned primary attempts for 18 eligible cells. Report actual cells and denominators if upstream platform exclusions reduce that matrix. Use unique attempt directories and no automatic retries.

Keep exploratory failures, expected-negative cases, regression experiments, and second sessions separate. Any primary failure stays in the sample. Diagnose it, fix the smallest relevant cause, and if a new final sample is warranted, label its new revision and preserve the prior sample. Do not aggregate successful retries into an apparently perfect result.

Three attempts are a bounded repeatability check, not a statistical reliability claim. Increase a problematic cell to ten only when a reproduced timing/state issue makes that useful. Do not rerun the prior Go 60/60 campaign merely to inflate counts.

## Checkpoint 6 — Diagnose findings and manage candidate changes

Classify failures as installation/runtime prerequisite, target behavior, spec synchronization, external oracle, Playtestr terminal rendering/input, lifecycle/cleanup, or documentation friction. Record elapsed setup/authoring time, manual intervention, custom scripting required, and evidence-reading difficulty. These operator observations inform later work but are not participant feedback.

Use focused comparisons against the same manual baseline and pinned target. Reduce suspected runner defects to deterministic PTY fixtures, prove the regression before the fix, and run appropriate tests, vet, race checks, and native coverage. Avoid a general terminal rewrite based on one unsupported sequence.

| Finding | Decision |
| --- | --- |
| False overall pass, surviving descendants, unintended mutation, broken advertised installation | Block publication; fix and verify candidate bytes |
| Supported workflow fails without explanation | Keep the cell failed and investigate; no blanket waiver |
| Proven upstream host limitation | Record unsupported host and restrict claims; roster decision remains explicit |
| Narrow rendering/workflow limitation with evidence | Describe exact version/host/sequence and workaround; owner records acceptance of narrowed scope |
| Harness-only oracle or setup error | Correct harness and rerun affected evidence; preserve original failure |
| Repeated costly authoring or state reset | Document a concrete future sprint input; implement only a small fix needed for this trial |

If Playtestr binary behavior changes, publish the next unused candidate with execution-phase authorization; never overwrite rc.2. Rerun native package/public-install checks and regressions on the downloaded new bytes. Refresh the nine-app primary/fault/recovery checks on every eligible cell and any affected broader paths. For shared PTY/input/lifecycle changes, refresh all affected Windows/Linux Go application paths as well. Record the impact decision; evidence from older bytes stays historical.

If only recipes/docs change, rerun the affected scenarios and documentation checks without inventing a new binary requirement. Freeze the final candidate after fixes and before the R4 handoff.

## Checkpoint 7 — Record evidence and decide R4 readiness

Extend existing records rather than creating a second report system. Store private raw evidence under ignored storage. Public records use anonymous IDs where association is restricted; do not publish contact details, local personal paths, credentials, or unreviewed terminal captures.

For each cell retain: app/version/runtime, host, runner tag/source/hash, setup/reset instructions, manual baseline, exact spec/oracle revision, scenario ID, expected result, actual runner category and exit, postcondition, bounded cleanup result, artifact paths, and failed/recovered attempt history. For mutations also retain starting and final state identity. Record postcondition command exit failures explicitly; empty output is not proof of absence.

Deliverables during execution:

- Nine project technical records and a compact matrix linked from the existing evidence ledger.
- Reproducible sanitized setup/spec/oracle recipes for the selected tasks.
- Three application-regression experiments, one per ecosystem, clearly separated from fixture faults.
- A findings list with fixes, accepted limitations, open blockers, and measured authoring friction.
- Updated candidate readiness and support wording tied to exact tested versions/hosts.
- Verified cleanup of trial-owned state and processes; retained evidence remains private.

Exit: nine completed real application trials (three per ecosystem), every eligible supported cell meets the acceptance slice, failed attempts are accounted for, no unresolved publication blocker, and candidate provenance is current. The owner records any platform exclusions. Stable publication still requires R4's own contract audit and actual stable-byte verification.

## Execution order and checkpoint demonstrations

1. Select all nine and freeze the matrix; do no full campaign work until tasks and oracles are concrete.
2. Finish PY-01, RS-01, and JS-01 one at a time through primary, fault, recovery, and second session. Demonstrate each before broadening.
3. Complete the remaining six in small application-sized increments, reusing only proven harness pieces.
4. Run frozen samples and the three application-regression experiments; resolve findings as they arise.
5. Refresh candidate bytes if required, reconcile all evidence, and make the explicit R4 handoff.

Stop expanding at nine. A blocked application does not halt independent eligible work, but a correctness defect cannot be hidden by swapping applications. Planning does not download targets, run trials, mutate source, publish releases, contact maintainers, or change CI.

## Definition of done

- [x] Nine distinct eligible applications selected: three Python, three Rust, three Node.js.
- [x] Version/runtime/host support checked and pinned; intended 18-cell matrix has explicit dispositions.
- [x] Useful flow, fault/recovery, relevant edge cases, external result, cancellation/cleanup, and second session recorded per eligible cell.
- [x] Three-attempt primary samples complete; earlier failures and revisions are accounted for, including one explicitly recorded pre-sample raw-evidence overwrite.
- [x] One real application good/bad/restored experiment per ecosystem completed.
- [x] No runner defect requiring candidate replacement was found; accepted observations are narrow and evidenced.
- [x] Private evidence retained, public records sanitized, and exact cleanup verified.
- [x] Candidate readiness updated and R4 technical entry accepted.

After R4 publication, execute the existing R3 participant program with the stable download. Three independent reviews across two stacks, two voluntary second uses, and one successful participant-owned CI integration remain open until observed. That later evidence selects Sprint 5 scope; these nine operator trials cannot satisfy it.
