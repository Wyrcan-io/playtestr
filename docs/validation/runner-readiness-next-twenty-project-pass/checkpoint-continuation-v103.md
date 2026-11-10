# Runner readiness continuation checkpoint v103

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E07 first native attempt and corrected oracle

Run `42788643494` failed on both hosts at step 7. Each captured screen shows `Reverting buffer notes.txt` after the missing-parent save-as attempt; the first contract waited for a transient low-level write error that the editor immediately replaced. Pinned-source review explains the sequence: `filewrite` clears old file attributes, `writeout` rejects the missing parent, then autorevert sees the cleared metadata and reloads the unchanged file. The report timed out before final-state steps ran; target shutdown was forced and confirmed, and workspace/owned-input cleanup succeeded. Failure artifacts are recorded in `mg/e07-first-attempt-readback-v1.json`.

The corrected contract expects the stable revert status and still asserts original bytes and the parent path absent. Focused local validation passed: 26 tests, four POSIX-only skips. Current total accounting includes this attempt: 258 host attempts, 244 passes, 14 failures, thirteen distinct passing scenarios. N01 pilot outcomes are separate. No qualification or admission gate is complete.

Next: run focused tests, push the correction with the preserved failure, validate both hosts, and audit the final file and directory absence checks.
