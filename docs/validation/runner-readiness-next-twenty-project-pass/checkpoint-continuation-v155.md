# Runner readiness continuation checkpoint v155

## Cumulative status

The campaign remains **17/30 admitted**. Pick remains pending package review and
campaign reconciliation. fzy is the active project and has no admission credit.

## fzy development run 43355127321

The exact pinned source built, passed all 32 upstream tests, and installed on
Linux and macOS. Playtestr cases N01–N05 each passed once on both hosts. N06
failed on both at its first screen assertion: the authored query `bluz` matched
no candidate, so the test timed out before it reached the intended Backspace
action. The retained screens show only `> bluz`; this is a scenario-authoring
failure, not a runner defect. N07–N20 did not run. Both hosts confirmed target
cleanup, exact source removal and bounded campaign storage. Provider artifact
identities and the failure are preserved in
`fzy/development-attempt-run43355127321-v1.json`.

N06 now types the valid unique query `blue`, confirms its rendered match, sends
Backspace, and confirms `blue` remains the unique match before selection. A
focused regression test binds this intended order and exact stdout bytes. The
next push-triggered workflow reruns all twenty cases on both native hosts; prior
passes will not be merged into that run as if they were one matrix.

## Remaining

1. Pass and independently audit the complete fzy development matrix on both
   hosts, then run its repeat matrix, real source faults, public authoring and
   maintenance routes, model controls, and exact-candidate admission review.
2. Reconcile Pick's project package and canonical ledger without inferring
   admission from its route or model-control milestone.
3. Continue all remaining projects and inherited candidate/global gates until
   thirty distinct admissions are complete or a real external block remains.
