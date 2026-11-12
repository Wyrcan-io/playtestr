# Runner readiness continuation checkpoint v145

## Campaign count

The audited total is **17/30 admitted distinct applications**: ten first-batch projects, six new projects admitted on rc.6, and JOE on exact rc.7. Pick remains 0 credit. Do not infer admission from partial matrices or target build success.

## Pick status

Pinned Pick source `caae95938359b2e814b3e7406f396f486c9d99fb` (MIT, archive SHA-256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`) builds, passes upstream tests, installs, restores source and passes storage checks on Linux/macOS. v4 run `43320083737` retained failures: Linux N02 selected amber instead of blue under an ambiguous visible-text checkpoint; macOS rejected E04 before launch due to invalid `expect_not`; its cleanup helper safely refused source deletion because the explicit invalid-spec digest was not supplied. Both receipts are saved; no credit.

v6 run `43322068022`: Linux passed N01-N08 and E01-E06 (14/15 launched outcomes), then E07 timed out because Pick's pinned C parser splits at LF but retains CR from CRLF input; rendered choice `beta\r` appears as `eta`. Cleanup and storage passed, and five cases were not attempted. Receipt `pick/development-attempt-run43322068022-linux-v1.json` records the exact artifact/report hashes. macOS job `131544993901` remains queued; its result is required and must be recorded. The v6 contract grants no credit.

Immutable v7 is now locally materialized. It keeps N02 as a query plus exact selected-output assertion, fixes E04's exact prior observation, and changes E07 to assert the source-proven `eta` behavior while preserving the CRLF risk. Supplementary source analysis is in `pick/source-review-v2.md`. Local acceptance tests: 18 total, 15 passed and 3 host-specific skips; compilation and diff checks pass. v7 has not been launched.

## Next actions

1. Commit and push v6 Linux receipt, v7 immutable contract, source review and updated checkpoint on `work/p0-p2-implementation`; observe and retrieve exact artifacts for v6 macOS and v7 both hosts.
2. Iterate new immutable contracts only after each launch. Preserve all attempted and not-attempted denominators, report/artifact digests, process evidence, source restoration and storage results.
3. After a complete twenty-case development set passes on both hosts, execute final 12x ordinary qualification, all three safe fault matrices/calibrations, public authoring/maintenance/Unicode/CI workflow, old-project/current-candidate transfers, required whole controls, and independent auditing before admission.
4. Continue through the authoritative candidate ledger to 30 admissions; keep current count **17/30** until every full admission gate closes.

No release, PR, issue, discussion, outreach or paid runner action is authorized.
