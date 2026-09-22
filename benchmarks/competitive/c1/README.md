# C1 frozen matched task

This fixture implements Sprint 13-C task C1 on Linux amd64: start at 60x12
with records `Alpha`, `Beta`, and `Gamma`; wait for the initial screen; press
Down once; prove the visible cursor is on `Beta`; press Enter; and require both
`Selected: Beta` and an independently written exact `Beta` oracle.

The good and known-bad executables come from the same source. The bad build uses
the reviewed `competitive_bad` build-tag mutation, so it visibly moves to
`Beta` but commits `Alpha`. Tool-specific test files and all other target inputs remain
unchanged. This is a target mutation, not a weakened input sequence or edited
snapshot.

Frozen tool pins for the first admission are Playtestr at the tested repository
commit, Atago v0.23.0, Microsoft tui-test 0.1.0-beta.5, and Termlens 0.11.2.
The host is GitHub's Ubuntu 24.04 amd64 image. Documentation was retrieved from
the matching project tags on 22 September 2026.

The Microsoft CLI's `expect exit-code` applies to submitted shell commands and
does not expose the exit code of a direct `run` program. Its adapter therefore
uses `/bin/sh` to run the same target and print `TARGET_EXIT:<code>` before
returning that code; the test asserts the marker and `wait exit`. This extra
command and authored glue remain part of that tool's measured surface.
