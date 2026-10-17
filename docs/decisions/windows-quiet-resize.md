# Observe native Windows dimensions without requiring target output

Measured during the runner-readiness campaign. Existing Windows resize completes
on a matching terminal resize reply or output from a read begun after the native
resize API returned. This correctly refuses stale output, but quiet applications
and a real Git/less child may produce no qualifying next read. Plop, Poetry and
Bundler expose bounded failures; Bundler's pager passed individually and failed
its full suite. Those first failures remain in the campaign evidence.

Do not relax the existing stream fence, inject target input or infer success from
silence. A separate detached instance of the same standalone runner can attach
read-only to the owned target console and query its actual dimensions. An owned
prototype verified 80x24, 40x12, 100x28, 40x12 and 100x28 with a quiet real Ruby
process, parent `60231bb2a79a495ebf48f8f76e0c33b6`. Its source is retained at
`artifacts/runner-readiness-ten-project-pass/experimental/console_probe_windows.go`.
No production behavior changed for that experiment.

Microsoft documents that [ResizePseudoConsole](https://learn.microsoft.com/en-us/windows/console/resizepseudoconsole)
changes the internal dimensions visible to console clients, and
[GetConsoleScreenBufferInfo](https://learn.microsoft.com/en-us/windows/console/getconsolescreenbufferinfo)
retrieves actual buffer/window coordinates through a read-capable handle.
The observed query is evidence of native dimensions, not application redraw,
semantic readiness, or complete stream draining.

Implement this query as an additional positive native acknowledgment. Bind it
to the launched target PID and creation time, retain a process handle during
the query, and compare returned dimensions with the current request. Never let
an old request or unrelated process acknowledge a new resize. Keep the existing
reply/output checks intact. Explicit redraw waits still require subsequent
rendered activity; ordinary assertions and saved-state checkpoints remain their
own observations.

Use only the same executable, a private startup mode, bounded numeric protocol,
read-only console access and a detached hidden child. No PowerShell, external
helper binary, new dependency, target stdin/output, global console changes or
persisted environment values. Reap the helper inside the current step context;
close all process/console handles and detach its console. Failed native queries
cannot create passing evidence. Cover quiet repeated real PTY resizes, stale
identity, malformed/wrong dimensions, cancellation, helper cleanup and unchanged
redraw semantics before native requalification. Existing source-93 development
admissions do not qualify the changed binary.
