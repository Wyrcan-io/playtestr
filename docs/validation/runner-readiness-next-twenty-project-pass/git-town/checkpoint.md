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
