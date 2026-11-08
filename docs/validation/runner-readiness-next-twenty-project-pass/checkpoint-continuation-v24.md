# Continuation checkpoint v24 — 8 November 2026

Branch `work/p0-p2-implementation`; Taskell correction and paired failure
evidence are committed and pushed in `5ec01145e2c9b1ddcbf0ac203bd8d843397c5a0b`.
The campaign remains incomplete: four new projects are admitted (14/30 total).

## Taskell qualification

Taskell is pinned to
`smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`, with
151 primary source blobs verified. It is the sole active target; do not start
another project until its full evidence and checked cleanup close.

Run `42456298245` passed the pinned 250-test suite and the authored plus public
recorder/replay/export/ordinary-test route on Ubuntu 24.04 and macOS 15 Intel.
This is one first-use observation on each host, not a scenario series, native
cell, fault calibration, or admission. Exact receipts remain in
`taskell/build-attempt-v18.json` and `build-attempt-v19.json`.

Run `42458747709` passed its pinned 250-test suite and existing-task smoke on
both native hosts, then failed the uncredited create-task candidate at step 1
on both. The candidate requested `board.md`, while the fixture contained
`board-basic.md`; both final screens show Taskell's create-missing-board
prompt. Both reports confirm process-group termination and workspace cleanup.
Exact provider artifacts, host/binary identities, report/screen digests and
the curated evidence paths are in `taskell/build-attempt-v20.json`. The
candidate now points to `board-basic.md`. This was a test-spec setup error,
not a Taskell defect and earns no create-task credit.

Run `42460993289` is the first native attempt with that correction and the
separately isolated duplicate-task candidate in the workflow. At checkpoint
creation, Ubuntu job `128670059694` and Intel macOS job `128670059826` are
both still in the pinned upstream test/build stage. Poll both through final
completion. Inspect each candidate's report, saved bytes, process cleanup and
workspace cleanup before assigning even one-case evidence credit. If creation
fails, do not accept the duplicate result as a substitute.

The catalog in `taskell/scenario-catalog-draft-v1.md` is still unfrozen. It
proposes eight normal and twelve edge/adversarial cases and three candidate
source mutations. Validate actual Taskell behavior and exact board bytes,
then freeze a revisioned catalog before the full 20-case x 2-host x 12-repeat
series, three real fault baseline/mutant/restored phases per host, calibration,
maintenance, relocation, audits, final candidate and checked cleanup. No
Taskell scenario-series, native-cell, fault-calibration, or admission credit
is recorded.

## Storage and boundaries

Storage checkpoint v19 (`storage-checkpoint-v19.json`) passed declared logical
caps with 151,279 bytes of combined-retained headroom before the v20 evidence
was added. The two full workflow artifact extractions were curated down to
reports, screens, runner and host identity files; their native binaries were
hashed and the exact temporary extraction directories removed. Measure
storage again before adding further retained evidence. Historical observations
remain losslessly packed and indexed as recorded in v19.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Standard hosted native workflow runs and commit/push are authorized.
