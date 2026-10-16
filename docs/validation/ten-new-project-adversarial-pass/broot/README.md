# Broot adversarial development validation

Development qualification complete: thirteen reviewed scenarios passed on native Linux and macOS at `b50d7d8` / run `38518046090`. Each host completed 130 ordinary replays and 130 separate state probes, all three actual source faults, exact restoration and verified owned teardown. The public prepared first-use, rerecord and maintenance routes passed. [Machine-readable results](result.json) retain identities and limits. Final frozen-candidate credit is zero.

The MIT-licensed target is `Canop/broot` at `41cb4c78d9d7736dfe83c65f8a393fc962e50662`, built using owned Rust 1.97.1. `TERM=screen-256color`, `BR_INSTALL=no`, and an explicit synthetic config avoid real shell integration and user configuration. Ordinary Unix `cp`, `mv`, and `mkdir` are upstream built-in external verbs, running with the operator's permissions. No sandbox is claimed.

Six normal workflows cover a spaced Unicode copy, rename and original-path absence, nested directory focus, Unicode preview, nested directory creation, and content search. Seven distinct boundaries cover a genuinely empty directory, no-match recovery followed by useful copying, cancellation without a destination, invalid-verb recovery followed by copying, unsuccessful copying to a missing parent, narrow/wide long-preview navigation with observed redraws, and content search across a generated 501-text-file directory tree. Exact fixture bytes, declared absences, and actual directory types are checked independently before workspace teardown. The oracle checks declared state; it does not prove that every undeclared path is absent.

The [scenario intentions](scenarios.json), public JSON tests, and reviewed snapshots contain the final interaction contracts. Snapshots normally retain rows 2–28, excluding the generated root path and transient footer. The empty-directory case explicitly uses footer rows 29–30, paired with a positive focused-path assertion and independent directory checks. Filesystem checks are campaign functionality, not public runner assertions. The historical prototype remains uncredited.

Actual failed recordings are retained under [local-first-failures](local-first-failures/inventory-12.json). They include guessed captions, filter state hiding a created destination, an incorrectly decoded Unicode checkpoint, ambiguous input text, stale checkpoints, and an intermediate preview-selection snapshot. A selected file's caption is not sufficient when already visible: useful selection markers and newly revealed content are required. The resized preview's final checkpoint now requires `1 ▶line 00:`; matching the text alone admitted an intermediate selection state and failed fresh replay. These are explicit authoring corrections, not additional core fixes.

Broot does not retain the external failed copy's stderr in its resumed final screen. That case verifies command disappearance, resumed tree interaction, destination absence, and intact declared inputs. It does not claim a persistent error-message assertion or that the application propagates the external process's failure as its own exit status.

The [fault definitions](faults/definitions.json) deliberately divert a copy, reverse page navigation, and copy the wrong file's bytes while preserving the expected visible destination. Both visible defects were detected. The third control passed ordinary terminal assertions while its independent byte oracle rejected the wrong copy. All three preserved contracts and restored exact source/binary hashes, followed by passing ordinary and state recovery. [Actual control reports and original failure evidence](local-fault-evidence/manifest-3.json) retain the identities. The first mutation invocation omitted the already-owned Rustup bootstrap environment; the adapter restored source bytes but could not rebuild without that prerequisite. The corrected invocation supplies the existing owned bootstrap explicitly; no system toolchain was installed.

The latest [prepared public route](ux-prepared-route.json) used four commands and seventeen recorder controls, taking 21.231 seconds with reviewed fixtures, warm caches and prior operator knowledge. It excludes acquisition, fixture engineering and earlier authoring corrections; it is not a beginner study. Manual editing changed the destination text and its two explicitly selected checkpoints in a separate JSON test. The resulting snapshot mismatch, HTML diagnosis, named baseline update, ordinary rerun, Unicode/spaced checkout relocation, generated workflow preview and suffix rerecord all passed again. Primary test/baseline bytes remained unchanged. The earlier fifteen-control assessment is archived with its earlier contract. The template is a preview; native execution requires separate successful hosted evidence.

No Windows qualification, shell integration, editor/clipboard/image/network compatibility, full Broot coverage, or independent beginner-usability claim is made. Linux/macOS are the intended additional native runs. The pre-acquisition [scope](scope.md) remains historical: content search replaces a speculative second-panel workflow, and an actual unsuccessful copy replaces an unobserved overwrite/conflict intention. Both replacements preserve useful distinct behaviors and exact state evidence.

First native run `38491057021` at `3d66b95` completed Linux's twelve cases,
120 ordinary plus 120 separate state repetitions, all source controls and
confirmed owned deletion. All three core/race jobs passed the nineteen-test
harness calibration and 82 mapped product controls; standard `38491057052`
passed. macOS failed initial unsuccessful-copy recovery: command disappearance
passed, but Escape did not clear the filter and the subsequent `bravo.txt`
checkpoint timed out. The source's external execution leaves/reenters the
alternate screen; the observed failure is consistent with input arriving
before resumed readiness, rather than proof from event-level instrumentation.
The corrected recipe positively observes the resumed `Hit alt-Enter...` prompt
before disappearance and Escape. Its old contract is retained under
`historical-transient-external-completion`; its final snapshot is unchanged.
The affected local development series was stopped via SIGINT to its exact
verified owned Python process before changing contracts, and a subsequent
process scan found no Broot or recorder remaining. Completed old attempts
remain historical; the interrupted series is not credited as a complete run.
The failed hosted macOS job skipped explicit owned deletion, so no deletion
receipt is claimed for that attempt. Corrected native qualification is pending.

Second macOS run `38492657053` at `d6bc664` passed all twelve initial ordinary
tests, then rejected an ambiguous destination anchor in the normal copy's
independent recorder execution. [The actual first failing recording](first-failures/macos-normal-copy-recorder.json)
is retained. All affected copy/move flows now assert their complete entered
input before Enter, then a positive resumed-view prompt before Escape.
Directory creation now asserts the actual tree branch, rather than the same
name inside its input field. All five revised cases passed recording and fresh
replay, and all five final baseline files are byte-identical to the archived
pre-correction baselines. The public prepared route and maintenance passed
again. New-contract native controls and complete host repetitions are pending;
earlier local source controls apply to their captured historical contracts.

Native run `38493835518` at `74083e4` subsequently passed all five jobs.
Linux/macOS each completed the corrected twelve cases, 120 ordinary and
120 separate state repetitions, all actual source controls with explicit
contract hashes and thirty-second negative budgets, exact restoration and
verified owned application deletion. All three native core/race jobs and
standard `38493835733` passed. The [latest local control package](local-fault-evidence/manifest-6.json)
also requalified the three source faults against these corrected contracts;
the earlier three controls remain distinguishable historical evidence.

The additional `edge-large-tree-content-search` boundary uses 501 text files
in 25 directories plus the explicit configuration: 502 independent exact-byte
checks. The deterministic generator in `adversarial_broot_cases.py` reconstructs
the ignored fixture tree in a fresh checkout; generated files are not retained
as hundreds of source-controlled inputs. Its first recording guessed a full
path where Broot displays the group and selected basename on separate rows;
the corrected actual marker passed recording, review, byte checks and fresh
replay in 100.734 seconds on WSL with OneDrive/DrvFS provenance and copying
overhead. This is measured total harness work, not a claimed startup benchmark.
This thirteenth case is pending native qualification; the twelve-case result
does not grant it credit.

The larger dataset also exposed an inspection gap in the campaign harness:
provenance time previously granted extra command time. A controlled 300-ms
identity delay plus a real 300-ms child incorrectly passed a 500-ms deadline
before the repair. Main execution now consumes the remaining original budget,
and expired provenance cannot launch a child. The reduced control failed before
and passed after; all twenty calibrations passed on Windows/WSL. Synchronous
metadata reads are checked rather than preempted, and cleanup retains its
separate bounded waits. This is a harness repair, not a new terminal capability.

The extended thirteen-case native run `38518046090` at `b50d7d8` passed all five jobs. Linux/macOS each completed 130 ordinary plus 130 separate state repetitions, including the generated large-tree boundary, all three source controls, exact restoration and verified owned deletion. All three core/race jobs passed, including the twenty-test harness calibration; standard run `38518046053` passed. The local exploratory source/toolchain/dependency tree was also removed after pristine-source/process checks. All 502 generated fixture files were checked against their recipe before removal; the generator, reviewed contracts, hashes and [removal receipt](generated-large-fixture-removal.json) remain. The earlier pending statements above describe their historical stages. Final frozen-source batch credit remains zero.

## Final frozen qualification

Final source `e8682f866622442c421005c7f477cd45fcc66fc5` / [run 38802794545](https://github.com/Wyrcan-io/playtestr/actions/runs/38802794545) passed the strict batch audit on Linux, macOS: 130 ordinary plus 130 separate final-group state probes per host, real source-fault/restoration controls and verified owned removal. [Machine receipt](final-frozen-qualification.json). Earlier pending text records development-time status; this receipt qualifies only the stated terminal/state matrix. [Usability limits](../usability-assessment.md) and [remaining limitations](../limitations.md) still apply.
