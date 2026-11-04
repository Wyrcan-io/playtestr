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
