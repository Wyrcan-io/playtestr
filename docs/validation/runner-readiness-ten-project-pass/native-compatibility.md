# Native development compatibility boundary

This table describes current source development evidence, not a published
archive or a final qualification claim. Production runner source is now
`f470cd99aef89e080cc8455e4f8ad4715ecd12c2`; full native core 39010459162 passes
on Linux amd64, macOS arm64 and Windows amd64, including ordinary/race checks.
Earlier core runs
`38948501204`, `38950594057` and `38953916606` each succeeded on native Linux
amd64, macOS arm64 and Windows amd64. Their exact source/test/event identities
remain in the owned raw packets. Final frozen archives must run their own series.

| Feature | Linux amd64 | macOS arm64 | Windows amd64 |
| --- | --- | --- | --- |
| Public same-execution exact file/directory assertions, recorder and selected maintenance | Development verified | Development verified | Development verified |
| Unix actual SIGINT/SIGTERM shell-convention status and post-exit state | Real PTY verified | Real PTY verified | Not applicable; native exit codes retained |
| Controlled terminal input, supported paste and lifecycle/cleanup | Applicable old controls pass | Applicable old controls pass | Applicable old controls pass |
| Native special-file/permission rejection | Applicable controls pass | Applicable controls pass | Different native junction/exclusive-lock controls pass |
| Actual selected file/link replacement | Passes ordinary/race controls | Passes ordinary/race controls | Hosted control passes; local symlink privilege unavailable |
| Resize with observed applicable terminal/output fence | Applicable controls pass | Applicable controls pass | Applicable controlled-output controls pass |
| Repeated resize while application/terminal remains quiet | Project semantics exercised in POSIX Plop | Project semantics exercised in POSIX Plop | General positive native-size query passes real ordinary/race controls; old Plop/Poetry Windows exclusions remain historical |
| Ctrl-C from a Windows ignoring ancestor through the standalone CLI | Not applicable | Not applicable | Real ancestor/CLI/PTY ordinary/race control and original Bundler E03 pass after process-local repair |
| Exact temporary short-path alias expansion | Not applicable | Not applicable | Actual local C-filesystem control passes; hosted D-filesystem alias unavailable |
| Installer version flood/hang, supported compact/spaced install route | Native controls pass | Native controls pass | Native controls pass; arbitrary long launch paths excluded |
| Plop full twenty-scenario development package | Admitted | Admitted | Nineteen pass; resize case red; excluded |
| Poetry full twenty-scenario development package | Admitted, run 38957159731 | Admitted, run 38957159731 | Nineteen pass; resize case red; excluded |
| Bundler full twenty-scenario development package | Admitted, run 39011298428 | Not selected | Admitted, run 39011298428; explicit runtime profiles retained |
| Edit full twenty-scenario development package | Admitted, run 39039845616 | Not selected | Admitted, run 39039845616; explicit new-document LF host difference retained |
| Primary device attributes, exact CSI c / CSI 0 c | Real PTY ordinary/race passes, core 39039797857 | Real PTY ordinary/race passes, core 39039797857 | ConPTY replies independently; runner injects no duplicate reply |

The [all-88 mapping](old-control-matrix.json) preserves every earlier control and
its actual host applicability: all 88 now have applicable development evidence
after the [local alias supplement](old-control-matrix-revision-2.json), preserving
the hosted filesystem's explicit skip. New controls are separately declared
with [actual development binding](new-control-development-evidence-revision-4.json);
all still need final archive evidence. A configured workflow is never a passed cell.

One local Windows snapshot-rename access-denied result remains an unexplained
residual (R3-07); ten unchanged focused repetitions did not prove a repair.
Historical wizard/readiness/helper incidents have separately declared bounded
investigations. Target/framework names never select production core behavior.

No coverage is claimed for arbitrary grapheme clusters/styles, mouse, clipboard,
other terminal replies, third-party plugins or network services. Concrete Unicode/path
fixtures do not establish universal Unicode support. PTYs, subprocesses and
managed workspaces run trusted targets with user permissions and provide no
security isolation. Native Actions execution is neither a PR-event study nor
human usability evidence.
