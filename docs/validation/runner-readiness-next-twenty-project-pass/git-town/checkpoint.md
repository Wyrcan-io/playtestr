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


Three source mutations are predeclared in [fault-declaration-v1.json](fault-declaration-v1.json), with unchanged tests for parent output, feature branch creation, and prototype state persistence. The hosted workflow verifies the pinned source tree before running each baseline, mutation, and restoration phase. It keeps each fault executable separate from the initial runtime and reports the expected failure category; the false-green case must pass terminal and exit assertions before the saved-state assertion fails.

Local harness rehearsals and their exact failures are preserved in [fault-matrix-local-harness-attempt-v1.json](fault-matrix-local-harness-attempt-v1.json). They add no project or fault credit. The local Windows workspace setup did not launch a scenario target, so native hosted execution is required.

Next gates: complete and audit the hosted fault matrix; run the public recorder path without handwritten specs, selected maintenance, Unicode/spaced-path relocation, and delivered free-workflow checks; then complete the exact final-candidate twelve-run cell, calibration, and cleanup audit. No Git Town admission or native-cell credit is claimed yet.
