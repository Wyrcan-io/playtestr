# Runner readiness: next twenty projects

Invoked 22 October 2026 under the [execution prompt](../../plans/runner-readiness-next-twenty-project-execution-prompt.md).
Status: **in progress; four of twenty new projects qualify on exact rc.6 (14/30 cumulative)**. Eight distinct new applications have an admission on some candidate; four are rc.5 history only. The original ten passed an exact-rc.5 carry-forward audit, but none is yet requalified on rc.6. Current rc.6 new-project totals are 80 scenarios, 8 native cells, 1,920 ordinary executions, 72 calibrations and 12 real target faults. The cumulative 30/100 engineering gate remains open.

Skim V34 and its exact-rc.6 Linux and Windows repeat V35, including three-fault
calibrations, are independently audited in [readback v15](skim-artifact-retrieval-readback-v15.json):
240/240 ordinary outcomes, 240 independently reconstructed contracts and all
nine fault phases per host passed, with exact archive/target hashes and checked
cleanup. First-use, useful seeded diagnosis (expected diagnostic failure), the originally failing stale
maintenance assertion and its paired query/result update, Unicode relocation,
and read-only delivered-workflow preview are all retained. Both actual cell
models also rejected twelve semantic corruptions each in
[model controls v3](skim-model-controls-v3.json). Skim has not yet received
admission credit: its formal project admission and cumulative audit remain open;
directional-key behavior and raw NUL framing remain explicit limitations. See
[checkpoint v55](checkpoint-continuation-v55.md).

Taskell has zero rc.6 credit. Exact run `42528435710` built and passed the
upstream test suite on Linux, but E11M failed in 11/12 batches and passed only
in the separately declared larger-viewport batch; this remains an unresolved
target/harness boundary. macOS stopped before target build because the signed
MacPorts archive contains harmless `opt/local/etc` directory metadata, then
its cleanup step also failed on the absent build receipt. Local bounded fixes
now accept safe in-prefix directory metadata and handle cleanup when no build
receipt exists. Focused Windows tests, compile, YAML and diff checks pass; a
fresh hosted Linux/macOS series is required to validate those fixes. See
[checkpoint v55](checkpoint-continuation-v55.md).
jrnl qualified with 20 scenarios, two native cells, 480 ordinary executions and
18 calibrations; its [admission](jrnl/admission.json) binds the audited package.
Commitizen passed its [complete admission audit](commitizen-python/admission.json):20 scenarios, two native cells,480 ordinary,18 mandatory calibrations and2 separate terminal-only probes. Its twelve delivered-CI observations qualify source-built and exact-archive triplets separately.
cz-cli passed its [complete admission audit](cz-cli/admission.json): 20 scenarios,
two actual native cells, 480 ordinary checks, 18 mandatory calibrations and two
separate probes. Its 63 local reports, original failures, compiled JavaScript and
dependency payloads, maintenance and checked cleanup are independently audited.
yo passed its [complete admission audit](yo/admission.json):20 scenarios,
two independently audited native cells,480 ordinary executions,18 required
calibrations and two separate probes. All60 local reports and original rejected
series remain preserved. Linux and Windows have separately recorded source/run
identities; the unsupported two-second Windows startup attempt supplies no credit.

The starting repository revision is `46d01dfb3671fd18b73f15261069daa994e9afb8`
on `work/p0-p2-implementation`. These four admissions and the original-ten
carry-forward use production `129b7a4`, private candidate rc.5. Current source
repairs a [native Windows status defect](findings/native-windows-exit-status.md)
found in project five, cargo-generate. A distinct replacement candidate and
fresh qualification of the original ten and these four are required. The distinct
[rc.6 archive freeze](replacement-candidate-freeze-native-exit-v1.json) and
[105 public-control reexecutions](replacement-public-controls-readback.json) are
complete. Cargo's [rc.6 admission](cargo-generate/admission.json) verifies both
native Windows and Linux cells: 480 ordinary executions, 18 fresh calibrations,
three real source faults and 24 rejected evidence corruptions. Two rejected Linux
windows remain retained. Actual syscall diagnosis motivated additive native input
checkpoints; every original action and oracle remains. Required compiled sources,
all eight native executable variants, reports and first failures passed complete
byte readback and current storage caps. PDM's [uncredited discovery package](pdm/README.md)
completed480 final ordinary executions and18 fresh calibrations on rc.6 across
Linux/Windows, independent byte/model audits and checked cleanup. Three original
development failure screens were lost by the former harness, so its
[qualification disposition](pdm/qualification-disposition.json) grants zero
admission credit. [Hatch replaces its slot](substitution-pdm-hatch-v1.json) from the
original metadata-only reserves; the20 selected/8 reserve and native/diversity
allocations remain intact. [Hatch](hatch/admission.json) now qualifies on exact rc.6 with480 ordinary executions,18 fresh calibrations,two native cells and32 rejected evidence corruptions. Original public-authoring and development failures remain retained. Its initial20-control usability target remains failed; zero human observations.
The original ten and four
earlier projects still need rc.6 qualification; current cumulative 30/100 is open.
The imported closing admission's 32 subject files and three
retained native archives passed checksum verification. One initial import-helper
schema mistake is retained as a failed engineering command, followed by a
successful corrected invocation. It is not a product failure or project outcome.

- [Requirements and historical risks](requirements.md)
- [Resource and execution declarations](declarations.md)
- [Resume checkpoint](checkpoint.md)
- [Project ledger](projects.json), [actual native compatibility matrix](compatibility-matrix.json), [screening decisions](screening-decisions.json)
  and [provisional allocation](selection-declaration.json)
- [Attempt format and accounting](attempt-schema.md)

Raw evidence is local-only under
`artifacts/runner-readiness-next-twenty-project-pass/`. Immutable events distinguish
started, identified, launched and finished commands; identities and consoles are
retained separately. Historical data under the first campaign is read-only.
Screening uses current primary upstream metadata and pinned READMEs. Metadata
screening supplies no compatibility, source-hook approval or admission credit.

Required final new-project evidence: 400 scenarios (8 normal + 12 edge each),
40 native cells (20 Linux + at least 10 Windows and 10 macOS), 9,600 ordinary
executions, 60 real source/configuration faults and at least 360 separate
baseline/mutated/restored calibrations. Historical rc.5 qualified new counts are80 scenarios, eight cells,1920 ordinary and72 mandatory
calibration executions, plus6 separately counted terminal-only probes. Target setup, authoring, controls, rejected
series, repeats, retries and old migrations remain separate counters.

Human participants: zero; beginner usability unmeasured. Paid admissions: zero.
No release, outreach, issues, discussions, PR mutations or paid infrastructure
are authorized. Existing scoped commits/pushes and standard hosted workflows
remain authorized. The bounded helper workflow has passed actual native runs. All105 shared public archive controls passed actual three-host reexecution39976090337 and independent audit; retained initial compiler-prerequisite failures remain. These are public-control reexecutions, not105 new whole controls.

Skim has a [reviewed Windows development package](skim/README.md). Hosted run `42506300345` passed the earlier exact rc.6 Linux and Windows series. V31 run `42514930671` passed 240 ordinary cases and nine fault phases per host; [readback v9](skim/artifact-retrieval-readback-v9.json) matches its provider digests, batch hashes, case receipts, reports and fault/restoration aggregates. V31's public route was refused before launch because the journal lacked `public-authoring`. V32 added that phase and passed the exact ordinary/fault matrix; [readback v10](skim/artifact-retrieval-readback-v10.json) verifies both packets. V32 first-use and diagnosis passed, then maintenance collided with immutable `selection.json` before target launch. V33 used a separate maintenance spec, passed 240 cases and nine fault phases per host, then both update routes timed out at the unchanged `expect cedar` assertion after switching the query to `amber`. [Readback v11](skim/artifact-retrieval-readback-v11.json) verifies both V33 packets and cleanup; V33 remains unadmitted. V34 updates the matching result expectation and binds focused tests for preservation and missing/ambiguous anchors. Earlier zero-launch freezes V29/V30 had stale hashes; those attempts remain preserved. See [checkpoint v51](checkpoint-continuation-v51.md).


Git Town v17 run `41988031958` preserved another failed final-series attempt. Native Windows completed all 240 ordinary cases and reported nine source-fault phases; process proof, exact restoration and checked cleanup passed. The uploaded packet omitted the referenced fault case reports, build receipts and mutated executables, so those phases cannot receive independent audit credit. Linux passed 220 ordinary cases; its batch-11 N01 contract correctly contained the declared 5,000 ms startup boundary but timed out at 5,040 ms with exit 130. Process/workspace cleanup and exact source/runtime removal passed. All v17 outcomes remain preserved with zero cell, calibration or admission credit in [attempt record](git-town/final-series-attempts-v17.json).

The ten preceding Linux N01 first-screen assertions each took 5,050?5,067 ms, which supports a 6,000 ms Linux startup edge boundary for v18; ordinary 20 s step and 60 s run budgets stay fixed. V20 passes the selected declaration through the shared batch helper and copies the bounded fault reports, builds, binaries, events, and matrix-start receipt into retained evidence before checked target removal. Immutable v18 and v19 declarations were superseded before any hosted run or target execution because their retained-evidence bindings were incomplete. At that prelaunch checkpoint, candidate and fault credit remained zero pending a fresh native run and full packet audits.

Peco has a complete [rc.6 admission](peco/admission.json): 20 canonical scenarios (8 normal, 12 edge), two native cells, 480 ordinary executions, 18 calibration executions, three real source faults, reviewed maintenance/relocation, and checked removal. Its exact per-host readbacks and model controls are retained in the project package.

Git Town v20 run `41994487910` passed and was independently audited on Linux and Windows using the exact frozen rc.6 archives. All 12 batches per host passed (240 each), with nine fault phases per host, exact source/build restoration, retained fault reports/builds/binaries/events, bounded cleanup, no remaining target processes, and checked removal. The Linux batch-11 N01 edge uses 6,000 ms; Windows uses 2,000 ms; standard 20-second step and 60-second run budgets are unchanged. [Attempt record](git-town/final-series-attempts-v20.json) and [audit receipt](git-town/final-series-audit-v20.json) grant two cells, 20 scenarios, 480 ordinary executions, 18 calibrations and three distinct faults to rc.6. Project admission remains open pending campaign model-tamper controls and cross-project reconciliation; raw ZIPs remain local-only under `artifacts/runner-readiness-next-twenty-project-pass/retained/`.
