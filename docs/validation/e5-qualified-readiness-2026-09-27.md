# E5 private qualification and readiness decision — 27 September 2026

Evidence availability: bulk raw records are local-only; see [the archive policy](README.md).

**E5 accepted at the scoped technical boundary.** The complete three-host
ledger records 3,000/3,000 passing first attempts, zero first-attempt failures
and zero managed-cleanup failures; every row has the expected frozen runner hash.

Recommendation: **technically ready for a scoped
trial; unpublished**. E3 is an accepted investigated deferral, E4 is accepted
operator evidence, and E5 qualifies exact private bytes. Publication, deployment,
tags, outreach and independent adoption are separate decisions. Differentiation
remains unmet. Implementing engineer self-review is the reviewer boundary;
maintainer owns the later release/claim decision.

Frozen shipping source is `ae97c62022966cde9699b26169b4dc6ef0a12439`, embedded
version `v0.4.0-rc.2`, Go 1.26.0, `-trimpath` and stripped version linker flags.
The version was checked unused before freezing. Documentation and validation
follow-ups do not rebuild the runner. [Native build 36329978517](https://github.com/Wyrcan-io/playtestr/actions/runs/36329978517)
built once per host; [manifest](../../release/e5-candidate-manifest.json) records
executable/archive hashes, exact four-member layouts, native images, extraction
into paths with spaces, version equality and source-installer identity. Original
build-time “qualification pending” fields are historical; derived qualification
fields describe subsequent checks. No tag or release was created.

| Host | Exact executable SHA-256 | Exact archive SHA-256 |
| --- | --- | --- |
| Linux amd64 | `543f56353cfa77e6270e8ae0ce4ab018fe58fc0a990a9b4a942e33a2f9ed0c03` | `e442710e1cc851d134cde7ccc9441be8503c65e210d35318f0106ed5ab54ce55` |
| macOS arm64 | `a6b806e38bf6818fcf2405f8fff2ccb83be3565e18ca444714c9886b2593c527` | `7dab72ab263b34f3e1a4958b6c6f6f8aa374633320531e9ebeaf11317006a9f4` |
| Windows amd64 | `b09f8daea6211ae24ca15aeb4b7f15f5daac277c920a02cb28feb6b99eb3aa8b` | `27284f5e994dc7e7122bdca83a52819aec55fa420e9dbd78cdc2bdde70c7eff4` |

The machine packet (`e5-observations-2026-09-27.json`, local evidence) preserves dated attempt
ledgers, pinned target/runtime and spec identities, expected/actual categories,
cleanup, resource observations, CI job metadata and artifact digests. The
[private kit](../trials/e5-private-kit.md) gives reproduction and exact later
promotion commands. Raw synthetic evidence and original archives are packaged
privately with per-member hashes; GitHub artifacts have 14-day retention.

| Gate | Actual denominator and boundary |
| --- | --- |
| Final selected qualification | [36330814511](https://github.com/Wyrcan-io/playtestr/actions/runs/36330814511): ten selected workflows × 100 first attempts × three native hosts; one 3,000-attempt campaign, also satisfying the existing 11-C requirement, never counted twice |
| Existing corpus | 120 first good workflows + 15 attributed controls + 15 unchanged recoveries = 150 accepted expectations; negatives retain nonzero product exits. Controls remain 12 executable-code defects and three changed-input/fixture controls |
| Support claim | 119 supported workflow cells plus one diagnostic MICRO-08 cell; its first execution passed but reliable wide-cell rendering is excluded. TIG/taskwarrior targets use admitted WSL lanes, not native Windows application claims or native Linux runner evidence |
| Affected native real journeys | [36333011585](https://github.com/Wyrcan-io/playtestr/actions/runs/36333011585): 48/48 accepted on each native Linux/macOS host, six pilots plus five good/defect/recovery executions per primary journey; exact frozen runner hashes |
| Holdouts | Two previously designed GitUI/television definitions; five fresh good journeys each, meaningful code defects and unchanged recoveries, 20 final-byte executions on native Windows |
| Authoring replay | Four clean-directory walkthroughs replayed with frozen Windows bytes, 52/52 accepted; eight reviewed synthetic maintenance changes, not upstream upgrades |
| Native source gates | [36329981123](https://github.com/Wyrcan-io/playtestr/actions/runs/36329981123): full tests/vet/race, required non-skipped lifecycle/install events and manual examples on all three native hosts |
| Exact-byte lifecycle/resources | [36330943126](https://github.com/Wyrcan-io/playtestr/actions/runs/36330943126): hang, run deadline, flood and descendants; 1/10/50 synthetic-fixture suites on each host, all expected categories/cleanup accepted |
| Release stories | [36330145384](https://github.com/Wyrcan-io/playtestr/actions/runs/36330145384): ten declared command outcomes per native host, 30 accepted, using exact frozen executables |
| Compatibility/presentation | 15/15 side-by-side v1/v2/old-reader expectations; reviewed baseline hashes unchanged; new reader renders old v1 evidence offline; keyboard/browser checks passed, human screen-reader use unknown |

Full native JSON events observed 136 Linux, 136 macOS and 135 Windows top-level
behavior tests plus 71 subcases per host; helper-process scaffolding is excluded.
Unix skips only the Windows-path syntax test; Windows skips the portable
unreadable-directory test because ACL mutation is outside that unit test.
Mandatory focused events are present and passed. The 300 risk-map rows resolve
to 40 test-function anchors plus BT-08, not 300 distinct executed tests. All 40
anchors appeared in Windows pass events, and frozen BT-08 passed. Local Go
1.27 Windows tests/vet and the actual project-local GCC race script are
supplementary to the frozen Go 1.26 native gates.

The initial holdout build used an invalid nested-module command and continued
with an older oracle. Those 20 preliminary executions remain visible. The
correctly built exact-index/worktree oracle was replayed, then the final frozen
binary completed its separately identified 20 executions. These developmental
repetitions are not more independent holdouts. Historical corpus presence and
operator knowledge limit independence; no replacement-shopping or assertion
tuning after a target failure occurred.

First failures remain retained: E3 Unix wide-cell failures; E4 volatile wizard
baseline, encoding/source-copy mistakes, installer stalled-body regression;
macOS lost final output and intermediate reduction/harness deadlocks;
the first native-byte workflow's same-step environment-variable setup error;
the old browser connection refusal; and the original instrumented Windows
50-suite MICRO-08 stale cell. The original instrumented suite passed 49/50;
its uninstrumented original passed 50/50. Sampling is not proved causal.
A separately admitted composition substitutes the already frozen basic café/λ
route, with no change to the original failed spec or wide-rendering contract.
Its instrumented and plain 1/10/50 cells all pass. This closes supported-suite
measurement, not wide-cell support.

Supported Windows tree-sampled suite wall times were 2.960/23.422/117.912 seconds,
with 2,989/31,240/155,381 artifact bytes. The 50-cell sampled peaks were about
17.72 MB runner and 146.94 MB tree. Plain times were 2.742/23.448/115.180 seconds.
These are n=1 per size/mode. Exact-byte synthetic native suites took Linux
0.118/0.224/0.656, macOS 0.578/2.785/13.630 and Windows 0.313/2.906/14.266 seconds.
CPU/RSS ledgers preserve sampling resolution and missed short-lived-process/PID
reuse limits. Zero observed survivors does not prove every possible process
was sampled. macOS retains the existing bounded final drain to protect output;
Linux retains immediate EOF. Product timeouts/output bounds were not relaxed.

Raw `target_startup_ms` means first-step wait and `runner_overhead_ms` means
outside-reported-run residual; neither isolates causal startup or overhead.
Qualification per-workflow descriptive medians/ranges/p95 and accumulated CPU
and bytes are in the machine packet; repeated samples do not establish universal
reliability or speed. Native preflight [36330142857](https://github.com/Wyrcan-io/playtestr/actions/runs/36330142857)
accepted 30 executions and forecast about 1.74 runner-hours plus setup, with
6.47 MB scaled evidence. The macOS job cap was raised to 90 minutes because
setup plus the forecast exceeded 60; product deadlines remain unchanged.
Actual job seconds and compressed artifact sizes, including cancelled/failed
attempts and separately attributed ordinary CI, are retained in the packet.
Focused human effort is unknown against the E3 2–3, E4 3–4 and E5 2–3 day
estimates; queues and machine wall time are not human days or billed dollars.
No paid runners or budget changes were used.

Task scorecard retains the strongest measured alternatives and full oracle/glue
scope: historical RW1 Playtestr about 1,116 ms loses to Atago 164 and Termlens
214; RW3 about 114 ties Atago 114 and beats Termlens 164. Selected correctness
ties, total human effort is unknown. These are the original exact E2 binaries
and toolchains, not a new final-RC competitor benchmark. Two meaningful
real-task advantages were not demonstrated. Independent comprehension,
first-use time, preference, demand, retention and buying evidence remain A1/A2.

Wide/combining cursor layout, query-dependent terminal flows, universal Unicode,
framework/host compatibility, isolation, universal superiority and broad human
accessibility are excluded. The runner accepts explicitly trusted targets and
is not a sandbox. Only synthetic fixtures/tool identities were retained; no
ambient environment dump or secrets. Process-group/Job Object cleanup applies
to the managed boundary, with documented escape limitations. Maintainer owns
the later interactive screen-reader walkthrough and specific outreach decision.

Existing public v0.4.0-rc.1 checks remain old-byte evidence. New candidate public
downloads and immutable external action checks are pending separately authorized
publication. The [prepared kit](../trials/e5-private-kit.md),
[migration](../migration-v0.4.0-rc.2.md), release-note draft and dispatch-only
verification workflow make that later decision concrete. No new convenience
family was justified. Preserve the fixed E0–E5 boundary and move independent
trial/adoption questions to separately authorized A1 rather than extending
engineering indefinitely.

Actual retained native job accounting before final handoff: ordinary ci 5060 seconds (1.406 hours), final qualification 6264 seconds (1.74 hours), preflight 795 seconds (0.221 hours), engineering validation 9175 seconds (2.549 hours). All engineering validation including failed/cancelled jobs is below the six-hour exploratory allowance; final qualification and ordinary CI are separately attributed. Final post-push CI metadata is additionally retained in the private packet.
