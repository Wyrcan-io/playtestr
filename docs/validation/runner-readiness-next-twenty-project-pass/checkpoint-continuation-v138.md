# Runner readiness continuation checkpoint v138

Campaign remains **16/30 cumulative admissions** and **6/20 new-project admissions**. JOE has **20 final-qualified scenarios, two native cells and 480/480 independently audited ordinary runs**, but **zero qualified source faults and zero admission credit**. The 18 native phases in v1 are preserved as an immutable failed calibration attempt; do not count them as audited calibrations.

## JOE v1 fault attempt: preserve false greens

- Workflow run `43042122414` at `e20f67e3d09b4fafdf20d45b1ae06bc7a6d875af` ran six native jobs and launched all 18 baseline/fault/recovery phases.
- The save-final-byte mutation passed N01 on both hosts; its low-level `bsavefd` mutation did not create the expected same-run state mismatch. These are two preserved false-green executions, not detections.
- The clean-exit mutation passed N01 on both hosts because it modified `ukilljoe`, while the tested CtrlK-X path is `uexsve`. These are two more preserved false-green executions.
- Forward-delete was rejected on N05 step 5 with `assertion_timeout` on both hosts, and both recoveries passed. The artifact retained the precise failed report and cleanup, but the acceptance helper then dereferenced a missing `run_bounded` result while writing the expected-fault receipt. The two calibrations remain incomplete and receive zero credit.
- All six job storage and owned-target cleanup steps passed. Provider artifact sizes/digests and classification are retained in `joe/fault-calibration-attempt-v1.json`; no original attempt was rewritten.

## Fresh v2 fault set

- `joe/fault-declaration-v2.json` freezes three distinct target mutations after the v1 evidence: the same forward-delete mutation with corrected receipt handling, a size omission in the actual named-save path, and a disabled modified-buffer CtrlK-X path.
- `joe/fault-declaration-source-readback-v2.json` verifies each unique patch against the pinned archive bytes. V2 has zero native launches so far.
- The calibration helper now falls back to the bounded command's recorded process-group cleanup when a declared expected target failure makes `run_bounded` raise. Added unit tests cover that path and v2 declaration integrity.

## General runner fix in progress

- Reproduction found that bare executable lookup uses the harness process PATH instead of the test's effective target PATH. Added a regression with different runner/target executables and updated resolution to use the spec environment and target working directory. Focused resolver and launch-failure tests passed. The full `internal/runner` suite passed on native Windows (143.377 s).
- This changes production source and requires exact source/build impact accounting and a rebuilt private candidate before any admission on the changed candidate. Existing rc.6 evidence remains tied to the old archive; no new candidate or project credit is claimed.

## Next

Finish the native candidate source/build qualification and freeze its exact host archives. Then run fresh JOE v2 baselines/faults/recoveries, independently retrieve and audit every v1/v2 artifact, complete JOE oracle/model controls, and requalify affected project and original-ten gates on the exact candidate. Continue the other remaining projects and campaign-wide closure afterward.
