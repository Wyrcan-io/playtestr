# litecli: completed real-project trial

Upstream [dbcli/litecli](https://github.com/dbcli/litecli/tree/aa53bb0c1530cd1dfb30534babb0bf47df33c60a), exact `aa53bb0c1530cd1dfb30534babb0bf47df33c60a`, BSD-3-Clause. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Insert and select Unicode SQLite data, reject table deletion, invalid SQL and resized recovery.

Excluded: Remote databases, completion compatibility, styles and every SQL construct.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [insert-query](insert-query.json): Insert Unicode row through SQL and independently verify committed SQLite data | SQL>; 1 row affected; 3 rows in set; reviewed `insert-query.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [cancel-drop](cancel-drop.json): Reject destructive table removal and independently confirm rows remain | SQL>; destructive; Wise choice!; reviewed `cancel-drop.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [error-recovery](error-recovery.json): Reject invalid SQL then execute valid query after viewport resize | SQL>; no such table: missing_table; \| fixture_total \|; 1 row in set; reviewed `error-recovery.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |

Exact SQLite rows are independently queried. Actual result truncation and database corruption with normal-looking output are rejected. Public psql formatting is an intentional maintenance example.

Upstream contains a Windows-invalid tracked filename: acquire actual unmodified source on Linux. Use explicit target-supported PROMPT_TOOLKIT_NO_CPR=1; terminal queries remain a documented product boundary. Exclude timing rows through reviewed row snapshots.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
