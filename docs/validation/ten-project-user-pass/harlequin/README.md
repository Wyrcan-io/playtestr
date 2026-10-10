# harlequin: completed real-project trial

Upstream [tconbeer/harlequin](https://github.com/tconbeer/harlequin/tree/2c6e7b21d42e10b08730ca89b0cce2f40c42dab3), exact `2c6e7b21d42e10b08730ca89b0cce2f40c42dab3`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Real SQLite result grid, cancel save, recover from actual SQL error, save Unicode SQL.

Excluded: AI/agent features, non-SQLite adapters, remote files, clipboard and database-wide correctness.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [query](query.json): Execute actual SQLite query in editor and render ordered Unicode result rows | ^s Save Query; select name,quantity from items order by name;; café; reviewed `query-results.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [cancel-save](cancel-save.json): Cancel SQL buffer Save As modal and keep editing without writing a file | ^s Save Query; unsaved_value; Enter file path OR press ESC to cancel; reviewed `cancel-editor-row.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [error-recovery](error-recovery.json): Observe real invalid-query modal, dismiss it and successfully query after resize | ^s Save Query; select * from missing_table;; Query Error; no such table; Tab 2; select 314 as recovered_value;; Query Results (1 Records); reviewed `recovered-results.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [save-query](save-query.json): Save Unicode SQL buffer and independently verify exact file bytes | ^s Save Query; select 'café' as saved_value;; Enter file path OR press ESC to cancel; Saving to; Editor contents saved to; reviewed `saved-editor-row.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |

Assert full SQL and actual result caption/grid. An early mechanically passing recovery test only showed typed SQL and an error modal; visually rejected, retained and excluded from acceptance. Corrected new-buffer/error-dismissal flow really executes 314. Saved SQL bytes are independently checked.

General CtrlJ byte 0x0a differs from Enter 0x0d (53561e6). Cold startup needs an explicit bounded 15s application deadline. Timing toasts/completion are outside reviewed result rows; path prompts need unique Saving to evidence. Wrong save-path and UTF-8 edit attempts remain recorded.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 40 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 4 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
