# Runner readiness continuation checkpoint v94

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E03 first native attempt and correction

Run `42782907773` failed on both Linux and macOS at step 9. Both hosts passed the newline-join screen check and sent save; the report's captured screen shows that the long workspace path clipped the filename in the status line. The full `Wrote notes.txt` expectation therefore timed out, and cleanup forcibly terminated the editor after the assertion deadline. The workspace and owned workflow inputs were cleaned. Failure artifacts and provider ZIP digests are recorded in `mg/e03-first-attempt-readback-v1.json`.

The revised contract now checks the visible `Wrote ` prefix; the exact final file state assertion remains. Review v2 binds the corrected contract hash and explains the failure. Focused local tests passed: 22 tests, four POSIX-only skips. This failure adds 20 host attempts: 18 prior scenarios passed again, E03 failed on both hosts. Totals are 138 host attempts, 108 passes, 12 failures and nine distinct passing scenarios. N01 pilot accounting is separate. No qualification or admission gate is complete.

Next: run local contract checks, commit and push the correction with the preserved failure evidence, then rerun native Linux/macOS validation. Preserve the failed attempts and update counts only after inspecting the corrected run artifacts.
