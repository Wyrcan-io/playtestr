# Runner readiness continuation checkpoint v156

## Cumulative status

The campaign remains **17/30 admitted**. fzy is still unadmitted; Pick's
separate admission review and campaign reconciliation remain open.

## fzy development run 43355826474

The corrected N06 passed. N01–N07 passed once on both Linux and macOS. N08
failed on both because the case expected output on the terminal screen while
`--show-matches` runs noninteractively and writes its sorted results to stdout.
Since the reviewed adapter redirects stdout to `result.txt`, no match text can
appear in the PTY screen. Cases N09–N20 did not run. Both native jobs passed
target cleanup, exact source restoration/removal and storage checks. Provider
identities are recorded in
`fzy/development-attempt-run43355826474-v1.json`.

N08 now uses the exact `result.txt` bytes (`cat\ncart\n`) and exact zero exit
status as its positive oracle. The declaration clarifies that rendered-screen
checkpoints apply to interactive cases; stdout bytes cover the noninteractive
filter case. A focused regression fixes this contract. The next run will execute
the complete matrix again rather than composing partial results from prior runs.

## Remaining

1. Complete and audit fzy's full native development and repeat matrices, source
   faults, public authoring and maintenance routes, model controls and exact
   candidate admission review.
2. Reconcile Pick's package and canonical campaign ledger without crediting
   partial evidence.
3. Continue the remaining new projects and inherited candidate/global gates to
   thirty actual admissions.
