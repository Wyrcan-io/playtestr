# Runner readiness continuation checkpoint v110

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E09 pass evidence

E09 passed in run 42791533584 on Linux x86_64 and macOS arm64. Accounting through E09: 16 distinct passing scenarios, 348 host attempts, 334 passes and 14 preserved failures. See `mg/e09-native-readback-v1.json` and `mg/scenario-development-accounting-v23.json`.

## E10 preserved failures and current contract

- Run 42793018573: E10a failed `invalid_spec` on both hosts because the public key action does not accept single-letter `n`; neither target was launched. E10b was not run. Readback: `mg/e10-first-attempt-readback-v1.json`.
- Run 42793902259: E10a timed out on both hosts waiting for overwrite confirmation because the filename prompt had not been submitted. Both targets were force-stopped and confirmed exited; workspaces and workflow inputs were cleaned. E10b was not run. Readback: `mg/e10-second-attempt-readback-v1.json`.

Both first failures and provider ZIPs are retained with verified hashes and CRCs. Contracts now send literal `n`/`y`, press Enter to submit the filename, and expect the stable `exists; overwrite` prompt substring. Focused local suite passed 30 tests with 4 host-specific skips; `git diff --check` passed. Storage check passed: retained 2,134,689,211 bytes; raw 3,976,289,954 bytes; curated 35,578,444 bytes.

Totals through the second E10 attempt: 16 distinct passing scenarios; 416 host attempts; 398 passes; 18 failures. Qualification remains zero; mg admission credit remains zero.

Next: push and verify both E10 variants on Linux/macOS, including the decline state and accepted overwrite bytes; then continue E11/E12.