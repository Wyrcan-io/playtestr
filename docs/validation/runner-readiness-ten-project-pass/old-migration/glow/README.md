# Original Glow migration

Original MIT pin: `8b0600fa445535b9c53194c0d4f7fe3cf700ef3e`.
The original twelve Markdown-reader scenarios require Linux and macOS.
Original source, license and module locks are reviewed. The local Windows
source tree is archived, selected restoration checked and removed without
building or running a target; this adds no Windows compatibility credit.

Preserve the original declared profile: `TERM=screen-256color`,
`GLAMOUR_STYLE=dark`, `GLOW_TEXT_SIZING=off`, mouse disabled. Optional OSC color
and text-sizing probes remain outside that boundary. Commands, rendered-body
snapshots and exact protected input bytes remain unchanged. Empty-document
coverage retains its meaningful identity footer rather than accepting a blank
snapshot. No URL, remote service, external editor/clipboard or user file is used.

Native builds use the exact owned Go 1.27.0 SDK, direct pure-Go compilation and
owned caches. The original `ui/stash.go` corruption writes wrong input-document
bytes after reading the correct body. The terminal-only contract must pass,
the public same-execution file assertion must reject it, and exact source plus
compiled-binary restoration must pass unchanged expectations.

The canonical original archive is retained once locally under the ignored
`old-glow/retained-source/source.tar.gz` campaign path. Native receipts bind its
hash and size; uploads exclude duplicate archive bytes. Both native packets
will be retrieved, independently audited, archived and removed one host at a time.
Standard Linux/macOS jobs are capped at two concurrent jobs, thirty minutes each;
expected combined native runtime is 5–10 minutes. Owned active build stop is
1,536 MiB; retained project cap stays 32 MiB. Migration and final-archive credit
remain separate from this migration.

Native run `39391254202` now passes all twelve original scenarios on Linux
amd64 and macOS arm64, including real compiled input-document corruption,
terminal-only false green, public same-run rejection, exact source/compiled
binary restoration and checked source/SDK/cache removal. Independent
[Linux](verified-linux.json) and [macOS](verified-macos.json) audits pass.
The [admission](migration-admission.json) records twelve canonical scenarios,
two native cells, 24 primary and six calibration executions; all thirty
ordinary executions are accounted for. No new-project or final-archive credit
is added.

Each native packet retains all 280 logical files in a separately verified
compressed archive (380,350 Linux bytes; 392,237 macOS bytes), with selected
restoration and explicit canonical-source checks. Expanded copies are removed.
The complete selected project retains 1,712,355 bytes, below its 32 MiB cap.
No owned target remains.
