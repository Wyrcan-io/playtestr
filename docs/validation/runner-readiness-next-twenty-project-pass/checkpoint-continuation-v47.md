# Continuation checkpoint v47: 9 November 2026

Branch `work/p0-p2-implementation` is pushed at `5c207172`. The exact-candidate
ledger remains five of twenty new admissions (15/30 cumulative); original-ten
current-candidate requalification remains zero. Do not report the campaign as
complete.

## Skim

The repeated exact rc.6 run `42538203316` passed Linux and Windows. Provider
artifacts 13640617894 and 13641066494 were downloaded; their original ZIP sizes
and SHA-256 values match GitHub metadata. Independent `next20_skim_artifact_readback.py`
reconstructed all 240 contracts per host and verified 240 distinct passing
reports/invocations, three baseline/mutation/restoration faults (nine phases),
public first-use/diagnosis/maintenance/relocation, and checked cleanup. Immutable
repeat readbacks are in `skim/artifact-retrieval-readback-v16*.json`; attempt
v37 grants zero additional admission credit.

The prior artifact-readback helper was hardcoded to V28 plans and V34 declarations.
It now resolves each declaration and scenario contract by hashes frozen in the
plan and requires a unique native-host plan. Three regression tests cover exact
hash selection, missing subjects and ambiguous duplicate subjects. The V36
provider artifacts pass this independent audit. Temporary ZIPs and expansions
remain under `.runner-readiness-compaction-tmp/` until their tracked readbacks
and cleanup inventory are confirmed.

## Taskell

Build-only run `42540153182` passed pinned upstream tests and native target builds
on Linux amd64 and Intel macOS x86-64. It adds no final-series credit. Fault run
`42540153229` passed all nine Linux source-fault phases; macOS ARM64 failed before
Taskell cases because GHC 9.0.2's bundled `ffi.h` includes missing
`ffitarget_arm64.h` while building the `basement` dependency. The exact run log
and artifact IDs/digests are recorded in `taskell/build-attempt-v38.json` and
`taskell/fault-attempt-v5.json`. The earlier exact run `42538328742` has a passing
Linux series but its macOS leg failed before target cases; keep that failure.

The local, uncommitted correction proposes the official [GHC 9.2.8 aarch64
Apple Darwin binary](https://downloads.haskell.org/ghc/9.2.8/) with the same frozen nightly resolver, Stack lock and pinned Taskell
source. It keeps 9.0.2 available to preserve old attempt reproducibility. The
exact-candidate and fault workflows now name 9.2.8; a focused parser test and
workflow validator are wired into both. No 9.2.8 native run has started yet.
Focused helper tests previously passed 24 tests with three expected Windows
symlink capability skips; re-run after this checkpoint's final edits.

Next: finish local YAML/syntax/diff checks, commit and push the scoped audit and
Taskell compiler changes under existing authorization, then inspect the push
workflows. The final and fault workflows share a concurrency group; preserve any
cancelled/pending attempt and dispatch the second manually after the first
completes. Require both Linux and macOS ARM64 exact series and fault recovery to
pass before Taskell admission. Continue the remaining ten selected projects,
the original-ten transfer, migrations, controls, delivered CI, storage and
campaign closure.
