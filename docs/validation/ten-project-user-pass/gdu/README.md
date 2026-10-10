# gdu: completed real-project trial

Upstream [dundee/gdu](https://github.com/dundee/gdu/tree/387cf50377e53bad628603658cfb76fd4a54d718), exact `387cf50377e53bad628603658cfb76fd4a54d718`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Computed sizes, folder navigation, cancel deletion, help and resize.

Excluded: Real disk/home scans, successful deletion, symlink traversal and every display mode.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [navigate](navigate.json): Scan actual files, enter largest directory and navigate back | alpha.bin; child.bin; alpha.bin; reviewed `navigate.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [cancel-delete](cancel-delete.json): Cancel a destructive deletion and independently verify file bytes survive | alpha.bin; Are you sure you want to delete; reviewed `cancel-delete.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [help-resize](help-resize.json): Resize, open and close keyboard help without corrupting the file table | alpha.bin; Move cursor up/down; reviewed `help-resize.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |

Only 1/2/3 KiB synthetic files. Canceled deletion preserves exact child bytes. Actual size-formatting regression is rejected; explicit --si output provides intended expectation maintenance.

Random fresh workspace name made full-viewport snapshots unstable. Implemented explicit reviewed physical-row snapshots in c8274d5; meaningful result rows stay asserted and full failure screens remain available.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
