# Bounded primary device-attributes replies

Status: implementation and native requalification in progress, 17 October 2026.

Edit Linux run 39037952527 builds successfully but all twenty scenarios time out
at their first readiness assertion. Failure screens contain only the ellipsis
written during its startup probe. Reviewed pinned setup_terminal sends CSI c and
waits for a c response before drawing. Existing vt10x has a DA TODO; the session
discards all emulator replies. Windows ConPTY answers independently and its full
development cell passes. Do not replace this target to hide the runner gap.

Provide only the measured general primary-DA exchange: exact CSI c or CSI 0 c
requests receive CSI ? 6 c (the VT102 identification form documented in the
[xterm control-sequence reference](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)).
This is a stable minimal identification, not complete VT102 certification.
Secondary/tertiary/private/malformed DA requests, cursor/status/color queries,
clipboard, images and application-directed window manipulation gain no support.

The emulator generates the reply while parsing complete control sequences, so
split sequences work and request-like text inside OSC is not answered. A bounded
collector filters every other emulator response. On Unix, one session-owned
writer sends complete reply batches through the same input mutex as user keys.
The queue holds at most sixteen batches; each batch is capped at 16 KiB (an
8-KiB PTY read can produce at most 13,655 DA-reply bytes). A full queue applies
backpressure outside the screen mutex, allowing assertion/run cancellation and
cleanup to proceed. No goroutine is created per request. Windows leaves replies
to ConPTY to avoid duplicates.

Shutdown stops queued replies, terminates the owned process tree when needed,
closes the PTY to release any blocked write, and joins both reader and reply
writer within the cleanup context. Preserve a live transport error separately
from the original test failure; a transport failure cannot earn a green result.
Existing target output and run/step budgets still bound a query flood; replies
are transport data and are not persisted as target output or recorder controls.

Native core 39038928656 at d7a9ed1 catches a Linux backpressure cleanup failure
in both ordinary and race tests: process termination is confirmed, but the reply
worker does not join within the unchanged three-second cleanup budget. The same
real-PTY test passes on macOS. Linux previously used a blocking master write;
closing its descriptor is insufficient to guarantee that syscall returns.
Use the existing macOS nonblocking read/write polling mechanism on both Unix
hosts, with at most 25 ms holding the transport lock per poll. Closure marks the
transport closed under that lock and releases both loops. Preserve Linux's
startup slave release and macOS's retained slave/final-output behavior. Do not
increase the cleanup deadline to hide a blocked writer. Requalify both paths.

Acceptance: exact bytes and rejected variants across every split boundary;
real native Unix PTY startup waiting for DA, repeated requests interleaved with
normal input and wide cursor content, wrong expected exit, timeout/cancellation,
query flood and blocked-reply cleanup; existing unsupported cursor-query control
stays unsupported. Run ordinary and race checks on all native hosts and requalify
affected project cells before claiming archive coverage. The first Linux failure
and successful Windows source-f470 cell remain historical evidence.
