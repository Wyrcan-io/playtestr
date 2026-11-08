# Continuation checkpoint v57: Taskell V2, declaration rebinds and storage recovery

Date: 9 November 2026. The ledger remains **5/20 new projects on exact rc.6; 15/30
cumulative**. Skim remains admitted. Taskell, Git Town's current candidate, and
Skim's current candidate remain open pending their independent requirements.

## Taskell native V2 attempts

Final series run `42533986467` passed all twelve Linux batches (252 ordinary
executions) and checked cleanup. Its macOS job stopped before Taskell build or
case launch when the signature-verified ICU package contained
`opt/local/sbin/gennorm2`; checked no-case source cleanup and artifact upload
passed. Separate fault run `42533986457` passed its Linux job and stopped at the
same macOS preparation path; checked no-case cleanup and fault artifact upload
passed there too. The provider packets and zero-credit outcomes are recorded in
[`build-attempt-v37.json`](taskell/build-attempt-v37.json) and
[`fault-attempt-v3.json`](taskell/fault-attempt-v3.json). V1's eleven wrapped
diagnostic failures remain unchanged. The bounded extractor now recognizes
signed `opt/local/sbin` package contents as unmaterialized support files; a
focused test asserts the exact `gennorm2` behavior. On this Windows host the
focused Taskell/cleanup suite ran 22 tests: 18 passed and four platform-capability
symlink checks skipped. A fresh macOS run remains required; Linux results still
need full packet audit before any Taskell admission.

## Skim and Git Town failed final attempts

Skim run `42533986434` failed both hosts at contract freeze, before target
execution, because V34's helper hash predated the committed
`next20_jrnl_final.py` change. Git Town run `42533986432` built the pinned target
and installed the exact archive on both hosts, then refused cases for the same
stale shared-helper binding. Checked cleanup completed. Both are retained as
zero-credit attempts in [Skim V35 attempt](skim/final-series-attempts-v35.json)
and [Git Town V25 attempt](git-town/final-series-attempts-v25.json). New
immutable V35 and V31 declarations rebind current harness bytes under fresh
plan identities while preserving candidates, contracts, batches, and fault
expectations. The declaration generators and execution helpers are being staged
and checked before fresh native dispatch.

## Storage recovery

The latest prior checkpoint exceeded the 2 GiB retained cap by 862,018 bytes.
An exact-content compactor inventoried the local control evidence and found 73
duplicate groups (279 paths, 1,523,628 source bytes). It wrote a one-blob-per-hash
XZ packet with original path, SHA-256, byte count, mode, and nanosecond mtime for
each alias. The complete packet passed byte-level readback before the native
PowerShell remover rechecked every source path/hash/type/ancestor and deleted
only those 279 aliases. All source paths are now absent, the packet reads back
completely, and the removal receipt binds the packet/index/plan. V1 global
duplicate evidence was not modified.

The exact packet is local-only at
`artifacts/runner-readiness-next-twenty-project-pass/duplicate-control-tests-v1/`.
Index SHA-256:
`ab25101762e598569639c0ad5d0e5b500f5074277fa436bcc95e1b5a9bcbce2f`;
archive SHA-256:
`44e4d4afcd7c003643e2743addc0441191de677632fd9ecb69d0205b01e4dcc6`.
Compactor readback controls passed four tests; the native PowerShell remover
parsed and completed successfully. The resulting storage observation is
[`storage-checkpoint-v42.json`](storage-checkpoint-v42.json): 2,146,972,546
retained bytes, 511,102 bytes below the 2 GiB logical cap. This is a point-in-time
observation, not an exact disk-allocation or peak claim. Keep the storage gate
open while new provider artifacts are collected and compact them before further
acquisition.

## Immediate next work

1. Complete review of the V31/V35 declaration source bindings and validate all
   affected Python, PowerShell, workflow YAML and diff checks.
2. Preserve and independently audit the completed Taskell, Skim, Git Town,
   source-development and harness workflow artifacts in bounded local packets;
   do not count a provider conclusion as packet proof.
3. Commit/push the reviewed successor declarations, Taskell sbin fix and exact
   compaction tooling, then monitor fresh native Git Town V31, Skim V35 and
   Taskell V2 Linux/macOS runs. Preserve every superseded attempt and never count
   reruns as new scenarios.
4. Continue the remaining selected projects only while storage and target
   cleanup gates pass. The original ten still need qualification on rc.6;
   migrations, public controls, delivered-CI triplets, fresh checkout,
   independent model tampering and final all-attempt reconciliation remain open.

No 30/100 completion claim is made. Human usability remains unmeasured, and paid
admissions remain zero.
