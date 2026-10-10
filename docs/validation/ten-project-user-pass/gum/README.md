# gum: completed real-project trial

Upstream [charmbracelet/gum](https://github.com/charmbracelet/gum/tree/879f048103adf0214b85943b52d8d65b08d772c5), exact `879f048103adf0214b85943b52d8d65b08d772c5`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Selector, confirmation, Unicode input, resize and length enforcement.

Excluded: Shell pipelines, passwords, styling, every Gum subcommand and mouse input.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [choose](choose.json): Choose the second release category, not the default | Choose:; reviewed `choose.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [decline](decline.json): Decline a destructive confirmation with exact nonzero status | Deploy fixture?; reviewed `decline.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [input](input.json): Enter and submit a Unicode project label | Project label; café; reviewed `input.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [resize](resize.json): Resize and verify cursor selection before accepting output | Choose:; > beta; reviewed `resize.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |
| [limit](limit.json): Enforce application input length without silently truncating the test contract | Code; abc; reviewed `limit.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp | 10/10 |

A real choose-output prefix mutation is rejected. A separate gamma selection demonstrates reviewed baseline maintenance. Exact decline exit 1 is declared.

No generalized core defect discovered by these Gum scenarios.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 50 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 5 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
