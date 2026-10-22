# Control applicability at the frozen candidate

The [native core audit](native-core-129b7a4.json) binds actual Linux amd64,
macOS arm64 and Windows amd64 ordinary tests, vet and race checks to production
source `129b7a45c0006be550f798ce52c2fbbfd327e515`. Those source inputs also built
the [frozen rc.5 archives](migration-candidate-freeze.json). Source tests and
archive invocations have separate denominators.

| Scope | Actual evidence | Interpretation |
| --- | --- | --- |
| 88 historical whole controls | [Source matrix](old-control-matrix-revision-3.json) | 87 applicable passes; hosted Windows short-path alias remains excluded. The earlier actual local C-volume alias success does not qualify a hosted D-volume alias. |
| 33 new whole controls | [Native outcomes](new-control-development-evidence-revision-13.json) | Whole tests only; host copies, subcases and seeds add no unique-control credit. Includes public state behavior, internal fault injection and the evidence/CI harness. |
| 35 public archive reexecutions on each of three hosts | [Declaration](archive-control-declaration.json), [Linux](archive-controls-verified-linux.json), [macOS](archive-controls-verified-macos.json), [Windows](archive-controls-verified-windows.json) | 105 actual hosted invocations against exact installed rc.5; a separately identified trusted fixture is compiled. Local Windows preflight adds 35 observations and no new control credit. |
| Archive recording, maintenance, reporting and migration | [Three native installation journeys](archive-experience/README.md) | Source-free record/review/replay/export, selected screen/file failure and recovery, reports, old versions, upgrade/rollback and portable removal. |
| Real application state, input, snapshots and lifecycle | [Final matrix](final-matrix-audit.json), [old migrations](closing-old-archive-audit.json) | Actual native application reports and source faults extend public archive coverage. These are application scenarios and calibrations, not additional whole product controls. |
| Auditor integrity | [Eleven global negative controls](final-matrix-audit.json) | Deliberately changed actual evidence models must reject qualification; no product-scenario credit. |

The 35 public controls exercise exact CRLF/NUL/Unicode bytes, wrong bytes after a
successful screen and exit, missing/wrong-type paths, absence, directories, exact
entry sets, empty files, the 64-KiB file/512-KiB aggregate/256-entry/1,000-step
boundaries and exceeded bounds, traversal, unsupported formats, output flood,
assertion/run deadlines, descendant termination, exact nonzero exit, alternate
screen restoration, Unicode and resize. Recorder controls refuse an unresolved
missing-file capture and an input-only draft. Each report is bound to actual
prelaunch runner, contract and fixture identities; state IDs belong to the same
invocation and workspace. Unsupported-format refusal has no target identity
because the target never launches.

Internal APIs cannot be called through an installed CLI. Partial backend writes,
injected cleanup/rollback failures, concurrent replacement schedules, specific
Unix permission/FIFO and Windows lock/junction controls, malformed report internals,
and atomic ledger publication retain their actual source-level evidence. The
archive checks above provide public behavior coverage; they do not relabel every
internal test as an archive execution or transfer an excluded platform result.
The evidence harness is validation tooling, rather than code shipped in the
standalone binary. Its ledger, selection, identity and CI checks remain harness
controls. No new dependency on an application framework was introduced.
