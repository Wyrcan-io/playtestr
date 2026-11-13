# Runner readiness continuation checkpoint v179

## Campaign status

The ledger remains **18/30 admissions**, with **2/20 new packages** admitted
(JOE and fzy). Percol remains at zero. Candidate remains
`v0.4.0-rc.8` (`native-exit-v3`).

## Percol attempt v6

Run `43384191533` passed N01 through N08 and E01 through E06 on both Linux amd64
and macOS arm64. E05's empty-input cancellation and E06's eager-count case
passed. E07's initial query case-sensitivity test failed the exact stdout check
on both: the UI kept both `Blue` and `blue`, and emitted `Blue`. The complete
provider-matching artifacts preserve the report and screenshots. Process,
workspace, source/runtime cleanup and storage checks passed. No final-matrix or
admission credit is earned from this partial run.

This confirms the case-sensitive option has the same initial-query/lazy-cache
ordering issue already observed for inverted matching. Both are recorded in
`percol/unsupported-controls-v2.json`; no claim is made about unrefreshed initial
query filtering for these modes.

## Current correction

V6 remains preserved. V7 removes E07's initial query: it first waits for the
visible `Blue` candidate, enters `blue` after CLI settings are active, waits for
the visible `1/1` result count, then selects and verifies exact lowercase output.
The v7 contract is materialized locally and not launched. Focused tests must be
rerun before committing the v6 attempt and v7 contract.

No local target runtime, process or mounted volume remains. First-failure ZIPs
stay in the ignored campaign `retained/` directory.
