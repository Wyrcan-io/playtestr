# Skim project package: development checkpoint

Skim is the eighth selected application. Its immutable source pin is
`1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3` from `skim-rs/skim`, MIT, version
5.8.0. The reviewed source tree has no root build script. We fetched its 357
locked crates by checksum, reviewed 53 dependency build hooks before Cargo build,
and built the Windows CLI offline with only `cli,frizbee`; `image` and `listen`
are excluded. The built target is `sk 5.8.0` and its SHA-256 is
`c7be41c93ff1811287b0e79e771d9e8cf8b0c064fa3205001f8c8a8cda758a5f`.

The reviewed route launches the pinned `sk.exe` directly in Playtestr's Windows
PTY. A fixed case-owned Python reader supplies only each synthetic `items.txt`
file through `SKIM_DEFAULT_COMMAND`. Interactive command mode, previews, remote
IPC, shell integrations, user history/configuration and network routes are out
of scope.

All 20 frozen development cases completed once on native Windows: eight normal
flows and twelve edge flows. The cases cover unique and fuzzy selection,
multi-select, query preservation, Unicode labels, long wrapped rows, no-match,
cancel, parser errors, small viewport, resize, rapid input, exact match,
late-list search and NUL-mode screen/exit behavior. Every action and assertion
passed, and owned workspace cleanup was confirmed. The exact per-case IDs and
source/report/spec/fixture/snapshot hashes are in
[the Windows readback receipt](windows-frozen20-development-readback-v1.json).
The specs and source/snapshot hashes are frozen in
[scenario declaration v5](scenario-declaration-v5.json).

Two early evidence defects were corrected and retained as failed attempts. The
v2/v3 Unicode fixture files had literal ASCII question marks because of Windows
PowerShell encoding; v4 uses explicit UTF-8 bytes and Unicode JSON escapes. The
v2/v3 Unicode runs therefore provide no Unicode evidence. The v4 Windows cases
N06 and E09 each reached the unique 1/2 match, selected the exact Unicode row,
exited zero and passed their byte-reviewed snapshots. Missing-snapshot first
runs remain failures; baselines were created only after reviewing the observed
final rows. One exploratory loose selector check was rejected after it accepted
an unselected candidate row; the frozen route requires positive match count,
exact selection and final snapshot.

The hosted source-development run 41810289319 passed the same frozen twenty
cases on native `ubuntu-24.04` and `windows-2025`: 20/20 on each host, with all
40 temporary workspaces confirmed cleaned. Both jobs verified the same 819-file
source provenance, fetched the 357 locked crates, reviewed all 53 build hooks,
and built Skim 5.8.0 offline with only `cli,frizbee`. Each host used an official
Go 1.25.0 SDK installed below the campaign-owned root. The per-case reports,
binary and dependency hashes, SDK receipts and artifact digests are bound in the
[hosted development readback](hosted-development-readback-v1.json); preceding
failures and their corrections remain in
[hosted development attempts v4](hosted-development-attempts-v4.json).

These runs exercise the current source runner, not the private rc.6 archive, and
receive no candidate admission or native-cell credit. Repeated final series,
current-candidate package installation, three real source faults, public
first-use/maintenance/relocation, target cleanup, storage closure, independent
full evidence audit and final candidate gates remain open.

Two explicit limits stay open. Earlier strict-selection attempts showed that
ArrowDown and Ctrl-N did not move Skim's highlighted row on local Windows even
though Playtestr's menu example accepted ArrowDown. The frozen cases avoid
claiming that directional navigation works. The hosted Linux and Windows source
runs now pass the frozen matrix, but they do not resolve directional-navigation
compatibility. E12 checks screen and exit only; exact NUL output framing still
needs a separate bounded output capture.

The 4 November hosted rerun also reproduced Linux E03 and E04 startup failures:
Skim's invalid-option parser exited with the declared code 2 before emitting
terminal output, while the generic startup gate required first output before it
would execute the explicit exit assertion. E03-v3 and E04-v3 remove that
startup-output gate; each requires its exact exit code and owned-workspace
cleanup as positive evidence for a CLI parser path that never enters terminal
mode. Scenario declaration v6 binds both replacement contracts and keeps the
earlier v2 results in the attempt log.

