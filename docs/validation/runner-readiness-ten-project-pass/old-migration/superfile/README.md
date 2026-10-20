# Original Superfile migration

Original MIT pin: `66fe169b87021f7424522ed5aadd711c5676601e`, version
v1.6.0. The original twelve workflows require Linux and macOS qualification.
No Windows target is built or run in this migration.

Source acquisition initially stopped at 16 MiB before extraction. Immutable
upstream tree metadata shows 20,027,803 logical source bytes across 527 entries,
including website/demo images. The reviewed source-download allowance is 24 MiB;
the old-project retained cap stays 32 MiB. The actual archive is 17,851,383 bytes.
A subsequent strict extraction rejected the sole website notice symlink.
Its exact target and omission are reviewed; the original archive and all regular
runtime/embedded configuration bytes remain intact. All failed preparations are retained.

The owned source was reviewed locally against original license and module locks,
then archived, selected files restored and checked, and the unbuilt source tree
removed. The source-only retention helper initially demanded runtime reports;
that preparation failure remains recorded. Source-only retention now requires
no execution report and earns no runtime compatibility credit.

Native builds use direct pure-Go compilation with an owned, official
checksum-verified Go 1.27.0 SDK and owned caches. The original configuration
disables update checks and image previews. Editors/openers, clipboard, trash,
shell integration and user files are excluded. The original nonpreviewed-copy
corruption must still pass the terminal-only contract, fail the public same-run
saved-byte assertion and pass after exact source/compiled-binary restoration.

The canonical original source archive is retained once, locally, at the ignored
campaign path `old-superfile/retained-source/source.tar.gz`. Both native jobs
record its exact hash/size and independently verify original source restoration.
Uploads exclude duplicate source-archive bytes. Native audit must resolve and
verify that explicit local canonical reference; a missing or mismatched archive
cannot earn credit. Native packets will be retrieved, audited, compacted and
removed one host at a time under the unchanged storage cap.

Native run `39384177500` passed all twelve original cases on Linux amd64 and
macOS arm64, including actual compiled copy corruption, terminal-only false
green calibration, same-run saved-byte rejection, exact source/compiled-binary
restoration and checked source/SDK/cache cleanup. Independent
[Linux](verified-linux.json) and [macOS](verified-macos.json) audits passed.
The first macOS audit refused the `macos` versus frozen `darwin` host label;
correcting that explicit mapping required no target rerun.

The [admission](migration-admission.json) records twelve canonical scenarios,
two native cells, 24 primary and six calibration executions. Both native packets
retain all 387 logical files each in separately verified compressed archives
(648,574 Linux bytes; 659,048 macOS bytes), with selected restoration checks.
Expanded packets are removed. The canonical source reference remains present
and hash-verified; the complete selected project retains 20,043,749 bytes,
under the unchanged 32 MiB cap. No owned target remains. New-project and
final-archive credit remain zero for this old-project work.
