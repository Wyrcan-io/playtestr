# Runner readiness continuation checkpoint v120

Campaign remains **15/30 admitted projects**. `mg` has zero qualification and admission credit.

## Completed on this continuation

- E12 run 42798471734 passed the complete development workflow on Linux amd64 and macOS arm64. Scenario development accounting v30 recorded 604 host attempts, 580 passes and 24 preserved failures.
- Run 42810801431 repeated all 20 canonical development scenarios on Linux and macOS: 40 host attempts passed, with 602 assertion steps, graceful confirmed target cleanup and absent runner process groups. The separate N01 first-use pilot passed on both hosts with matched same-invocation state, graceful cleanup and cleaned workspaces. Provider ZIP hashes and CRCs were verified. Scenario accounting v31 now includes the 40 repeats: 644 attempts, 620 passes and 24 failures. These remain development observations.
- Native source build run 42810801391 passed on Linux and macOS. Native adapter run 42810801477 passed on Linux, macOS and Windows.
- Fault run 42804421593 passed its eight pristine baselines, then failed cleanup before mutations because generated Autotools symlinks were rejected. Its eight artifacts and zero calibration credit are preserved in `mg-fault-calibration-first-attempt-readback-v1.json`.
- Fault run 42805846400 calibrated save suppression, deletion byte corruption and undo deletion omission on Linux and macOS. The original read-only mutation targeted `ldelete` instead of the E06 `linsert` path and passed unexpectedly on both hosts; those false negatives remain preserved without credit in `mg-fault-calibration-readback-v1.json`.
- Corrected fault run 42811359525 passed all eight cells: four distinct source mutations across Linux amd64 and macOS arm64. Every pristine baseline passed, each mutation triggered the expected public-contract failure, and every restored-source recovery passed. The 126-file pinned source map was verified and all 24 owned source trees were removed. All eight provider ZIPs match their SHA-256 digests and pass CRC. See `mg-fault-calibration-readback-v2.json`.
- The corrected read-only mutation removes only the exact `linsert` BFREADONLY guard; the focused Windows suite passed 32 tests with four POSIX-only skips. The harness, source reviews, attempt accounting and phase-level readbacks are committed and pushed.

## Open

- Complete the required qualification matrix for `mg`; the development and fault-calibration runs above do not count as admissions.
- Requalify the original ten projects against exact candidate `v0.4.0-rc.6`.
- Continue the remaining new-project admissions, required ordinary and calibration runs, delivered-workflow journeys, candidate checks, maintenance and relocation controls, and final audits.

Next: preserve the corrected calibration records, then continue the exact-candidate qualification and remaining independent project packages. Current total remains **15/30**.
