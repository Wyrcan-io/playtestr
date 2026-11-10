# Runner readiness continuation checkpoint v109

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E09 evidence closed

E09 passed on Linux x86_64 and macOS arm64 in run 42791533584. Readback and verified provider ZIPs are recorded; the scenario ledger includes 348 host attempts, 334 passes and 14 preserved failures through E09. See `mg/e09-native-readback-v1.json` and `mg/scenario-development-accounting-v23.json`.

## E10 first attempt and correction

Run 42793018573 preserved the 32 successful N02-N08/E01-E09 host executions, then failed E10a validation on both hosts because the spec used unsupported single-letter `key` names. Both reports say `invalid_spec`; `target_attempted` is false. E10b was not run. The provider ZIP digests and CRCs are verified and the first attempt is retained in `mg/e10-first-attempt-readback-v1.json`.

E10a now uses literal text `n`; E10b uses literal text `y`, consistent with the public key/text contract. Source review hashes are refreshed. Focused local tests passed 30 tests, with 4 POSIX-only skips; `git diff --check` passed. Latest storage check: combined retained 2,134,487,004 bytes; combined raw 3,976,087,747 bytes; combined curated 35,559,425 bytes.

Scenario totals through the first E10 attempt: 16 distinct passing scenarios; 382 host attempts; 366 passes; 16 failures, including the two preserved E10a invalid-spec attempts. Accounting: `mg/scenario-development-accounting-v24.json`. No qualification or admission gate is complete.

Next: push the corrected E10 contracts with the preserved first-failure audit, verify the full Linux/macOS rerun and all artifacts, then continue E11/E12.