# Continuation checkpoint v59: Taskell route diagnostics and complete artifact retention

Date: 9 November 2026. The campaign remains **5/20 new-project admissions on
rc.6; 15/30 cumulative**. Taskell is the sixth selected project and remains
unadmitted. The original ten are still 0/10 requalified on rc.6.

## Exact candidate run `42550352497`

Both hosts passed pinned upstream tests and built the native Taskell runtime.
Linux passed the public authoring route, all twelve candidate batches (21
scenarios each), and checked target cleanup. Its artifact ZIP had a verified
provider digest and passed ZIP integrity testing, but the 23-member packet
omitted the `final-series-native-exit-v1-v2` batch directory and the public
route output. This is recorded as zero-credit [exact attempt v41](taskell/final-series-attempts-v41.json).

macOS ARM64 failed the public route's first record command with exit 1, before
candidate batches; checked cleanup succeeded. Its packet did not include the
per-command `console.log` under `taskell/<attempt-id>/`, so the exact failure
cause is not yet known. Preserve this as a failed route, not a platform pass.

## Source fault run `42550352499`

Linux and macOS both passed all nine declared source-fault phases across three
faults, checked target cleanup, and restored the pinned source. Both artifacts
were independently audited without local ZIP retention: provider digests
matched; Linux ZIP integrity passed; all 18 per-host baseline/mutated/restored
reports matched their recorded SHA-256 values; all nine reports per host
confirmed cleanup; all mutated contracts failed as intended; baseline and
restored cases passed; and source restoration was true. [Fault attempt v8](taskell/fault-attempt-v8.json)
preserves the two-host pass with zero admission credit.

## Artifact-path correction and next actions

The local uncommitted workflow change broadens both Taskell artifact uploads
to include the complete `taskell/` evidence tree and campaign `events/`. This
will retain exact batch summaries, public-route receipts, and per-command
console logs. The change was checked by parsing both workflow YAML files and
running `git diff --check`. The public route's saved-board oracle and the
macOS `/tmp` alias correction are already in pushed commit `0a68aebb05f93d06ccd0310b940cd877e48bd9f9`.

Next, commit and push only the two workflow path changes and Taskell receipts
plus this checkpoint. Let the resulting Taskell native workflows run
serially. Inspect the macOS first-record `console.log` from its newly retained
artifact, fix the actual public-route issue, then rerun both hosts with complete
route and exact-series output retained. Independently audit each candidate
summary, report hash, runtime identity, cleanup result and the complete
scenario matrix before considering Taskell admission. Do not acquire project
seven (`mg`) before Taskell is admitted or explicitly closed as unsupported and
its workspace is checked clean.

Provider artifacts remain in GitHub; ZIPs were processed in memory and not
saved in the local workspace. Unrelated caches and Skim drafts remain
untouched and unstaged. Git Town's accidental run `42546285552` is canceled
before its scenario suite with a separate zero-credit receipt; do not rerun it
as part of this Taskell transition.

No 30/30 completion claim is made. Human usability remains unmeasured, and paid
admissions remain zero.
