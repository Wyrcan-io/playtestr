# Original lf migration

The original MIT pin is `5d3c7b702515dfb72d8d496673fa1c4144d1dbed`.
Its source, original license and exact `go.mod`/`go.sum` are reviewed before
building. The direct native pure-Go build uses an official checksum-verified
Go 1.27.0 SDK, owned caches and temporary paths. Makefile, installation and
generation hooks are excluded. The active logical-byte stop is 1,536 MiB;
periodic measurements do not establish an exact peak or an operating-system quota.

All twelve original contracts are prepared for previously qualified Windows
and Linux, with public same-execution saved-state assertions appended after
completion. Original commands, inputs, snapshots and fixtures remain unchanged,
including explicitly restored empty fixture directories. `-single` avoids lf's
shared server; openers, editors, custom shell commands and user files are excluded.

The original unselected `charlie.txt` copy corruption will be rebuilt in the
real target: the selected preview and terminal-only contract must still pass,
the public state assertion must reject the wrong bytes in that same execution,
and exact source plus reproducible compiled-binary restoration pass the
unchanged contract on local Windows and native Linux run `39382652107`.
All twelve original cases pass on each host. Independent
[Windows](verified-windows.json) and [Linux](verified-linux.json) audits bind
actual public invocations, original native prefixes, saved-state expectations,
compiler/source/compiled-binary identities and cleanup.
The [admission](migration-admission.json) records twelve canonical scenarios,
two native cells, 24 primary and six calibration executions. No new-project or
final-archive credit is added. All thirty ordinary executions are accounted for;
the earlier failed setup probe is retained separately.

Owned source, native SDK and build caches are removed after source archive,
selected restoration and process checks. The Linux packet retains all 526
logical files in a verified 635,342-byte compressed archive; its expanded copy
is removed. Bulk evidence is local-only under the ignored campaign artifact root.

The first local build compiled successfully, but its version probe panicked
because Windows requires `USERNAME` during target initialization
(`d357024aa217495eb063fcdca2135fe5`). The original public scenarios already
declare `USERNAME=synthetic-maintainer`. Applying that value to the build's
version-probe environment and rebuilding with unchanged source/flags passed
(`3ca26be170dc4fe3a525143f6ebefe50`); the original failure remains retained.
