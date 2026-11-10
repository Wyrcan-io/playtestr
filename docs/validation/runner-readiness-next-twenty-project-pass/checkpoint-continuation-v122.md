# Runner readiness continuation checkpoint v122

Campaign remains **15/30 admitted projects**. `mg` has zero exact-candidate qualification and admission credit.

## Exact-candidate series setup

- Series v1 (`mg/final-qualification-declaration-v1.json`) froze 20 canonical scenarios, 12 batches, two native hosts and 504 contract executions. The first workflow attempt was run 42819643394.
- That attempt's 12 Darwin jobs failed during GitHub job setup because the download-artifact action reference did not resolve. The workflow matrix also omitted the host dimension, so the Linux cells were never instantiated. No scenario command, target execution or qualification attempt started. Both pilot jobs passed separately; those remain development checks.
- The failed preflight remains preserved with zero contract attempts and zero qualification credit. Series v2 (`mg/final-qualification-declaration-v2.json`) explicitly supersedes it for that setup-only reason. It uses the repository's established download-artifact pin and an explicit 2-host × 12-batch matrix.
- The v2 focused helper suite passed 25 tests locally. The registered workflow parses as 24 matrix cells. Native v2 execution remains pending.

## Immediate next steps

1. Push the v2 declaration and workflow correction using the authorized branch workflow; verify 24 native jobs actually instantiate, then inspect setup and first batch receipts.
2. Preserve any first scenario failure without retries; audit successful artifacts against the exact runner, target, contract, host, exit, process cleanup and provider digest.
3. Finish every remaining `mg` qualification and admission gate before considering credit.
4. Continue the original-ten candidate requalification and remaining new projects. Campaign total remains **15/30**.
