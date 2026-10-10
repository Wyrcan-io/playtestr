# visidata: completed real-project trial

Upstream [saulpw/visidata](https://github.com/saulpw/visidata/tree/dd1a9f0a53fe4bf030db939b06c73cb665406d4a), exact `dd1a9f0a53fe4bf030db939b06c73cb665406d4a`, GPL-3.0. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Find noninitial row, cancel cell edit, save Unicode TSV and inspect exact exported bytes.

Excluded: Network loaders, arbitrary formats, plugins, styles and spreadsheet-wide correctness.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [search](search.json): Search actual table data and move to the matching beta row | alpha; search; row=1; reviewed `search-offline.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [cancel-edit](cancel-edit.json): Cancel a pending cell edit without changing the data table | alpha; DROP; alpha; reviewed `cancel-edit.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [edit-save](edit-save.json): Resize, edit a Unicode cell, save a new TSV and independently inspect exact persisted data | alpha; café; save to:; save finished; reviewed `edit-save-complete.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |

Native isolated Python environment; --nothing plus explicit empty --motd-url avoids MOTD network access. Actual search regression and real saved-header corruption are rejected.

Preserve empty argv values, and add general CtrlA/CtrlK keys (4a1f41d). Mounted Windows virtualenv startup took 11.85s; native /var/tmp runtime fixes setup. WSL erased a /tmp runtime; ownership-tracked /var/tmp replaces it.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
