# Restore Windows interrupt processing in the standalone CLI

The native Windows Bundler interrupt scenario timed out although the same
reviewed contract passed locally. Independent Ruby `gets` and Readline probes
also timed out on that host. Waiting for the complete application prompt did
not repair it. These failures remain separate recorded attempts.

Microsoft documents that the process attribute set by
[SetConsoleCtrlHandler(NULL, TRUE)](https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler)
ignores Ctrl-C and is inherited by children. Setting NULL/FALSE restores normal
processing. A process-local experiment reproduced the failure with the unchanged
runner and Ruby contract by setting that attribute in its ancestor, then passed
after clearing it (parent `68054e299b2340789cf12cabf38f2dc6`). This proves the
inherited-attribute failure mechanism, without claiming which hosted ancestor
originally set it.

A real CLI/PTY regression uses a dedicated ancestor process with this attribute,
the ordinary CLI entry point, and a target waiting for an actual interrupt. It
fails before the repair (`88fd69be0f634b39bc533db726fdbaa0`), with a bounded step
timeout and confirmed Job Object cleanup. It needs no Ruby dependency.

The standalone Windows CLI will restore normal Ctrl-C processing once, before
registering its cancellation handler or launching any targets. This changes
only that process's attribute and its future children. It does not modify host
configuration, input modes, target handlers or already-running processes. API
failure must be reported explicitly. Other platforms retain their current
signal handling. Named Ctrl-C still sends its documented byte through the PTY;
it does not become an out-of-band process-kill operation.

Native ordinary/race checks, the Ruby reduction and original Bundler scenario
must verify the repaired source. Prior binaries retain their original results;
final archives must be rebuilt and independently qualified.
