# Runner readiness continuation checkpoint v164

## Cumulative status

The campaign remains **17/30 admitted**. Fzy's final rc.8 matrix is
independently audited at 480/480 ordinary Linux/macOS outcomes. Fzy is not yet
admitted.

## Fault calibration attempts

The fault declaration and calibration runner now retain exact source archives,
pristine and mutated build receipts/logs, reports, events, and per-phase source
removal/process proofs. The campaign attempt ledger at
`fzy/fault-calibration-attempt-run43360846815-v1.json` preserves three failed
native dispatches and their artifact digests.

Run `43360846815` stopped before case launch because the workflow duplicated
the helper's source acquisition. Run `43361379650` reached F01 baseline and
fault reports, then collided on the same immutable process-proof path across
phases. Run `43361636083` advanced through F01 and stopped at the first
corrupted F02 case. Run `43361837784` reproduced F02's actual failure:
`state_assertion_failure` at step 6, where the exact output-byte oracle caught
the wrong selected candidate. F02 is now declared against that observed
category and step. None of the partial executions earn calibration credit.

## Current state

The corrected F02 declaration, exact per-phase cleanup windows, report-bound
failure diagnostics, and retained cleanup proofs are committed locally and
awaiting/under the next standard native GitHub-hosted run. The five focused
fault-runner tests pass. The full fzy helper suite last passed 32 tests with
three platform-specific skips.

After the complete Linux/macOS three-fault baseline/corrupted/restored matrix
and its independent packet audit, fzy still needs public authoring,
maintenance, model controls, and admission review. Continue subsequent
eligible projects until the campaign reaches 30 evidence-backed admissions.
