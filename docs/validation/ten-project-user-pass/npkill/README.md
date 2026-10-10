# npkill: completed real-project trial

Upstream [voidcosmos/npkill](https://github.com/voidcosmos/npkill/tree/620f011bf79ebf345d76d916448b37840b30e2a3), exact `620f011bf79ebf345d76d916448b37840b30e2a3`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Filter actual directories, cancel filter and inspect selection, delete only filtered beta.

Excluded: User home scans, delete-all, explorer launch, age/update checks and real dependency trees.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [filter](filter.json): Filter actual scan to beta, exclude other paths and preserve all directory bytes | Search completed; data/alpha/node_modules; data/café/node_modules; data/beta/node_modules; Search:; Search: beta_; reviewed `filter.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [cancel-resize-details](cancel-resize-details.json): Cancel filter, resize and inspect the nondefault directory without deleting any data | Search completed; data/alpha/node_modules; data/café/node_modules; data/beta/node_modules; Search:; Search: beta_; data/alpha/node_modules; Result Details; data/beta/node_modules; reviewed `details.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [delete-one](delete-one.json): Delete only filtered synthetic beta directory and independently verify survivors and actual absence | Search completed; data/alpha/node_modules; data/café/node_modules; data/beta/node_modules; Search:; Search: beta_; [DELETED] data/beta/node_modules; reviewed `deleted.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |

Only synthetic node_modules directories and an outside sentinel. Independently verify all survivor bytes and deleted directory absence. Actual filtering regression and fake-success dry-run deletion are rejected.

Recorder correctly rejects stale existing beta and trimmed trailing-space anchors. Require initial positive presence and actual disappearance; disable update/age through supported public flags.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
