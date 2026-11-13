# Runner readiness: next twenty projects

Invoked 22 October 2026 under the [execution prompt](../../plans/runner-readiness-next-twenty-project-execution-prompt.md).
Status: **in progress; 17/30 cumulative admissions, with 1/20 new projects admitted on exact rc.7**. JOE is the first rc.7 admission: 20 scenarios, two Linux/macOS cells, 480 ordinary executions, three real source faults, 18 calibration phases, public authoring, oracle calibration and twelve rejected model corruptions. The previous exact-rc.6 checkpoint was 16/30 (six current-candidate new-project admissions). No rc.5/rc.6 project evidence transfers to rc.7; the original ten and the other nine next-twenty projects remain unqualified on rc.7. The cumulative 30/100 engineering gate remains open. See [checkpoint v143](checkpoint-continuation-v143.md).

Pick's exact-rc.8 public authoring route passed and was independently audited on Linux and macOS in run `43347165865`. Its separate technical route passed and was independently audited in run `43350106198`: suite selection, manual v3 edit with exact input-state check, JSON/HTML reports, v2 execution, v2-to-v3 migration, and prefix-preserving suffix rerecord. Source restoration and process cleanup were verified on both hosts. Pick's reconstructed model now rejects 17 semantic corruptions; the receipt is `pick/model-controls-v1.json`. All prior failed attempts and provider digests remain in [the route attempt ledger](pick/public-route-attempts-v1.json). Pick remains unadmitted pending independent project-package review and campaign reconciliation; its workflow preview is not counted as delivered CI. See [checkpoint v152](checkpoint-continuation-v152.md), the [public-route audit](pick/public-route-audit-run43347165865-v1.json), and [technical-route audit](pick/technical-route-audit-run43350106198-v1.json).

Fzy is the next selected target. Its pinned source and MIT license are reviewed; its first native workflow run acquired and built source and passed 32 upstream tests on Linux and macOS, but the exact-source cleanup gate caught leftover compiler-generated `.d`/`.dSYM` outputs before any Playtestr scenarios ran. Cleanup and storage steps also failed for missing pre-scenario mode/provenance setup. The provider packet and all failure causes are preserved in [the fzy attempt receipt](fzy/development-attempt-run43354015363-v1.json); corrected bounded cleanup, provenance and workflow gates are recorded in [checkpoint v153](checkpoint-continuation-v153.md). Fzy has zero scenario or admission credit until a corrected native run is independently audited.

The next fzy run `43354855944` stopped before native build because the build helper omitted its `DOC` import. Explicit no-case cleanup, exact source removal and storage validation passed on both hosts; no scenario ran. The import fix now has a focused module-import/provenance test. The attempt is retained in [its receipt](fzy/development-attempt-run43354855944-v1.json), with progress in [checkpoint v154](checkpoint-continuation-v154.md).

Run `43355127321` then built fzy and passed its 32 upstream tests on Linux and macOS; N01–N05 passed once per host. N06 timed out because it expected a match while typing the invalid query `bluz`, before reaching its Backspace action. N07–N20 did not run. Target cleanup, exact source removal and storage checks passed. The run and failure are preserved in [its receipt](fzy/development-attempt-run43355127321-v1.json). N06 now starts from a valid `blue` query, with a focused order/output regression. See [checkpoint v155](checkpoint-continuation-v155.md).

Run `43355826474` passed N01–N07 once on both hosts, including corrected N06. N08 failed because `--show-matches` is noninteractive and emits to stdout rather than the PTY screen; N09–N20 did not run. Both jobs passed cleanup and storage. The artifacts and outcome are retained in [the attempt receipt](fzy/development-attempt-run43355826474-v1.json). N08 now asserts the exact harness-captured output bytes and exit code, with a focused regression. See [checkpoint v156](checkpoint-continuation-v156.md).

The corrected native development run `43356291927` passed all 20 fzy cases once on Linux amd64 and macOS arm64 (40 outcomes). Each host also built the exact source pin, passed all 32 upstream tests, restored and removed owned source, and passed storage bounds. Provider artifact metadata and exact runner/target hashes are recorded in [the run receipt](fzy/development-run43356291927-v1.json). An independent bounded ZIP/report/identity/event/source/cleanup audit reconstructed all 40 outcomes and verified both provider digests; see [the audit](fzy/development-artifact-audit-v2.json) and [frozen contract](fzy/scenario-declaration-v1.json). See [checkpoint v158](checkpoint-continuation-v158.md).

The first 12-repeat qualification dispatch, `43358141466`, stopped prelaunch because `qualification` is not a declared campaign evidence phase. Both target builds and upstream suites passed, but no Playtestr case launched. Its report-required cleanup also failed without case reports; storage recorded the active source/runtime under the ephemeral hosted job. This is preserved with zero scenario/cleanup credit in [the attempt receipt](fzy/final-archive-attempt-run43358141466-v1.json). The workflow now uses the declared `final-archive` phase and labels its artifacts accordingly. See [checkpoint v159](checkpoint-continuation-v159.md).

The corrected fzy run `43358562580` passed 20 scenarios ×12 on Linux and macOS (480 total). Both builds passed the 32-test upstream suite; exact source restoration/removal, process cleanup and bounded storage passed with empty active/failed inventories. Provider artifact identities and frozen candidate/target hashes are retained in [the run receipt](fzy/final-archive-run43358562580-v1.json). Independent readback verified all 480 reports/events and both exact provider digests in [the final artifact audit](fzy/final-archive-artifact-audit-v1.json). Fzy remains unadmitted until its source faults, public authoring, maintenance, model controls and ledger review close. See [checkpoint v161](checkpoint-continuation-v161.md).

Five failed native fault attempts and their provider digests remain preserved in [the attempt receipt](fzy/fault-calibration-attempt-run43360846815-v1.json), all with zero credit. Corrected run `43363053728` passed nine baseline/fault/restored phases per host. F01–F03 were each detected at the exact declared public failure step on Linux and macOS; all 576 upstream test executions, cleanup, source removal and storage checks passed. Independent packet readback verified all 18 reports, builds/logs, events, identities, mutations, candidate installs, provider digests and process/source cleanup in [the fault audit](fzy/fault-calibration-artifact-audit-v1.json). See [the run receipt](fzy/fault-calibration-run43363053728-v1.json), [fault declaration](fzy/fault-declaration-v1.json) and [checkpoint v167](checkpoint-continuation-v167.md). Fzy still requires public authoring, maintenance, model controls and formal admission review.

Fzy's public route passed on Linux and macOS in run `43364417379`. It used the documented recorder to capture selected stdout bytes, seeded a wrong-file-bytes diagnosis, updated selected state after a controlled fixture reorder, relocated the reviewed spec into a Unicode/space path, and previewed (but did not dispatch) a hosted workflow. An independent audit reconstructed both provider packets and verified all eight attempts per host, exact artifacts, cleanup, event chains and identities; see the [run receipt](fzy/public-route-run43364417379-v1.json) and [artifact audit](fzy/public-route-artifact-audit-v1.json). Focused auditor tests pass. Saved-state coverage and admission credit remain zero. See [the route declaration](fzy/public-route-declaration-v1.json), [route harness](../../../scripts/acceptance/next20_fzy_public_route.py) and [checkpoint v169](checkpoint-continuation-v169.md).

Fzy's first technical-route workflow run `43365829863` passed exact two-spec selection, the manual v3 edit with exact input-file state, and JSON/HTML report checks on both hosts, then failed before v2 launch because the harness placed the v2 spec outside its fixture workspace. Exact provider packets, source restoration, target removal and zero-live-process checks are retained in [the failed-attempt receipt](fzy/technical-route-attempt-run43365829863-v1.json); it receives zero technical and admission credit. The workspace placement is corrected and covered by a focused test. The next native run remains required before technical-route credit. See [checkpoint v171](checkpoint-continuation-v171.md).

Skim V34 and its exact-rc.6 Linux and Windows repeat V35, including three-fault
calibrations, are independently audited in [readback v15](skim-artifact-retrieval-readback-v15.json):
240/240 ordinary outcomes, 240 independently reconstructed contracts and all
nine fault phases per host passed, with exact archive/target hashes and checked
cleanup. First-use, useful seeded diagnosis (expected diagnostic failure), the originally failing stale
maintenance assertion and its paired query/result update, Unicode relocation,
and read-only delivered-workflow preview are all retained. Both actual cell
models also rejected twelve semantic corruptions each in
[model controls v3](skim-model-controls-v3.json). Skim's formal
[admission](skim/admission.json) is complete and included in the exact-candidate
ledger. Directional-key behavior and raw NUL framing remain explicit
limitations. The prior retained-storage overage is now resolved by the indexed
exact-duplicate packet, leaving 511,102 bytes of measured retained headroom while
Taskell remains active. See [checkpoint v57](checkpoint-continuation-v57.md) and
[storage checkpoint v42](storage-checkpoint-v42.json).

Taskell has zero rc.6 credit. V2 run `42533986467` passed all twelve native
Linux batches (252 ordinary executions) with checked cleanup. macOS stopped
before target build because its signed ICU package includes the safe,
unmaterialized `opt/local/sbin/gennorm2` utility. The separate V2 source-fault
run `42533986457` passed on Linux and stopped at the same macOS package member;
that job completed checked no-case cleanup. The bounded extractor now allows
signed `opt/local/sbin` package contents without materializing them, with a
regression for the exact utility path. V1's wrapped diagnostic failure and both
new macOS preparation failures remain preserved; no failed attempt is replaced
or credited. See [checkpoint v57](checkpoint-continuation-v57.md).

Skim V34 exact-candidate run `42533986434` and Git Town V30 run `42533986432`
both exposed stale frozen helper hashes after the shared final-series helper
was extended for Taskell's v2 contract directory. Skim refused both hosts before
target execution. Git Town built its pinned target and installed the exact
candidate, then refused case launch on both hosts. Their failed artifacts and
zero-launch dispositions remain recorded. New V35/V31 declarations rebind the
current helper bytes and preserve the exact candidate/contracts; they add no
scenario breadth. New hosted native runs remain necessary before either
project's current-candidate evidence can be closed.
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
