# Git Town development checkpoint

The v3 source-development run (`41879628387`) established exact spec bytes and
passed all 20 frozen Windows cases; Ubuntu failed all 20 with blank screens.
The follow-up run (`41881662967`) shows why: the direct PTY probe exited 0 with
195 bytes of expected output, while `pty.fork()` with a controlling terminal
received only `OSC 11;?` and `CSI 6 n`, then timed out. Cleanup confirmed the
Linux process group absent. The run still has zero scenario/native-cell credit.

Current source change: pass only vt10x-generated bounded device-attributes,
device-status, cursor-position, and default-color responses through the Unix PTY
writer. The reply collector rejects malformed and unselected response shapes.
A real-PTY test now mixes repeated query families, regular key input, and
unsupported palette queries. The full runner and VT package suites passed on
native Windows in 153 seconds after rerunning outside the sandboxed Windows temp
path; final parser checks and `go vet` also pass. The new regression's real Unix
PTY path is skipped on Windows. The Git Town workflow runs both ordinary and
`-race` package suites on native Ubuntu before repeating the 20 cases. Hosted
Linux validation remains pending; no scenario or qualification credit is
claimed yet.


Run `41897622026` (commit `28b09fd`) is preserved as hosted attempt v4. Ubuntu
verified the source build and exact catalog but failed before any scenario in
`TestTerminalReplyTransportErrorIsPreservedWithRealTarget`: its injected PTY
wrapper looked only for a DA reply at the start of a combined batch, now led by
OSC 10. Windows passed all twenty exact cases. Artifacts and dispositions are
in `hosted-development-attempts-v4.json`. The Unix-only test wrapper was fixed
to detect the DA response anywhere in the batch. Native Linux ordinary/race
checks and scenarios remain pending; no credit was added.


Corrected run `41898559438` on commit `ad3da7e` passed the full runner and VT
package suites on native Ubuntu (ordinary and race), ran the bounded direct and
controlling-TTY probes, and passed all 20 exact v3 cases on both Ubuntu 24.04 and
Windows 2025. All 40 case runners exited 0; each report SHA is indexed in
`hosted-development-attempts-v5.json`. The controlling-TTY diagnostic still
captured Git Town's 12-byte `OSC 11`/`CSI 6 n` wait and confirmed process-group
cleanup; the runner regression now returns those emulator-generated replies.
Linux and Windows artifact ZIPs are retained with their digests in the v5
record. This remains source-development evidence: Git Town has zero project
qualification, current-candidate or native-cell credit. Fault detection, public
authoring, maintenance, relocation, repeated candidate series, and final cleanup
audit remain open.

Three source mutations are predeclared in
[`fault-declaration-v1.json`](fault-declaration-v1.json), with unchanged specs
for parent output, feature branch creation, and prototype state persistence. The
hosted workflow invokes the bounded mutation/build/detect/restore/rebuild helper
on both hosts. It verifies the pinned commit and clean source tree before
building, retains a receipt per phase, restores source even when a corrupted
phase fails, and grants no credit until hosted outcomes and evidence are audited.

The local rehearsal was refused after discovering the available `src` path was
not the pinned Git Town checkout; an immutable refusal receipt is retained. An
earlier helper attempt failed during Go build VCS inspection before any Git Town
executable ran; it is retained as a harness failure with zero target or
qualification credit. Neither event changes the successful hosted v5 source
development evidence.

Next Git Town gates: complete and audit the hosted fault matrix; attempt the
no-handwritten-spec recorder route, selected maintenance, Unicode/spaced-path
relocation, and free-workflow delivery; then run the twelve-repetition exact
final-candidate cell and applicable calibration. No project admission, native
cell, or final-series credit is claimed yet.


Git Town source-development and public authoring update (5 November 2026):

- Native source-development run `41947116665` on `6c52fe6deabd74a217599be5a58eee0baf760a2e` passed Ubuntu 24.04 and Windows 2025. Each host verified the 4,533-file exact source pin, built Git Town 24.1.0 with Go 1.27.0/vendored modules, passed all 20 catalog-v3 public scenarios, and passed all nine fault phases (three unchanged-contract mutations and three restored-source rebuild recoveries). Linux query-bridge and race checks passed; the target/process and workspace cleanup checks passed.
- Independent audit request v14 was executed by run `41949100190` after correcting a workflow path mismatch. It audited run `41947116665`, fetched both original provider artifacts, independently checked 40 public reports and 18 source-fault calibration reports, exact source/spec/executable identities, exits and cleanup, then retained the curated packets. Provider artifact ZIPs were 167,184,094 bytes (Linux) and 169,830,019 bytes (Windows); curated retained packets are 9,210,835 and 402,655 bytes respectively, within the 64 MiB combined cap. Receipt is `retention-readback-v14.json`.
- A preceding audit workflow attempt (`41948736271`) gated on request v14 but invoked the stale v13 request; its successful output audited run `41935126990`, not the requested run. It is retained as a misconfigured audit attempt and earns no Git Town credit. The corrected run/receipt binds to the requested head.
- Repeat source-development run `41948227877` on `09db6bd07c3a715ed54e0a9ae051e667e29f11a2` passed both hosts again; it is additional source evidence, not another unique project or final-candidate repetition.
- The generated public first-use authoring workflow passed run `41948227863` on hosted Ubuntu after the original push-context failure. The corrected helper recorded `event=push`, exact checkout SHA `09db6bd07c3a715ed54e0a9ae051e667e29f11a2`, four passing steps, target exit 0, confirmed process exit and fixture removal. Artifact 13378953789 (5,040 bytes; SHA-256 `54f9aeba56d517e923dd6e446d8fa2dc45097aea41811a1ca4e0df30d80d0cd3`) was downloaded and checked. The prior run `41947116756` remains a failure before test execution, with cleanup successful.
- The push context fix is bounded to the supported event set (`local`, `push`, `pull_request`, `workflow_dispatch`); push evidence binds the exact `GITHUB_SHA`, and privileged/unknown events remain rejected. Focused helper tests passed 3/3.

These observations are source-development and authored-user-flow evidence only. They do not qualify the exact frozen private candidate, do not complete the 12 x 20 final series, and add no project admission or candidate qualification credit.


Exact-candidate preflight: native Windows local run of v0.4.0-rc.6/N01 (`0e64475632234057b757324f6ede884e`) was refused during workspace setup with `expand native workspace path: Access is denied.` No target process started; the test has zero candidate or project credit. The attempt is preserved in `candidate-smoke-attempts-v1.json`; the declared standard `windows-2025` final cell remains required.

First hosted exact-candidate attempt (5 November 2026): workflow run
`41953084178` installed the exact frozen RC6 candidate and successfully verified
and built Git Town, generated the synthetic repository, and materialized the
frozen host contracts on Linux and Windows. The final-series wrapper was invoked
with a 3,300-second limit, above `next20_check.py`'s 1,200-second cap, so the
helper rejected it before launching the final-series program or any candidate
target scenario. Both jobs correctly remain failed and receive zero candidate
ordinary, calibration, or admission credit. The downstream cleanup checks also
failed because no target reports existed for report-based cleanup proof; explicit
source/runtime removal was not verified for that failed attempt. Hosted process
proof passed on Windows. Provider artifacts and complete extracted packet
inventories are recorded in `final-series-attempts-v1.json` and preserved under
the campaign raw retention root. Immutable declaration v2 sets the wrapper to
the helper maximum, binds changed harness bytes, and preserves v1. A new full
Linux/Windows run and independent packet audit are still required.

Second hosted attempt `41954388734` used declaration v2 and the corrected
1,200-second wrapper bound. Both hosts installed the exact candidate, built the
pinned application, generated the fixture, and materialized the same frozen
contracts. The final harness hash check then refused before launching any
candidate target test: Linux found a raw-byte mismatch in
`readiness_evidence.py`; Windows found one in the workflow YAML, consistent with
LF/CRLF checkout conversion. Candidate executions and source-fault phases remain
zero, and report-based cleanup again could not prove source/runtime removal.
Windows process proof passed. Packet artifact digests, extracted inventories,
event identities, and dispositions are in `final-series-attempts-v2.json`.
Declaration v3 now normalizes line endings for text harness hashes and preserves
v1/v2 unchanged. The next native run must pass its full declaration gate before
the exact 12 x 20 series can start.

Third attempt `41955366681` confirmed the LF/CRLF normalization but exposed a
separate declaration-input error: v3 hashed the dirty local `readiness_evidence.py`
while the workflow checked out the committed blob. Both native cells refused at
the final harness gate; candidate ordinary/calibration launches remain zero.
Windows process proof passed; cleanup could not use report-based proof because
there were no target reports. Full packet inventories and attempt IDs are
preserved in `final-series-attempts-v3.json`. V4 derives hashes from the Git
index after explicitly staging the final-series consumer and generator, then
compares normalized working-tree bytes on the runners. The next two-host run is
the first eligible attempt to start candidate scenarios.


Fourth exact-candidate attempt `41956408435` passed the v4 staged-blob hash gate
and started real RC6 cases. Linux timed out on its first cold N01 checkpoint at
the default 3,000 ms with an empty captured screen; target process-group and
workspace cleanup were positively confirmed. Windows passed the first 12
selected cases, then N15 rejected a saved-state mismatch after the target
displayed `feat-Ã©` while the frozen state expected `feat-é`. Both host jobs
failed, no complete batch or candidate credit was earned, and report-based
target cleanup could not finish because the common cleanup verifier requires
the pinned `source.tar.gz`, absent from the Git-checkout acquisition path.

The full packets (Linux artifact `13382803190`, Windows artifact `13384125287`)
and extracted inventories are preserved in
[`final-series-attempts-v4.json`](final-series-attempts-v4.json) and under the
raw retained directory named in that record. V5 raises only N01's declared
checkpoint to 10,000 ms and changes N15 to a Unicode branch-selection scenario
using a separately seeded local fixture; it does not erase the observed
Windows command-line conversion failure. V5 is declared to acquire the pinned
source archive by its existing reviewed SHA-256 and retain it in the cleanup packet.
The new v5 catalog/freeze and staged-harness declaration remain zero-credit
until both hosted cells, complete repeated series, source-fault calibration,
independent audit, and checked source/runtime removal pass.


Fifth exact-candidate attempt `41960284415` installed RC6 and checked out the
pinned Git Town commit on both hosts, then failed during preparation because
the downloaded codeload archive bytes did not match the historical reviewed
archive digest. No Git Town build, candidate scenario, or source-fault phase
started. Cleanup was skipped because the preparation step failed; no checked
source/runtime removal is claimed. The provider packets and extracted
inventories are preserved in [`final-series-attempts-v5.json`](final-series-attempts-v5.json).

V6 constructs a deterministic gzip/PAX archive from the already verified
4,533-file pinned checkout, reopens it and verifies every member byte against
the source provenance manifest, records its generated digest, and adds tests
for repeatability and partial-output cleanup. The codeload mismatch remains a
preserved acquisition failure. V6 still has zero candidate credit until the
full Linux/Windows series and audit complete.


Sixth final-series run `41962045773` verified the generated pinned-source
archive on both native hosts and installed the exact candidate. Before the
first target case, the final journal failed because
`next20_jrnl_final.py` reads `host-contracts/scenarios.json` while the v2 freeze
only materialized `scenarios-native-exit-v2.json`. No final target case or
fault calibration launched. Cleanup checks could not prove target report
cleanup, so source/runtime removal is not claimed. Retained host packets are
recorded in [`final-series-attempts-v6.json`](final-series-attempts-v6.json).

The same push dispatched source-development run `41962045862`; both hosts
refused before target launch because the source workflow verified catalog v3
against the revised N01 v2 bytes. This is a separate preflight failure and
earlier source-development evidence remains tied to the old inputs. V7 adds the
frozen journal alias and updates the final fault declaration to catalog v4.
The stale source-development push trigger is disabled until its historical v3
contracts are re-versioned; its manual workflow dispatch remains available but
does not establish a passing source-development run.

Seventh candidate attempt `41964820652` launched 15 exact-RC6 cases: 13 passed,
while Linux N02 timed out at the implicit 3-second checkpoint and Windows N15
selected `feat-blue` after displaying `feat-é`. Linux checked source/runtime
removal; Windows confirmed process exit, source restoration, and all 13 case
workspace cleanups, then its final deletion script failed because
`Get-FileHash` was unavailable in its isolated PowerShell environment. Both
full packets and extracted inventories remain under the v7 retained directory
and are summarized in [`final-series-attempts-v7.json`](final-series-attempts-v7.json).
The independent three-host helper readiness run `41964820676` passed but is not
candidate evidence. V8 freezes a 10-second N02 readiness bound, adds `Down` to
N15, and replaces the missing PowerShell cmdlet with in-process SHA-256. Across
v4 and v7, 29 target launches produced 25 passes and four failures; no complete
batch, calibration, or admission credit is claimed. The full 12-batch,
three-fault exact candidate run, independent audit, and checked cleanup remain
open.

Eighth final attempt `41967210773` passed 16 of 17 launched target cases across
Linux and Windows. Linux N03 timed out at its implicit 3-second checkpoint;
Windows N01-N14 passed, while N15 was refused as an invalid spec because `Down`
is not a valid key name. Linux source/runtime deletion passed. Windows retained
the owned source because the cleanup validator refused the unconfirmed
invalid-spec report. Both packets and inventories are preserved in
[`final-series-attempts-v8.json`](final-series-attempts-v8.json). Cumulative v4,
v7 and v8 observations are 46 launched target cases (41 pass, five fail), with
zero complete batches or candidate credit. V9 sets N03's readiness bound to
10 seconds and uses supported `ArrowDown` for N15.

Ninth final attempt `41968702601`: Linux passed N01-N03 then N04 timed out at
3 seconds. Windows passed four complete 20-case batches (80/80) and stopped
before batch 5 when the viewport transformer raised `KeyError: width` on v3
specs that omit optional dimensions. Both host jobs restored source and
runtime and verified exact removal. The host packets and full inventories are
in [`final-series-attempts-v9.json`](final-series-attempts-v9.json). This run
adds 84 target launches (83 pass, one fail); Windows's four completed batch
receipts are retained but no candidate execution credit is qualified. V10
gives all frozen cases a bounded 10-second deadline and fixes viewport defaults
to 80 by 24 in the batch transform.


Tenth exact-candidate attempt `41970500610`: Windows completed 240/240 cases, all 12 batch receipts, all nine source-fault phases, process proof, and checked source/runtime removal. Linux passed the first nine complete batches and 11 cases in the next batch, then N14 was cancelled after 3.65 seconds with target exit 130; its report and empty screen evidence are retained and workspace/process cleanup passed. Total observed 432 launches: 431 passed, one cancelled; no qualification credit. Both packets and extracted inventory digests are in [`final-series-attempts-v10.json`](final-series-attempts-v10.json). V11 increases public case step/run bounds to 20/60 seconds and declares a fresh complete rerun.

V11 declaration note: the first immutable v11 declaration was superseded before dispatch because its revision-summary labels were inconsistent and its generator bytes changed during correction; no target ran under that declaration. V12 binds corrected labels and final staged harness hashes to the same v8 scenarios, then reruns the complete two-host series.


Eleventh hosted attempt `41974745060` refused before launching any Git Town test cases: the journal preflight still referenced scenario alias v5 after the freeze advanced to v6. Both artifacts are preserved with full inventories in [`final-series-attempts-v11.json`](final-series-attempts-v11.json). Candidate case counters do not change. Windows process proof found no target process, but both cleanup jobs refused source/runtime deletion because no case-report cleanup proof existed; ephemeral runner teardown followed. V13 shares and tests the scenario-alias validator, and a fresh complete run must re-establish cleanup evidence.


Twelfth exact-candidate attempt (`41975837578`): Windows completed 240/240 cases, all nine source-fault phases, and checked cleanup. Linux passed 195 cases; the outer `next20_check.py` deadline fired at exactly 1,200 seconds during N18 in batch 9, cancelling one target case. Its workspace/process cleanup and the host source/runtime removal passed. Both packets and inventory hashes are preserved in [`final-series-attempts-v12.json`](final-series-attempts-v12.json). The run adds 436 target launches (435 pass, one cancelled) and zero candidate credit. V14 raises the bounded outer series deadline to 2,400 seconds and binds the workflow file.


Fourteenth hosted workflow `41978773971` refused before target launch on both platforms: the workflow requested 2,400 seconds, but `next20_check.py` still capped its parser at 1,200. Cleanup refused source/runtime deletion without target reports; the runner VMs were ephemeral and ended with their jobs, but no checked removal is claimed. Both packets and inventories are in [`final-series-attempts-v13.json`](final-series-attempts-v13.json). Case totals and qualification credit do not change. V15 raises the adapter's checked maximum to 2,400 seconds and adds numeric-boundary tests.


Fifteenth hosted attempt `41980469906` (`v15`): Windows completed 240 ordinary cases, all nine source-fault phases, process-tree proof, source restoration, and checked removal. Linux completed batches 0-10 (220 passes), then its first batch-11 N01 attempt failed at the declared 2,000 ms startup boundary before any action step; the target exited 130 and process/workspace/source cleanup passed. No retry or qualification credit is counted. Both complete packets and canonical inventories are retained in [`final-series-attempts-v14.json`](final-series-attempts-v14.json). The exact N01 report records `assertion_timeout` waiting for first output at startup. V16 will preserve this result and adjust only Linux batch-11 startup to a bounded 5,000 ms, leaving the Windows 2,000 ms boundary and ordinary test deadlines unchanged.


Seventeenth hosted workflow `41984301547` (`v16`) repeated the same effective Linux N01 failure: Windows completed 240 ordinary cases, nine fault phases and checked cleanup; Linux completed 220 cases then timed out on N01 at 2,000 ms. The packet?s generated N01 contract confirms 2,000 ms, although the v16 declaration specified 5,000 ms for Linux. Root cause: the top-level Git Town wrapper checked v16, while the shared batch runner read the legacy v1 startup profile. Preserve both packets and the exact report in [`final-series-attempts-v16.json`](final-series-attempts-v16.json); no retry or qualification credit. A duplicate queued dispatch `41984332161` was cancelled before any jobs started and is separately recorded in [`final-series-attempts-v15.json`](final-series-attempts-v15.json). V17 threads the explicit per-host startup profile to the batch runner and adds an override regression test.
