# create-vite: completed real-project trial

Upstream [vitejs/vite](https://github.com/vitejs/vite/tree/8a4c19cfc035f2dd203f2fa6d00ab9256a5e77c9), exact `8a4c19cfc035f2dd203f2fa6d00ab9256a5e77c9`, MIT. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `53561e6cbef4c80a25893c2f25be5a0979442103`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.

Tested: Full React TypeScript wizard, cancel nonempty destination, recover invalid Vue package name.

Excluded: Network/custom starters, immediate install/dev server, credentials and generated-app runtime correctness.

| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |
| --- | --- | --- | --- |
| [react-ts](react-ts.json): Choose React TypeScript in actual multi-step scaffold wizard | Project name:; synth-react; Select a framework:; Select a variant:; Done. Now run:; reviewed `react.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [cancel-existing](cancel-existing.json): Cancel scaffold into nonempty directory and preserve exact existing Unicode file | is not empty. Please choose how to proceed:; Operation cancelled; reviewed `cancel-existing.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |
| [invalid-name-recovery](invalid-name-recovery.json): Reject invalid package name, recover after resize and scaffold correct Vue files | Package name:; Bad*Name; Invalid package.json name; valid-vue-name; Done. Now run:; reviewed `invalid-package.rows.json` | Committed tiny fixtures; temporary copied workspace, HOME and temp; independent exact bytes/command state before teardown | 10/10 |

Public --interactive --no-immediate --no-eslint, with no upstream test-only bypass. Independently compare full 18-file React and 15-file Vue manifests derived from pristine pinned templates. Exit-7 regression and corrupted package name despite success UI are rejected.

Retain @clack readiness checkpoints and package-name validation; snapshot final commands without random absolute destination. Native portable Node and task-local pinned pnpm build actual source; no global installs.

The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.

Final qualification: 30 fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all 3 scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).

Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.

Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.

Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.
