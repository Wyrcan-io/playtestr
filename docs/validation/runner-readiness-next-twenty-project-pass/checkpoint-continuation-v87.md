# Runner readiness continuation checkpoint v87

Campaign remains **15/30 admissions**. N01 first-use and N02-N07 development probes pass on native Linux/macOS. N02-N07 counters: 70 host attempts, 60 passed, 10 failed; N05 failures preserved. mg has zero admission credit.

## N08 prepared

N08 fixture begins with UTF-8 `caf? wide: ?`, appends ` ?`, checks exact rendered text before and after, saves, exits and asserts exact UTF-8 bytes. The contract explicitly sets `LANG` and `LC_CTYPE` to `C.UTF-8` because pinned mg calls `setlocale(LC_CTYPE, "")` before UTF-8 detection. Source review covers the pinned locale setup, decoder and double-width renderer. Contract: `mg/n08-utf8-wide.json`; source review: `mg/n08-source-review-v1.json`.

A local PowerShell pipeline initially corrupted literal Unicode to `?`; the contract and fixture now use verified escaped Unicode generation, the bytes were checked as UTF-8, and all 19 focused tests pass with four POSIX-only skips. N08?s native locale behavior remains unverified; run the Linux/macOS workflow and inspect any locale or render failure directly.
