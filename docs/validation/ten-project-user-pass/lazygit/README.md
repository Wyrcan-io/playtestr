# lazygit: completed real-project trial

Upstream [jesseduffield/lazygit](https://github.com/jesseduffield/lazygit/tree/c5f7158154602d23b0750d4304c73e2aead8df5b), exact `c5f7158154602d23b0750d4304c73e2aead8df5b`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Stage a file, cancel discard, create and independently inspect a local commit.

Excluded: Remotes, credentials, hooks, signing, conflicts and every Git operation.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [stage](stage.json): Stage a modified file and independently verify the Git index |  M seed.txt; M  seed.txt; reviewed `stage.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [cancel-discard](cancel-discard.json): Cancel destructive discard and prove worktree content remains modified |  M seed.txt; Discard all changes; reviewed `cancel-discard.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [commit](commit.json): Stage and commit a local change, independently verifying the commit subject |  M seed.txt; M  seed.txt; Commit summary; No changed files; reviewed `commit.txt` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |

A trusted synthetic launcher creates a local repository with fixed identity/date, no hooks/signing/remotes. Index blob, canceled file, commit subject, committed blob and clean status are independently checked. Real add-to-reset mutation fails.

Portable explicit PATH setup replaces an operator-machine binary path; synthetic Git fixture modes and LF bytes are explicit. A real Git regression proved identical commits from 0644/LF and 0755/CRLF inputs after the fix. Only changed synthetic commit hashes were deliberately reviewed in selected baselines, then all scenarios were requalified. Intentional unstaging is reviewed separately from defect recovery.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
