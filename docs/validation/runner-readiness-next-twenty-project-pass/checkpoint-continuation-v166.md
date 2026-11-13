# Runner readiness continuation checkpoint v166

## Status

The campaign remains **17/30 admitted**. Fzy's ordinary 12-repeat matrix is
independently audited; its source-fault work is not yet complete or credited.

## F03 correction

Run `43362667605` completed both native source-fault jobs through F01 and F02,
then failed before F03's Playtestr scenario. It showed the first F03 mutation
only removed later search updates; N02 uses an initial `--query`, whose
selection is initialized separately, so the scenario correctly passed.

F03 now replaces the `choices_search` query argument with an empty string
during initialization. That is a real source fault expected to select the
wrong result, which N02 catches in its exact output-byte check at step 4. The
new mutated source digest was recomputed from the exact pinned source bytes.
Run and provider artifact hashes remain in
`fzy/fault-calibration-attempt-run43360846815-v1.json`, with zero partial
credit.

The independent artifact auditor is implemented and its ZIP-boundary tests
pass. The full fzy helper suite passed 35 tests with three host-specific skips
before the latest change. Rerun the focused suite, then dispatch the complete
corrected matrix and audit both packets before continuing the public route,
maintenance, model controls and admission package.
