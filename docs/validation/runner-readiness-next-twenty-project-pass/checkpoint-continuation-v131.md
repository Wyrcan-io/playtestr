# Runner readiness continuation checkpoint v131

Campaign remains **15/30 recorded admissions**; the exact rc.6 new-project ledger remains **5/20**, 2,400 ordinary executions, 90 calibration executions, 100 scenarios and 10 native cells. `mg` remains unadmitted. Branch `work/p0-p2-implementation` is pushed through `f5bdcb8f`.

## Completed after v130

- Added a hosted saved-state oracle calibration to the Linux public-route job. Run `42991234833` passed the route, six oracle cases and storage gate. The exact artifact `13841697956` is 617,638 bytes with SHA-256 `f9a4f81febd22a730b2ba9349f55f156ffc2ec396b34daeb1159e58760eed820`; independent ZIP CRC and content audit passed.
- The six cases were two positives (correct file bytes and exact directory entries) plus four final-state rejections (same-size wrong bytes, missing required file, unexpected extra entry and a directory asserted as a file). Each negative failed as `state_assertion_failure` after earlier checks passed and cleanup was confirmed. This is oracle evidence only, zero admission credit.
- The first hosted calibration attempt, run `42990561239`, stopped at preflight because its declared target SHA was truncated. No calibration target run occurred. It and its retained artifact remain preserved; the full 64-character hash repair passed in run `42991234833`.
- Independent route audit: `mg/public-route-audit-run-42991234833-v1.json`; it records nine public-route attempts separately from six calibration attempts and retains exact case/report/console/identity digests.
- Fresh local storage observation `65282cd858444de689fca77350e62759` passes. Combined retained is 2,071,512,966 bytes, 75,970,682 below cap; new curated is 25,069,057 bytes, 1,145,343 below cap. Checkpoint is `storage-checkpoint-v46.json`.
- Focused Python report tests: 8 passed, one native Unix permission case skipped on Windows. Prior artifact-auditor compatibility check against run `42980303472` passed.

## Remaining work

Keep the admission count at 15/30. Review and close any remaining mg-specific technical authoring/maintenance and package gates; then proceed to the next selected project. Campaign-wide open gates include the other fifteen new project packages, current-candidate requalification of the original ten, whole-control/archive refresh, delivered-CI triplets, fresh-checkout audit, complete attempt reconciliation, and final storage/cleanup/reporting. Human study remains unmeasured and does not replace technical evidence.

Preserve all existing unrelated untracked paths, including `.codex-go-cache/`, `.codex-test-tmp/`, `.runner-readiness-compaction-tmp/`, continuation v117/v46, and skim readbacks/model-control files. Keep failed run `42990561239` and the current raw provider packet. Never run blanket cleanup.
