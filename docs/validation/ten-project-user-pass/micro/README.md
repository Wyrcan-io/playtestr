# micro: completed real-project trial

Upstream [micro-editor/micro](https://github.com/micro-editor/micro/tree/02164788bd29c90456e39f976a566899d39579e4), exact `02164788bd29c90456e39f976a566899d39579e4`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Unicode save, discard without saving, regex search and resized cursor location.

Excluded: Plugins, system clipboard, arbitrary languages, remote files and editor-wide compatibility.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [save](save.json): Edit Unicode content, save, and independently inspect exact disk bytes | seed alpha; Saved notes.txt; reviewed `save.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [discard](discard.json): Refuse saving unsaved changes and verify original disk state | seed alpha; Save changes; reviewed `discard.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [search](search.json): Search a noninitial line after resize and inspect the result | seed alpha; Find (regex):; (2,7); reviewed `search.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |

Exact original and saved notes bytes are checked before workspace teardown. A source mutation suppresses the real Saved notification; another corrupts real saved bytes despite success UI.

Recorder rerecord printed a stale working directory. Fixed generally in 06af0c0 with a failing-before/passing-after regression. Manual-edit encoding mistakes were also rejected.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
