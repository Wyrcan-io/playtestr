# Runner readiness continuation checkpoint v116

Campaign remains **15/30 admissions**; mg has zero admission credit.

## E12 first attempt preserved

Run 42797676328 passed N02-N08 and E01-E11 again on both hosts, then E12 timed out at step 8. The contract expected `Modified buffers exist; really exit`, but pinned `quit` first asks `Save file <path>` through `anycb(FALSE)`. Both targets were force-stopped and confirmed exited, and hosted input cleanup passed. Provider ZIP digests and CRCs are recorded in `mg/e12-first-attempt-readback-v1.json`.

E12 now expects `Save file`, answers `n`, then expects and declines the modified-buffer exit prompt. It confirms the unsaved edit remains, saves, exits and checks exact bytes. The source review covers both prompts in source order.

Focused tests passed 32 tests with 4 POSIX-only skips; `git diff --check` passed. Storage check passed: retained 2,135,567,157 bytes; raw 3,977,167,900 bytes; curated 35,688,787 bytes. Totals through the first E12 run: 19 passing scenarios, 564 host attempts, 540 passes, 24 failures.

Next: push and audit E12 on Linux/macOS, then continue the campaign's candidate qualification and remaining project packages.