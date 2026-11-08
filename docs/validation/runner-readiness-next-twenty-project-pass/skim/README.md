# Skim project package: development checkpoint

Current status: **admitted on exact v0.4.0-rc.6**. The formal [admission
receipt](admission.json) binds 20 scenarios, 480 passing ordinary executions,
18 baseline/mutated/restored fault phases, 24 rejected actual-model corruptions,
Linux and Windows native cells, the public first-use/diagnosis/maintenance/
relocation route, and checked cleanup. V35 is a verified repeat of V34, not
additional breadth. Delivered workflow execution and human usability remain
unmeasured; directional-key navigation and exact raw NUL framing remain open.
Campaign-wide storage, original-ten requalification and the remaining project
admissions are separate gates.

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
receive no candidate admission or native-cell credit. Those source-development
observations remain separate from the exact candidate admission above.

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


The corrected declaration v6 was executed in source-development run `41827379783`
(commit `47d5ff9bdaabadbf98539a8dce81ecb33fed3012`). Native Linux and Windows
each passed all 20 frozen cases, including E03-v3 and E04-v3 exact exit-code-2
and workspace-cleanup checks; all 40 owned workspaces were cleaned. Windows also
detected all three declared real source mutations. Its 28-member fault archive
was independently verified against its manifest, including failed screen evidence,
confirmed process-tree/workspace cleanup and exact source restoration. Receipts
and per-case hashes are in [source development readback v2](source-development-readback-v2.json).

This completes Skim's hosted source-development matrix and source-fault discovery
gate. It does not qualify a private candidate archive, final repeated series or
calibrations, and it does not change the new-project admission count.


The source-development workflow automatically repeated on commit `19e689f1d3721743146a11647fcb152048becd5d` (run `41831060729`). Linux and Windows again passed 20/20 with all workspaces cleaned; Windows detected all three declared faults, verified all 28 archive members, and confirmed source restoration. The source-pinned per-case repeat, archive hashes and fault results are in [hosted repeat readback](hosted-source-repeat-41831060729.json); its attempt is retained in [hosted development attempts v5](hosted-development-attempts-v5.json).

The exact local source/runtime tree has now been removed after 819-file pinned-source verification, 112 target/workspace cleanup confirmations, a native Windows process scan, and a checked 21,954-file inventory. Four invalid-spec and three workspace-setup reports received zero cleanup credit. The source archive, inventories, removal receipts and process proof are retained under the campaign artifact directory; the compact tracked summary is [cleanup readback](cleanup-readback-v1.json). Five Skim fault/evidence roots (2,166 files, 207,405,391 bytes) were moved byte-identically out of `active/` and retained under `artifacts/runner-readiness-next-twenty-project-pass/skim/retained-active-evidence/`; the complete move manifest is hash-bound in the cleanup readback. At that historical cleanup checkpoint, no candidate admission had been completed; the current admission is linked above.
