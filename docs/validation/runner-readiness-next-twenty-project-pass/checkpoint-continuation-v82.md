# Runner readiness continuation checkpoint v82

Campaign remains **15/30 admissions**. Five new projects have candidate admissions, original-ten current requalification remains zero, and mg has no admission credit.

## mg development probes

Pinned target `troglobit/mg` at `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`, candidate `v0.4.0-rc.6`. N01 first-use and N02-N05 development probes passed on native Linux and macOS. N05?s successful workflow `42775438321` ran commit `05c11580a621ed0620a6b4128fd28da71671c1c5`. Both host reports show 27/27 steps passed, target exit 0, graceful confirmed cleanup, and exact same-invocation state outcome `matched`. Both retained downloaded artifacts pass ZIP CRC (41 members). Full host evidence: `mg/n05-native-readback-v1.json`.

N05 needed two corrected attempts; both failures remain in `mg/n05-first-attempt-readback-v1.json` and `mg/n05-second-attempt-readback-v1.json`. The corrected probe proves deletion, undo restoration, modified-marker consumption, redo, save, exit and exact-state assertion on both hosts. The report does not retain actual saved bytes or their hash; there is no independent saved-file readback.

N02-N05 development totals including every recorded rerun: 48 host attempts, 38 passed, 10 failed, four distinct scenarios with native passes. N01 pilot repeats across runs 42722834841, 42774674956 and 42775438321 are separately accounted in `mg/pilot-attempt-accounting-v3.json`. Current local storage observation is `artifacts/runner-readiness-next-twenty-project-pass/storage/e1ab9896a4054a0fb053cc98fe4cc0e1/observed.json`: combined retained 2,131,896,843 / 2,147,483,648 bytes, combined raw 3,973,497,586 / 6,442,450,944, curated 35,135,929 / 52,428,800 bytes; no cap exceeded. The latest hosted workflow storage step also passed. No higher qualification gate has been completed for mg.

Next: move to N06. Keep all dev probes separate from formal qualification; every project still requires exact full scenario matrix, repeated ordinary executions, native cells, calibration and real source faults, authoring/maintenance/relocation/CI/audit/storage/cleanup gates, then a complete admission audit before any credit.
