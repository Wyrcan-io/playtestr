# fzf: completed real-project trial

Upstream [junegunn/fzf](https://github.com/junegunn/fzf/tree/b1be3a8be1b833ce5b92fbbac11637643d60a046), exact `b1be3a8be1b833ce5b92fbbac11637643d60a046`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Search across 1,004 synthetic entries, cancellation and resized Unicode selection.

Excluded: External preview commands, personal shell integration, filesystem crawling and mouse interaction.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [search](search.json): Filter 1004 choices and select an exact nondefault item | Find:; Find: beta; reviewed `search.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [cancel](cancel.json): Cancel selection without returning a chosen item | Find:; reviewed `cancel.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [resize](resize.json): Resize filtered Unicode search and preserve matching result | Find:; Find: café; reviewed `resize.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |

Synthetic alpha/beta/gamma/café entries plus 1,000 filler entries; exact cancellation exit 130. Actual emitted-result prefix regression fails unchanged tests.

A mutation-build helper initially decoded UTF-8 through Windows legacy encoding; retained as operator error and corrected.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
