# R3b — Resolve trial findings and verify the next candidate

Status: technical candidate work complete as of 10 September 2026. Sequencing revised 11 September: [R3c nine-application validation](03c-cross-stack-validation.md) precedes [R4 publication](04-stable-release.md); independent R3 adoption follows publication. Source fixes, rc.1 baseline, rc.2 publication, native checks, release boundaries, six Windows/Linux real-app cells, second sessions, negatives, and exact cleanup remain completed evidence. Created 8 September 2026.

## Outcome

Deliver a candidate whose downloaded binaries can run the supported real-application workflows, whose failures have accurate evidence, and whose remaining limitations have a reviewed disposition. Close the gap between a locally patched runner and a release people can actually install. Carry forward the independent-adoption requirements of [R3](03-real-project-trials.md); this plan does not replace them with internal repetitions.

Execution order: evidence audit → harness correctness → focused compatibility diagnosis → source review and CI → next candidate → downloaded-asset trials → R3c nine-application validation → R4 publication → R3 adoption. Existing completed technical work is not reopened by this planning change. Candidate publication waits for any fixes needed by its declared support boundary.

## Starting evidence and limits

- The [technical report](../../trials/technical-trial-2026-09.md) records all six Windows/Linux client cells and 60 passing final primary attempts. Four earlier Windows Lazydocker primary attempts failed and remain separate. Broader scenarios include unresolved failures; 60/60 is not an all-scenarios compatibility claim.
- Windows trials used published rc.1. Linux successful trials used a checkout-built runner after the controlling-terminal fix. These Linux results do not validate the published rc.1 archive.
- The local Unix fix sets the child PTY as its controlling terminal and has a real `/dev/tty` regression test. Earlier Windows tests, vet, race checks, and the runner suite executed in Ubuntu passed. Record exact revision and command provenance again when selecting the candidate.
- The install workflow change passed a local greeting smoke on Windows Git Bash and Ubuntu. This is less coverage than the entire hosted workflow, and macOS has not been validated by those local runs.
- Git/Docker/Kubernetes postconditions were checked by the operator and private harness. Playtestr has not gained a general external-assertion action. No new snapshot or failure-artifact feature should be attributed to this campaign without a corresponding code change.
- Missing diagnostics, missed input, application exit, and blank final screens do not establish an upstream defect by themselves. Several prior classifications are provisional and require the comparisons below.
- Trial infrastructure was removed. Recreate only dedicated synthetic resources if needed; do not assume old IDs still exist. Preserve private approval records and raw evidence under ignored storage.

## Finding register and closure policy

| Item | Required work | Closure evidence / release decision |
| --- | --- | --- |
| R3-T01: published Linux PTY defect | Review controlling-terminal fix, validate Unix lifecycle behavior, release new bytes | Downloaded candidate runs `/dev/tty` and Lazygit regression checks; old rc.1 limitation stays documented |
| R3-T02: stale text gives misleading mutation passes | Add bounded independent state checks to repeatable recipes; exercise lock, historical YAML, and retained-log failures | Overall harness returns nonzero when state is wrong even if screen steps pass |
| R3-T03: shared dashboard reveals unrelated names | Dedicated endpoint/config and narrowly selected artifacts | Sanitized reproducible recipe; no ambient container data in public evidence |
| R3-T04: Lazygit Linux quit after help/resize | Minimize sequence and compare normal terminal, published runner, patched runner | Fix with regression coverage, or demonstrated target-specific limitation with explicit supported scope |
| R3-T05: unavailable/denied target leaves blank diagnostics | Compare application output, terminal state before exit, and evidence capture timing | Accurate failure category and useful available evidence; documented absence when the target supplies none |
| R3-T06: WSL Docker integration interrupted | Retain endpoint preflight and bounded setup failure | Missing integration prevents mutations and produces setup failure; no daemon restart or endpoint fallback |
| R3-T07: stopped Lazydocker fixture does not start | Confirm selection, documented action, input processing, async completion, and API result | Reproduced cause and correct harness status; never accept retained logs as startup proof |
| R3-T08: Lazydocker Linux help after 80x24 resize | Minimize resize/help/quit and compare manual behavior | Fix verified, or narrowly documented limitation backed by comparison |
| R3-T09: persisted Lazygit commit draft creates a screen false pass | Clear the field, prove dialog closure, and check exact commit/tree externally | Failed oracle attempts retained; corrected candidate workflow passes |
| R2 install-smoke failure | Review PATH/blocker mechanism and execute complete hosted matrix | Passing run tied to workflow commit and downloaded asset hashes |
| Application-regression proof absent | One controlled source regression or known-bad revision with good control | Same test detects intended application behavior change and recovers; complete each qualifying R3 record separately |
| Cross-language and independent use absent | Non-Go technical flow plus qualifying participant review/reuse/CI records | R3's existing gates satisfied with private identities kept private |

A false overall pass, surviving managed process, unintended resource mutation, or broken advertised installation blocks promotion. An unexplained failure affecting a promised workflow also holds that workflow's support decision. A documentation waiver requires evidence of its cause or a conservative scope restriction; unexplained failures cannot simply be called target bugs. Each disposition records owner, reproduction, affected versions/hosts, evidence, and next action.

## Checkpoint 1 — Audit the actual handoff

1. Read the current diff, candidate workflows, trial reports, and [observations](../../trials/observations.md). Inventory tracked changes separately from ignored private evidence. Confirm the approval file is untracked without printing it.
2. Reconcile planned checkpoints against actual evidence. Specifically verify LG-01 unstage, second-session samples, manual baselines, cancellation/readiness/log waits, output-flood diagnostics where feasible, and real-app CI. Mark missing items unexecuted; checked boxes in the previous plan are not proof.
3. Preserve the original 60 final attempts and four earlier primary failures. Distinguish exploratory attempts, final repetitions, setup failures, screen outcomes, external checks, and cleanup. Do not manufacture per-attempt oracle evidence retrospectively; rerun only the missing acceptance evidence when needed.
4. Correct summary chronology and attribution, including the campaign's continuation on 8 September. Record the difference between an observed Linux failure and a confirmed runner or application cause.
5. Record current source commit, dirty patch identity, runner hashes, target versions, host, commands, and artifact locations. Freeze the previously tested target versions for diagnosis. New upstream versions belong to a separately labeled sample.

Deliverable: a coverage/evidence ledger and corrected technical summary. Exit: every earlier completion or improvement claim is supported or explicitly qualified.

## Checkpoint 2 — Make the useful recipes reproducible

Keep orchestration outside the runner core. Add only small reusable scripts/specs that capture proven workflows; do not introduce a new DSL, public plugin system, or database.

- Replace personal paths with explicit workspace/tool inputs. Pin archives and checksums, isolate application configuration, use synthetic identities, and bound setup, polling, execution, output, and cleanup.
- Allocate a unique attempt directory containing the unchanged runner report plus separate harness outcome and postcondition evidence. Keep old adjacent artifacts from being attributed to a later pass.
- Record target identity before input. A filter field containing a name does not prove that the selected row has that identity. Require selection evidence before mutation and verify the exact external resource afterward.
- Git checks must prove the exact index content, commit/tree, branch, and unstage result. With a stale index lock, an unchanged index makes the overall workflow fail.
- Docker checks must distinguish stopped, starting, running, and restart completion. Poll for a changed start timestamp or fixture generation with a deadline. Old logs and transient status labels are insufficient; requiring a fleeting label can also create a false failure.
- Kubernetes checks must inspect live fields and resource UIDs. A matching last-applied annotation must not satisfy the intended ConfigMap postcondition. Verify cancellation preserves the same UID and deletion replaces only the intended pod.
- Add a small meaningful harness regression: a screen-pass paired with a failed external postcondition must yield a nonzero overall result. Preserve both the original runner outcome and cleanup failure if present.
- Use a dedicated Docker endpoint for public dashboard evidence. Do not inspect or mutate unrelated containers, restart Docker Desktop, prune globally, or change the user's active Kubernetes context. Validate recorded IDs/labels before cleanup. If infrastructure is unavailable, report setup failure and continue independent work.

Exit: another operator can reproduce at least one useful flow per app from documented inputs, including a failed postcondition, recovery, and exact cleanup. Public recipes contain no private paths, approval details, credentials, or dashboard snapshots from the shared endpoint.

## Checkpoint 3 — Diagnose the unresolved Linux interactions

### Lazygit help/resize/quit and Lazydocker help/resize

For each application, run the pinned build with isolated config in a normal interactive terminal first. Compare with Playtestr at the same dimensions and state. Establish: plain quit, help then quit, resize without help, help after 80x24 resize, restore 120x40, then quit. Add one transition at a time and retain the shortest failing case.

Check that readiness actually precedes input, the expected pane has focus, Escape does not leave a dialog active, and input bindings match the pinned version. Investigate terminal modes, resize notifications, alternate-screen transitions, process exit timing, and whether cleanup erased an earlier useful screen. Do not assume Ctrl+C has identical meaning in every terminal mode.

If Playtestr differs from the manual baseline, reduce the relevant behavior to a deterministic PTY fixture. Require that regression to fail before the fix and pass afterward, then rerun the real app. If the application behaves the same manually, document the exact version/sequence and available workaround. Do not widen deadlines or replace clean-exit assertions with forced cleanup just to obtain green results.

### Lazydocker stopped-container start

Verify the pinned application's supported start/restart behavior on a dedicated stopped fixture. Check selected row identity independently of filter text, wait for the filter to apply, and ensure the application remains alive long enough to complete the action. Compare the same action manually and under Playtestr.

Separate an unprocessed key, unsupported action, no selected item, missed transient status, asynchronous operation interrupted by early quit, daemon rejection, and successful API transition. Preserve the fixture state before and after each attempt. A direct Docker start can restore the next attempt's fixture but cannot count as a successful TUI start.

Exit: T04, T07, and T08 each have a minimal reproduction and reviewed fix-or-limitation decision. Confirmed runner fixes include appropriate tests/vet/race and native reruns; unresolved promised behavior keeps candidate promotion held.

## Checkpoint 4 — Make negative evidence accurate

Reproduce invalid Docker endpoint, denied Kubernetes identity, and unreachable API using dedicated test config. Verify there is no fallback to an ambient endpoint. Compare normal application behavior with the captured rendered screen and exact exit status.

Inspect whether useful text existed before clear/alternate-screen exit or whether cleanup overwrote the evidence. If Playtestr loses meaningful rendered state, implement the smallest evidence-retention fix and a deterministic regression. Preserve the distinction between the screen at failure and an earlier retained screen; update public artifact documentation/tests if behavior changes.

If the application never renders an error, record that fact and keep a truthful bounded result. Do not infer success from exit zero or quiet output. Private target logs may help diagnosis but are not automatically suitable for a new public artifact channel. Avoid unrestricted raw-output capture or secret-bearing environment dumps.

Exit: each negative case records the target's behavior, runner category, available screen evidence, and cleanup result. Any missing diagnostic has an explicit reason or an open investigation, not an invented explanation.

## Checkpoint 5 — Review, commit, push, and restore hosted installation proof

Prepare reviewable changes by purpose: runner fix/tests, sanitized trial recipes/evidence, and install workflow. Run checks appropriate to the final diff, including native Unix coverage for the shared non-Windows process setup; Windows passing alone cannot validate that change on macOS.

Before an authorized push, review all selected files for privacy and confirm branch/remote. Preserve unrelated changes. Record commit IDs and actual Actions run URLs/results. This planning request performs no commit, push, workflow dispatch, tag creation, release publication, or outreach.

Audit the local install workflow proposal before calling it fixed:

- Preserve paths required by PowerShell/ConPTY and target runtimes.
- Confirm the blocker wins lookup in each actual execution context. A shell script that shadows `go` in Git Bash does not necessarily block native Windows `go.exe` discovery, absolute paths, or alternate Go installations. State the guarantee precisely; improve the check if stronger no-Go evidence is required.
- A blocker sentinel proves that particular lookup is disabled. It does not prove Go is uninstalled from the host. Where practical, use a minimal environment without a toolchain for stronger evidence, without stripping target runtime prerequisites.
- Clear relevant Go environment variables only as needed; retain a valid target environment. Check that workflow cleanup remains scoped to its own workspace.

After the reviewed workflow is pushed, manually dispatch **Published install smoke** for `v0.1.0-rc.1` on that workflow revision. Push alone does not trigger this workflow. Verify Linux amd64, Windows amd64, and macOS arm64 results, including checksum corruption rejection, extraction into a spaced path, version/help, good → bad → recovered run, missing target, invalid spec without sentinel execution, and report-write failure. Preserve artifacts even on failure and record the actual failing layer.

A passing rc.1 installation test closes the workflow repair only. It cannot close rc.1's `/dev/tty` defect. If the hosted run still fails, inspect its first substantive failure and fix that cause before rerunning; retain the failed run instead of retrying to hide instability.

Exit: complete hosted installation matrix tied to the reviewed workflow and exact rc.1 assets, with remaining candidate defects stated separately.

## Checkpoint 6 — Prepare and publish the next candidate

Use `v0.1.0-rc.2` only if it is still unused when execution starts; otherwise choose the next unused candidate version. Never replace existing release bytes or move a published tag.

1. Freeze the reviewed source commit after in-scope runner fixes and compatibility decisions. Record spec/report versions and migration impact; do not bundle future sprint features.
2. Review `.github/workflows/release-candidate.yml` and the packaging command against the R1 release contract. Verify version injection, supported architecture matrix, checksum files, notices, and archive layout.
3. Run appropriate unit/integration tests, vet, race tests for lifecycle changes, and native extracted-archive checks on each advertised host. Record missing infrastructure as missing evidence.
4. Prepare candidate notes explaining the controlling-terminal fix, affected rc.1 Linux behavior, confirmed other fixes, and exact remaining limitations. Review README, support table, compatibility notes, and website wording for agreement.
5. Prepare the exact tag/commit, asset manifest, and release notes for review. Publish only with session authorization for that action. Stable-release authorization is separate.
6. Download the public candidate assets afresh, verify checksums, and assert the embedded version. Retain archive/binary hashes and workflow/source provenance.

Exit: immutable candidate assets exist and their source, version, hashes, and support scope agree. A successful source build is insufficient.

## Checkpoint 7 — Validate downloaded candidate bytes

Run the complete **Published install smoke** matrix for the new version. Add a bounded published-binary controlling-terminal check so a simple shell greeting cannot miss the original Linux regression again. Validate the non-Windows change on macOS as well as Linux.

Using downloaded assets rather than a checkout-built runner:

- Rerun pinned Lazygit stage/unstage, commit, branch, and the diagnosed help/resize/exit sequence on Linux. Verify `/dev/tty` startup and Git postconditions.
- Rerun Lazydocker logs, stop/start, restart timestamp, resize/help, and negative endpoint cases with dedicated resources. Apply documented exclusions explicitly; do not silently skip them as passes.
- Rerun K9s logs, live YAML, controlled delete/cancel, resize, empty namespace, and negative APIs. Verify exact UIDs and cleanup.
- Revalidate Windows real-app primary paths with the new asset and appropriate Unix/macOS runner regression coverage. Do not claim macOS real-app compatibility unless those real-app paths run.
- Repeat the corrected primary workflow ten times for each of the six client cells with per-attempt external checks and no hidden retries. Keep this candidate sample separate from the historical checkout sample. Run a second session on both hosts and verify state reset.
- Confirm cancellation, total timeout, output limits, natural exit, and descendant cleanup through the release fixtures; add real-app cases where the evidence audit found a relevant gap. Verify evidence and harness statuses, not just CLI exit codes.

If code changes after this freeze, associate reruns with the new revision and publish a new candidate when already-published bytes change. Do not attach old green results to new binaries.

Exit: candidate-specific installation and real-app evidence matrix, including expected failures, external postconditions, cleanup, and limitations. Every supported required path passes; remaining exclusions have a reviewed release decision.

## Checkpoint 8 — Demonstrate application-regression value and complete R3

First prove one useful application regression with a bounded experiment. Prefer a documented known-bad revision; otherwise make a small reversible mutation in a separate pinned source checkout that changes the selected user-visible behavior. Build an unmodified control with the same toolchain. Preserve patch, source IDs, hashes, and good → bad → restored evidence. The bad build must launch and reach the intended behavior; compilation errors, absent executables, altered expected text, or changing only fixture data do not satisfy this experiment. A local mutation is labeled synthetic and never attributed as an upstream bug.

Extend this proof to each qualifying R3 project record as required by that plan. Do not search indefinitely for a historical upstream regression when a transparent local mutation can test the same user task.

Choose one authorized non-Go application with a valuable repeatable flow, ideally one that writes a small configuration result. Select it for the user's task and accessible runtime, not language count alone. Pin its version and test its actual host with a downloaded candidate, external result check, failure/recovery, and repeated use. This supplies technical stack diversity; it is not independent adoption by itself.

Prepare the participant kit around the tested candidate and narrow recipes. Record three qualifying completed project trials across at least two stacks, participant review/understanding of failure evidence, at least two voluntary second uses, and at least one project CI integration. Record assistance and setup friction. Names and consent references stay private unless publication is explicitly allowed. User-reported permission to test does not itself prove these outcomes. Prepare outreach material without sending messages unless specifically authorized.

Exit: technical proof is complete; parent R3 participant gates remain visibly pending until the post-publication program. The 11 September sequencing decision transfers their timing, not their completion. R3c now owns the additional three-per-ecosystem technical requirement before publication.

## Checkpoint 9 — R4 handoff decision

Produce one short readiness record containing candidate tag/commit/hashes, hosted run links, native coverage, scenario/sample results, corrected historical counts, resolved findings, accepted limitations, cleanup evidence, participant gates, and named release owner. Link supporting evidence without publishing private artifacts.

Give each finding one status: fixed and verified in candidate bytes; demonstrated limitation accepted within narrowed support; deferred outside supported scope; or unresolved blocker. Include a reason and owner for each non-fixed item.

R4 publication requires this plan's technical checklist and R3c closure. Independent participant review/reuse/CI follows publication under R3. Stable packaging, contract audit, maintenance policy, website download changes, publication, and the first independent stable run remain in R4. Its install-smoke controlling-terminal gate must stay enabled for v0.1.0.

## Definition of done

- [x] Earlier claims/checkpoints reconciled against evidence; missing coverage recorded and addressed.
- [x] Reusable recipes fail overall on incorrect external state and preserve runner/harness/cleanup outcomes.
- [x] T01–T09 have evidence-backed dispositions; the compact Lazydocker exclusion and commit-draft synchronization are explicit.
- [x] Reviewed source changes committed/pushed with authorization and passing applicable CI.
- [x] Repaired full rc.1 hosted installation matrix verified; the shell-lookup claim matches what was actually tested.
- [x] Next candidate published with authorization, immutable provenance, and native artifact checks.
- [x] Downloaded candidate passes the controlling-terminal regression and the complete supported Windows/Linux real-app matrix, including Lazygit, Lazydocker, and K9s.
- [x] Completed candidate repetitions are recorded separately from historical 60/60, setup failures, and earlier failures.
- [x] Real application-regression experiment and cross-language technical coverage completed.
- [ ] Transferred to post-publication R3: independent review, repeat-use, and participant CI gates have actual records (still uncompleted; no longer an R3b technical exit gate).
- [x] Historical and candidate-owned resources were cleaned by verified exact identity; the named kind cluster was also removed with absence confirmed.
- [x] Public docs are accurate and sanitized; the R4 readiness record visibly retains its blockers.

This is a bounded release-readiness plan. General external-assertion APIs, new artifact formats, hosted dashboards, broad terminal-emulator rewrites, and later sprint features require separate evidence and scope decisions.
