# Continuation checkpoint v56: Skim admission and Taskell wrapped-output diagnosis

Date: 9 November 2026. Overall new-project count is **5/20 on exact rc.6; 15/30
cumulative**. The original ten remain unqualified on rc.6. Global closure is
still open.

## Skim admission

Skim is now the fifth new project admitted on exact rc.6. The new
[admission receipt](skim/admission.json) binds the same successful V35 native
run and provider-digest-bound V15 readbacks, 480 ordinary executions, 18
positive/mutated/restored fault phases, 24 rejected semantic corruptions, both
Linux and Windows cells, the public prepared-agent route (3 shell invocations,
8 recorder controls), diagnosis, maintenance, Unicode relocation and checked
cleanup. Delivered workflow execution and human usability remain unmeasured.
ArrowDown/Ctrl-N navigation and exact raw NUL framing remain unverified. V35 is
a repeat of V34 and adds no scenario breadth. The exact-candidate ledger now
shows 5 projects, 2,400 ordinary executions, 90 calibrations, 10 native cells
and 15 real source faults. Two pre-final admission draft receipts remain in
local review state and carry no credit; they are excluded from the final
admission subject set. Only `skim/admission.json` is current.

## Taskell V35 and V36

Run `42531548193` on commit `bb4572f5686ad892189103ddd9015e540e040198` is recorded
in [build attempt v36](taskell/build-attempt-v36.json). Linux built Taskell and
passed the upstream suite, but E11M failed in eleven standard-width batches and
passed in the widened batch. The provider artifact was downloaded to the
protected workspace-local `.codex-test-tmp/taskell-v36-linux/` and audited at
the report/screen level. Its 80-column actual screen wraps the diagnostic as
`Could` followed by `ld not parse file.`; the frozen exact phrase therefore
cannot match. Exit 1 and unchanged-file assertions remain appropriate.

The v2 contract is frozen under
`taskell/host-contracts-native-exit-v2/`, with
`taskell/final-series-declaration-native-exit-v1-v2.json` and
`taskell/scenario-revision-native-exit-v2.json`. Its E11M assertion matches the
stable rendered suffix `not parse file.` while preserving exit 1 and exact file
state. The previous v1 failures remain unchanged and receive no v2 credit.

The V36 macOS job failed on the signed empty
`opt/local/etc/xml/.turd_libxml2` package marker. The no-build cleanup path also
needs `--no-case-reports` so it can verify the absence of partial case evidence
before source removal. Local code now accepts only empty `.turd_*` regular files
below `opt/local/etc` without extracting them, rejects nonempty markers, closes
directory iterators on every exit path, and opts into checked no-case cleanup.
The focused suite passed 22 tests with four expected Windows symlink capability
skips. The v2 scenario and newest cleanup changes still require fresh native
Linux/macOS runs.

## Storage and immediate next work

The latest measured combined retained storage is 2,148,345,666 bytes versus the
2,147,483,648-byte cap (862,018 bytes over). No campaign storage compliance is
claimed. Continue with: complete Python/YAML/diff checks; record v36 and the v2
scenario revision; commit/push to the authorized branch; let standard hosted
Taskell exact and fault workflows finish; audit macOS toolchain setup, checked
no-case cleanup, and every Linux v2 case before considering Taskell admission.
Then continue the remaining selected projects, original-ten rc.6 qualification,
migrations, controls, delivered CI, fresh-checkout testing, storage compaction,
and final all-attempt reconciliation. Do not claim 30 until every required gate
passes.
