# Private archive experience

The exact frozen [rc.5 archives](../migration-candidate-freeze.json) passed actual
native installation and migration journeys on [Windows amd64](windows-migration-v2.json),
[Linux amd64](linux-migration-v2.json), and [macOS arm64](darwin-migration-v2.json).
Each independently verified journey includes 19 commands and eight outcomes:
fresh owned spaced/Unicode paths, exact checksums, source-free version/help,
record/replay/test/report, meaningful screen/file regressions and recovery, and
side-by-side previous-version upgrade/rollback. Installation changes no global PATH.

Portable four-file package removal passed on [Windows](windows-portable-uninstall.json),
[Linux](linux-portable-uninstall.json), and [macOS](darwin-portable-uninstall.json).
The [current unsupported-version control](windows-current-unsupported-version.json)
checks supported positive execution, prelaunch refusal and recovery using rc.5.
The [Linux process-offline journey](linux-process-offline.json) ran public commands
through a measured process-scoped seccomp socket guard, with positive/unfiltered
and denied socket probes. This is bounded offline execution evidence, not a
firewall, general isolation or security-sandbox claim.

The generated [free CI triplet](delivered-ci-verification.json) has actual
[success](delivered-ci-success.json), [saved-file corruption rejection](delivered-ci-corruption.json),
and [recovery](delivered-ci-recovery.json) jobs. Its frozen-source runner was built
on the hosted Linux runner. The corruption preserved successful earlier screen,
exact-file and exit checks before the public entry-set assertion rejected an
unexpected file. Report/summary/artifact handling, restoration and cleanup were
independently checked. No real pull-request event or paid service was exercised.

The [archive auditor controls](auditor-controls-migration-v2.json) and
[complete ten-project matrix audit](../final-matrix-audit.json) preserve separate
tampering refusals. Overall campaign admission additionally requires the final
old-project migration and closing documentation/storage audit. Nothing here
publishes a release or establishes unfamiliar-user usability.

The earlier rc.4 Windows-only experiment below remains historical evidence.

`windows-provisional.json` records an independent audit of the actual
v0.4.0-rc.4 Windows archive against the older private v0.4.0-rc.2 archive.
It does not qualify the final candidate or substitute for real-project tests.

Both archives were checksum-checked and extracted into fresh owned paths with
spaces and Unicode letters. Version/help ran from their four-file package
directories with an empty PATH. A deliberately corrupted archive was rejected
before extraction. The audit observed a non-administrator token; no global
installation or user configuration changed.

A separately compiled Go fixture supported public recording, review, replay
and ordinary v3 file assertions. A screen change caused an assertion timeout;
a saved-file change caused a state assertion failure. Restoring only the
fixture executable passed with unchanged contracts and baselines. The v2
terminal contract passed on the previous, current and rollback binaries, and
the current binary rendered the older machine report into HTML. The synthetic
fixture receives no real-project fault credit.

The first helper attempt failed before fixture compilation because it created
the same owned temporary directory twice. That failure remains retained. The
first independent audit scanned the entire live event ledger and failed;
the corrected audit validates all four immutable events for each of its
nineteen completed commands and checks actual prelaunch binary hashes.

These checks establish the exercised private Windows installation sequence.
They do not enforce network disconnection, prove Unix installation, run an
actual PR, or establish final archive or human-usability coverage. Upgrade and
rollback use explicit side-by-side owned installations rather than changing a
global PATH.

`windows-v3-rejection.json` adds an actual older-binary rejection check. The
v2 positive control launched a target that wrote an owned HTML marker. After
preserving that output elsewhere, the identical v3 contract produced a clear
unsupported-version error and no marker. The initial control omitted v2's
required workspace and was retained as invalid; the corrected positive control
ran before the negative check. This verifies the exercised prelaunch boundary.
