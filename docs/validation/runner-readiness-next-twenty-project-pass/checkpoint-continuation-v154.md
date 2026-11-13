# Runner readiness continuation checkpoint v154

## Count

The campaign remains **17/30 admitted**. Pick's package review and campaign
reconciliation remain pending; fzy has not yet run any Playtestr scenarios.

## fzy retry outcome

Run `43354855944` acquired the selected source on both Linux and macOS and then
failed before the build command started: `next20_fzy_build.py` referenced `DOC`
without importing it. Both hosts took the corrected explicit no-case cleanup
path, proved checked source removal, and passed the campaign storage check.
There were zero candidate installations and zero scenarios. Provider identities
and the failure are preserved in
`fzy/development-attempt-run43354855944-v1.json`.

The missing import is fixed. The focused tests now import the build module,
validate the pinned provenance path/archive, exercise exact compiler `.d` and
macOS `.dSYM` cleanup, and refuse unknown files. The corrected workflow should
now progress through upstream build/tests and then the frozen 20-case one-time
development matrix. No fzy scenario, cell, fault or admission credit is claimed.

## Remaining

Retry and independently read back the full Linux/macOS artifacts. Preserve every
first failure, then finish fzy faults, public authoring/update route, model
controls, project admission review, the remaining selected projects and global
campaign gates.
