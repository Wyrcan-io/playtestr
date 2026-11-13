# Runner readiness continuation checkpoint v163

## Cumulative status

The campaign remains **17/30 admitted**. Fzy's final rc.8 repeat matrix is
independently audited at 480/480 Linux/macOS outcomes. No fzy admission credit
is claimed yet.

## Preserved fault-workflow attempt

Workflow `43360846815` failed before any Playtestr scenario launched on either
host. The workflow acquired fzy once, then the calibration helper correctly
refused to acquire into the already-present active target. Its cleanup step
then used the report-required mode despite there being no scenario report.
Storage checks passed. The failed packets and provider digests are recorded in
`fzy/fault-calibration-attempt-run43360846815-v1.json`; scenario, fault,
cleanup and admission credit are all zero.

The corrective workflow removes its redundant source acquisition. Each phase
now performs its own acquire, pristine upstream build/test, optional isolated
fault build, one frozen scenario, and checked cleanup. The final recovery step
chooses no-case cleanup when a failed phase produced no runner reports. The
command wrapper also copies bounded helper output into the GitHub job log so
the next failure can be diagnosed without relying on artifact internals.

## Current local checks

The four fzy fault-calibration tests passed; the combined fzy scenario,
artifact-audit and cleanup suite passed 31 tests with three host-specific
skips. The corrected hosted workflow has not run yet.

## Remaining

Complete and independently audit the native baseline/fault/restored matrix.
Then finish fzy public authoring, maintenance, model controls and admission
review. Continue the remaining distinct project slots and original-ten
reconciliation until 30 admissions are supported by their full evidence.
