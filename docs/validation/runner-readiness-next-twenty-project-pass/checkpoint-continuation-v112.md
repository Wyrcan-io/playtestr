# Runner readiness continuation checkpoint v112

Campaign remains **15/30 admissions**; mg has zero admission credit.

## Preserved E10 history

The three failed E10a attempts remain recorded: run 42793018573 rejected unsupported `key: "n"` before target launch; run 42793902259 timed out before filename submission; run 42794710358 reached the overwrite confirmation but the long absolute path clipped its suffix. The last two runs force-stopped and confirmed target exit on both hosts. Each provider ZIP is retained with provider-matched digest and passing CRC. Readbacks: `mg/e10-first-attempt-readback-v1.json`, `mg/e10-second-attempt-readback-v1.json`, `mg/e10-third-attempt-readback-v1.json`.

E10 now answers with literal text, submits the filename with Enter, and asserts the visible `File backtick` confirmation prefix. E10b separately tests accepting overwrite after an edit. E11 resizes the PTY, waits for redraw output, then edits, saves and checks exact bytes; pinned-source review covers SIGWINCH handling and redraw.

Focused suite passed 31 tests with 4 host-specific skips; `git diff --check` passed. Storage passed: retained 2,134,891,448 bytes; raw 3,976,492,191 bytes; curated 35,602,617 bytes. Through run 42794710358: 16 distinct passing scenarios, 450 host attempts, 430 passes, 20 preserved failures. Qualification and admission gates remain open.

Next: push the visible-prefix E10 and E11 contracts; verify Linux/macOS results and artifacts; continue E12.