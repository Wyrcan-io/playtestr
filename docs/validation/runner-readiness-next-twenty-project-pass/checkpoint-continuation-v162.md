# Runner readiness continuation checkpoint v162

## Cumulative status

The campaign remains **17/30 admitted**. Fzy's exact rc.8 final archive is now
independently audited at 480/480 ordinary executions across Linux amd64 and
macOS arm64. It has no project admission credit yet. Pick also remains
unadmitted pending its project-package and ledger reconciliation.

## Fzy source faults in progress

`fzy/fault-declaration-v1.json` freezes three distinct source changes against
the exact pinned source archive and the frozen rc.8 candidate:

* F01 removes the selected output newline; N01 must fail its exact captured
  output state at step 4.
* F02 makes down navigation a no-op; N05 must time out at its second candidate
  checkpoint, step 3.
* F03 skips applying the typed query; N02 must emit the wrong candidate and
  fail the exact captured output state at step 4.

Each fault is run in baseline, corrupted and restored phases on both native
hosts. Every phase reacquires the pinned source and passes its 32 upstream
tests before Playtestr runs. The corrupted binary is built from an isolated
copy after an exact one-region source replacement; pristine source remains
unchanged. Pristine and mutated build logs, source and binary copies, runner
reports, events, candidate hashes and cleanup receipts are retained. No fault
credit is available before provider artifact and report readback.

The local contract suite passed four fault-runner tests, the existing 24 fzy
scenario/artifact-audit tests, and the target-cleanup suite (31 total, three
platform-specific skips). The native matrix has not run yet. Its workflow is
`.github/workflows/runner-readiness-next20-fzy-fault-calibration.yml`.

## Remaining gates

After the hosted fault matrix and independent audit, fzy still needs its public
authoring route, maintenance route, model controls, and admission review. Then
continue distinct eligible projects and reconcile the original-ten work until
30 total admissions are evidenced. Do not count the scenario repeats as
project admissions or infer saved-state coverage from fzy's stdout capture.
