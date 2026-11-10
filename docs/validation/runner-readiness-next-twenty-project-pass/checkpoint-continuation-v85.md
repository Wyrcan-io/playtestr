# Runner readiness continuation checkpoint v85

Campaign remains **15/30 admissions**. mg currently has five distinct selected development scenarios passing on Linux/macOS (N02-N06), N01 first-use pilot is also passing, and no formal project admission credit. N02-N06 totals: 58 host attempts, 48 passed and 10 failed; every failed attempt is preserved.

## N07 prepared

N07 opens a second fixture file with `C-x C-f`, checks its unique screen text, switches explicitly to `first.txt` with `C-x b`, confirms the first-buffer screen text, exits, and asserts both exact fixture files unchanged. `filevisit`, `usebuffer`, their source-level key bindings, prompt names and buffer names were reviewed at the exact mg pin. Details: `mg/n07-source-review-v1.json`; spec and fixtures: `mg/n07-buffer-switch.json`, `mg/fixtures/n07-buffer-switch/`.

The focused local mg contract/build/pilot suite passes (18 tests, 4 POSIX-only skips). N07 native validation is pending. Next: commit/push and run the Linux/macOS workflow; audit actual reports, both file states, process cleanup, provider artifacts, ZIP CRC and storage; then continue N08.
