# Skim resume checkpoint

As of 4 November 2026, the corrected hosted source-development gate passed on commit
`47d5ff9bdaabadbf98539a8dce81ecb33fed3012`, workflow `41827379783`: Linux 20/20,
Windows 20/20, all 40 workspaces cleaned. E03-v3 and E04-v3 both require target
exit 2 plus workspace cleanup and pass on both hosts. Windows detected all three
declared real source faults; the source pin was restored and all 28 inner archive
members matched their manifest. Readback: `source-development-readback-v2.json`.
The native helper/readiness workflow `41827379961` passed on Ubuntu, macOS and
Windows. GitHub artifact digests and complete per-case hashes are in the readback.

Skim remains selected project 8, not admitted: private candidate archive repeated
series/calibrations, public first-use and authoring, maintenance/diagnosis,
relocation, delivered CI, and final cleanup/storage/audit are open. Known risks
WIN-NAV-01 (directional navigation) and OUTPUT-NUL-01 (exact NUL framing) remain
open. Development faults do not count as final source faults. Do not increment
project or current-candidate counters.

Next selected project is Git Town (project 9). Re-read its declaration, review
its pinned source/license/build hooks and native support before acquisition. Keep
late-transfer projects `ne`, `sc-im`, `btop`, and `htop` unexposed until provisional
candidate freeze.
