# Runner readiness continuation checkpoint v113

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E10 and E11 current state

Run 42795656864 passed the overwrite-decline variant on Linux and macOS: all 14 steps and both exact file-state assertions passed, with target exit 0 and graceful cleanup.

The accepted-overwrite variant passed 18 steps and exited 0 on both hosts, but its exact destination-byte assertion failed. The contract inserted an unnecessary Enter after typing `accepted edit`, creating an extra blank line. That failure and both provider artifacts are retained in `mg/e10-fourth-attempt-readback-v1.json`; observed file bytes are not retained by the report. E10b now omits that Enter while preserving the reviewed expected final newline.

E11 is included in the next full run. It resizes to 60x16, waits for fresh output, then edits, saves and checks exact bytes. Its contract also avoids adding a redundant trailing line. Both cases have pinned-source reviews.

Focused local tests passed 31 tests with 4 host-specific skips; `git diff --check` passed. Storage passed: retained 2,135,105,363 bytes; raw 3,976,706,106 bytes; curated 35,622,573 bytes. Totals through run 42795656864: 17 distinct passing scenarios, 486 host attempts, 464 passes and 22 failures. Qualification and admission gates remain open.

Next: push the corrected E10b and E11 contracts, verify both native host results and artifacts, and continue the remaining mg edge workflows.