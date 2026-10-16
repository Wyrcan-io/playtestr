# Native E1/E2 readiness record — 27 September 2026

Evidence availability: bulk raw records are local-only; see [the archive policy](README.md).

**E0, E1 and E2 are accepted at their engineering boundaries: 3/6 readiness milestones complete.** Final native and matched real-task campaigns passed and their artifacts were inspected. This supersedes the Windows-only status in the [26 September record](e1-e2-local-readiness-2026-09-26.md) without replacing its failures. Operator self-review is not independent adoption. E3–E5 remain unstarted, and the candidate is unpublished and not final-byte qualified.

## Authorization and native evidence

The user authorized standard GitHub-hosted Linux/macOS jobs, testing-branch pushes, workflow execution, artifact retrieval, continued E1/E2 repairs and the final completed push. The [execution prompt](../archive/prelaunch-2026-10-06/plans/e1-e2-ci-execution-prompt.md) records the boundary. No paid infrastructure, release publication, outreach, PR/issue/discussion activity or E3–E5 execution occurred. GitUI and television remain frozen, unexecuted holdouts.

The unchanged v0.4.0-rc.1 binaries were acquired from published assets and checked against frozen archive/executable hashes. Linux amd64 runs on Ubuntu 24.04 and macOS arm64 on macOS 15, with Go 1.26.0, Node 24.7.0 and Python 3.12. Windows amd64 uses the frozen published binary and separately labeled Go 1.27.0 candidate checks. Source, target, helper, fixture and derived-definition hashes are retained in the artifact manifests and compact observations (`e1-e2-ci-observations-2026-09-27.json`, local evidence). None of these task samples substitute for the separate 3,000-attempt final-byte qualification.

## E1 acceptance

All six journeys have five fresh good executions, one executable-code defect and unchanged-spec recovery on Windows, Linux and macOS: 18 primary-host cells, 126 selected discovery observations. Native pilots are additional observations. The final native campaigns each contain 74 observations: six pilots, 42 primary controls, 13 variations, one real network race case and 12 maintenance controls. A per-host script writes `e1_complete:false` because it cannot decide aggregate checkpoint acceptance; this record reviews the required cross-host set.

| Journey | Exact independent outcome | Reviewed synthetic target defect |
| --- | --- | --- |
| RW1 Lazygit 0.65.0 | Only alpha staged with exact bytes; beta remains changed and unstaged; HEAD unchanged | StageFiles omits Git add |
| RW2 micro 2.0.14 | Saved bytes survive reopening; second unsaved edit is discarded; neighbor untouched | Save reports success with corrupted bytes |
| RW3 create-vite 9.2.1 | Correct invalid name, exact reviewed 11-file scaffold/tree and JSON fields; occupied directory preserved | Actual JavaScript code writes commonjs instead of module |
| RW4 fzf 0.74.4 | Exact post-exit selected-output snapshot `beta record.txt` and exit status | Go entrypoint returns a different record despite plausible selection UI |
| RW5 litecli 1.17.1 | Independent SQLite connection verifies rollback and exact committed rows | Successful-looking insert persists wrong value |
| RW6 Posting 2.10.0 | Independently read saved YAML and exact local HTTP method/path/body after editing URL path | Save persists stale URL despite successful UI feedback |

These are reviewed disposable source mutations, not historical upstream bugs. RW2/RW3/RW5/RW6 exercise plausible success with wrong persisted state. RW1's Linux negative can stop earlier at the missing staged-pane assertion; only its exact step/category/exit combination is admitted, with confirmed cleanup. Other state defects fail at their independent oracle; RW4 fails its final-output snapshot. No accepted negative is merely a missing dependency or wrong test expectation.

The selected Windows frozen-runner cohort combines RW1/RW2/RW4 from `discovery-final-local`, RW3 from `discovery-rw3-exact-final`, RW5 from `windows-portable-helpers`, and RW6 from `windows-final-bounded-posting`. Later helper changes invalidate the superseded affected rows; they are not double counted. Separately, current-source Windows candidate discovery passes 42/42. Final Windows maintenance passes 12/12 and the real Posting failure case passes 12/12 steps with a race-built helper. Native controls and race checks are visible in [baseline run 36301105572](https://github.com/Wyrcan-io/playtestr/actions/runs/36301105572) and [candidate run 36301783921](https://github.com/Wyrcan-io/playtestr/actions/runs/36301783921).

The scheduled variations cover distracting neighbors, resize/help, save/reopen/discard, spaced/multilingual filenames, reviewed existing configuration, occupied-directory refusal, similar/combining candidates under a fixed locale, transactional partial progress, delayed response and local service failure. Arbitrary retained user homes are outside these disposable reviewed-config probes.

| Synthetic maintenance exercise | Original outcome | Legitimate expectation edits | Helpers / baseline churn | Maintained defect and recovery |
| --- | --- | --- | --- | --- |
| micro filename/status label | Timeout at old saved-name expectation | One existing spec, one expectation value | Existing oracle reused; zero new maintenance-only helper files; zero snapshots changed | Both accepted |
| create-vite Select → Choose | Timeout at old prompt | One existing spec, two expectation values | Existing oracle and explicit runtime routing reused; zero snapshots changed | Both accepted |
| Posting Request saved → Request stored | Timeout at old notification | One existing spec, one expectation value | Existing oracle and explicit variant routing reused; zero snapshots changed | Both accepted |

The defect variants retain the same meaningful state checks. These are synthetic UI changes, not newer upstream-version compatibility. Automated operation durations, commands and attempts are recorded. Active human authoring/diagnosis minutes were not measured and remain unknown; line counts are not a substitute for human effort or user preference.

## First failures and diagnostic revisions

| Original observation | Disposition |
| --- | --- |
| Local Lazygit selected root/staged all; micro reopened before meaningful readiness; create-vite only checked a subset of scaffold | Repaired fixture/navigation/readiness and exact state oracles; fresh affected controls retained separately |
| Posting query-string edit looked changed but server received old query | Still unisolated; RW6 explicitly tests URL-path editing. No query-edit support claim |
| Native micro wide Snow input rendered `雪l alpha marker` | Retained unsupported wide-cell probe on both native hosts. The separately labeled basic Unicode café/λ variation passes; it does not repair or erase the wide failure |
| Posting local failure marker was transient beneath redraw | Read bounded HTTP headers, record exact unavailable path, close before response, assert actual Couldn't send request UI and independent request log; race integration added |
| First real comparison staged generated config files; alternatives launched from different cwd | Shared workspace glue repaired: HOME/TMP siblings outside Git fixture and explicit repository root. Original comparison controls invalid, including negatives incorrectly credited by its old classifier |
| macOS driver demanded Linux's before-fix EOF failure | macOS baseline EOF already passes. Retain first experiment failure, require Linux-specific reproduction and passing macOS baseline/candidate controls |
| Windows diagnostic pipe changed Unicode to question marks | Operator encoding error; retained, then separate UTF-8/escaped-input control passed |
| Historical/local inventory and timing instrumentation errors | Retained exclusions in the dated local record; no replacement of original observations |

## E2 measurements and cost

The baseline profile's 30 ordinary and 30 instrumented C1 runs had median wall times 314.697 and 314.713 ms. Median nested final drain was 250.815 ms; cleanup was 0.141 ms. Instrumentation overhead was small in that selected cell. Nested spans are not added or subtracted to invent isolated overhead.

The pinned Unix PTY library retains a parent slave handle after the target inherits it. On Linux this prevents natural EOF and forces the full final-drain deadline. The small internal adapter releases the parent duplicate after successful start and keeps the master until ordinary cleanup; release errors remain cleanup errors. Windows retains ConPTY. No assertion, snapshot settlement, timeout, quiet period, final-drain allowance, output bound or process-tree policy changes. [Candidate protocol and first failure](e2-unix-eof-candidate-2026-09-27.md) preserve the before-fix proof and host distinction.

The final-source pinned short-task campaign has 30 observations per task/tool, 360 total, all passing, with good/defect/recovery and adversarial lifecycle controls retained separately:

| Task | Playtestr candidate median ms | Atago 0.23.0 | Termlens 0.11.2 | tui-test 0.1.0-beta.5 |
| --- | ---: | ---: | ---: | ---: |
| C1 selection | 45 | 50 | 51 | 139 |
| C2 invalid config correction | 46 | 52 | 52 | 147 |
| C3 resize/modal | 54 | 107 | 56 | 153 |

This uses the original pinned idiomatic routes, with Rust 1.85.0. It is Linux-only, task-specific evidence. These whole commands include their adapter costs. Fresh baseline reproduction preserved the original direction before the repair. Different jobs are not a matched before/after comparison.

The final Linux candidate campaign completed 180/180 accepted counterbalanced before/after observations, 30 per task/mode, on the same Go 1.26.0 host. Its original-source real PTY test failed specifically at natural EOF before cleanup and passed on the candidate. The earlier campaign's overall red status is the retained macOS driver expectation error, not a hidden Linux failure.

| Matched task | Before median ms (min–max), n=30 | After median ms (min–max), n=30 |
| --- | ---: | ---: |
| C1 | 314.920 (314.633–315.135) | 64.277 (64.162–64.388) |
| C2 | 314.969 (314.812–316.026) | 64.280 (16.069–65.352) |
| C3 | 314.891 (314.719–315.542) | 64.241 (64.087–65.145) |

This is approximately an 80% decrease in that whole-command harness, including Python wait/polling and report/artifact costs. It is a different measurement route from the shell campaign above. The ≥30% reduction target and short-task distance target are met in these selected Linux cells. Startup/readiness/evidence-generation spans are not separately isolated; first-step duration is not called startup latency.

Two real-task comparisons use the same Go fixture/state-oracle/workspace-cleanup wrapper for all tools, their idiomatic keyboard/readiness adapters, and exact wrong-persistence controls. All 18 good/defect/recovery controls and 180 counterbalanced measurement observations pass. This table measures the unchanged published runner, not the optimized candidate:

| Real task | Published Playtestr median ms (range), n=30 | Atago median ms (range), n=30 | Termlens median ms (range), n=30 |
| --- | ---: | ---: | ---: |
| RW1 stage exact neighbor | 1366.896 (1366.598–1367.454) | 164.433 (114.215–165.785) | 214.603 (214.379–216.423) |
| RW3 correct/scaffold | 364.674 (364.472–414.811) | 114.333 (114.184–166.010) | 164.459 (164.318–164.587) |

The baseline loses runtime on both real tasks; selected detection ties. The common Go wrapper is 172 lines, shared experiment driver 99 lines, and Termlens task adapter 63 lines at the final comparison source. Dynamically generated Playtestr/Atago specs, all logs, compiler/package prerequisites and helper code are retained. Those are real costs, not proof of a human authoring-effort win. Alternative cleanup here proves completion of the shared fixture oracle and deletion of its workspace, not a universal descendant-cleanup guarantee.

The additional [matched real-task campaign](https://github.com/Wyrcan-io/playtestr/actions/runs/36303388321) passes all 24 good/defect/recovery controls and all 240 measurements, 30 per task/tool. Original-source and candidate runners use the same Go 1.26.0 host, targets, dimensions, fixture/state/cleanup helper and reviewed keyboard actions; before/after order is balanced 15/15 per journey.

| Matched real task | Before median ms (range), n=30 | Candidate median ms (range), n=30 | Atago median ms (range), n=30 | Termlens median ms (range), n=30 |
| --- | ---: | ---: | ---: | ---: |
| RW1 | 1366.890 (1366.639–1367.741) | 1116.533 (1116.139–1117.414) | 164.403 (114.310–165.706) | 214.553 (214.413–215.306) |
| RW3 | 364.678 (364.548–414.775) | 114.266 (114.140–164.382) | 114.319 (114.148–164.332) | 164.418 (164.343–164.605) |

RW1 improves about 18.3% but remains a substantial loss against both alternatives. Its first positive `alpha.txt` assertion takes a median 1060 ms in both before and after reports (ranges 1050–1070 and 1050–1061 ms). This localizes the remaining gap to that readiness wait without claiming isolated target startup or a proven cause. RW3 improves about 68.7%; candidate/Atago medians are effectively tied at this resolution, while the candidate is faster than the selected Termlens route. Correctness ties on these selected controls. Two-primary-task differentiation and independent total-effort superiority remain unmet/unknown later scorecard boundaries.

Termless 0.9.1's Windows real-PTY menu interaction passes, but natural-exit cleanup remains unqualified: bounded no-kill Node stays alive until diagnostic exit 2; kill-after-exit reproduces AttachConsole failed. Node 24.7.0/node-pty 1.1.0 pins and reduced tests are retained. No competitor patch or stderr suppression admits it to timing rankings; Linux/macOS feasibility remains unknown.

Published-runner resource baseline uses the reviewed five-task serial composition, 30 plain and 30 sampled size-1 observations, then one plain and one sampled size-10/50 suite. All 64 outcomes pass with confirmed runner/workspace cleanup and zero observed survivors. Plain medians/observations are 2.353 s, 24.907 s and 125.405 s. Sampled values are 2.362 s, 25.182 s and 126.370 s; sampled CPU lower bounds 110 ms, 7.850 s and 39.970 s; peak aggregate RSS lower bounds 47.56 MB, 107.81 MB and 108.54 MB. Evidence sizes are roughly 3 KB, 31 KB and 153 KB. The size-50 ten equal-time peak intervals span 105.37–108.54 MB with no monotonic growth in that observation.

Sampling can miss short-lived/reparented processes; CPU/RSS are lower bounds and zero sampled survivors is not complete process-tree proof. The sampler's requested sleep is 20 ms plus inventory work. Larger suites are single observations per mode, not reliability estimates. No p95 is claimed from n=30 or by pooling different tasks/tools.

The final same-job paired resource campaign accepts 128/128 command observations: 30 plain and 30 sampled size-1 runs per runner, and one plain/sampled size-10/50 suite per runner. Before/after order alternates; the larger suite order reverses. It contains 360 accepted spec executions with independent task-state oracles, confirmed cleanup and zero observed sampled survivors.

| Serial size | Before plain ms | Candidate plain ms | Before sampled ms | Candidate sampled ms | Before/candidate sampled CPU ms | Before/candidate peak RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1, medians n=30/mode | 2353.247 | 2111.285 | 2364.498 | 2115.857 | 110 / 100 | 48.70 / 48.48 |
| 10, single/mode | 25156.889 | 23013.227 | 25397.384 | 22806.608 | 8120 / 8030 | 111.07 / 109.04 |
| 50, single/mode | 126760.716 | 113455.685 | 127299.847 | 114583.491 | 41140 / 40770 | 109.70 / 109.51 |

Candidate plain wall time is about 10.3%, 8.5% and 10.5% lower in these observations; there is no observed real-suite regression. Size-1 sampling increases median wall time about 0.48% before and 0.22% after. These are instrumentation checks for this composition, not universal overhead guarantees. Candidate evidence sizes stay about 3 KB, 31 KB and 153 KB, with no evidence truncation. The candidate's size-50 ten interval RSS maxima span 106.60–109.51 MB and do not show monotonic growth; original-source maxima span 106.91–109.70 MB. CPU/RSS sampling limits and small larger-suite denominators still apply; no universal memory or leak-free claim is inferred.

Fresh release acquisition/extraction on the observed Linux job took 544.026/49.397 ms (verification 2.324 ms); macOS 269.162/26.099 ms (verification 1.990 ms). These are fresh local downloads, not controlled cold Internet/CDN conditions. Atago acquisition/extraction took 195/206 ms, tui-test 228/127 ms. Parent install timings overlap those children and must not be summed. Source build/dependency and pinned target preparation operations are separate ledgers; Actions tool/dependency caches are not assumed cold.

Seven experimental campaigns consumed about 150.75 standard runner-minutes and retained 67.96 MiB compressed artifacts, excluding ordinary root CI. Every campaign is below the six-runner-hour/1-GiB ceiling. [Run identities, first failures, exact durations and artifact digests](e1-e2-ci-runs-2026-09-27.json) and Windows selected outcomes/maintenance/race evidence (`e1-e2-windows-final-observations-2026-09-27.json`, local evidence) are durable records; full downloaded artifacts remain under the ignored `artifacts/readiness-ci-*` directories. Remote artifacts have 14-day retention. The compact ledger preserves original rows and file digests, reduces sampled RSS traces to ten equal-time maxima, and does not pool repeated or invalidated revisions into a reliability estimate.

Go tests/vet pass on all three native hosts. Runner lifecycle race checks pass on Linux/macOS, the full repository race suite passes on Windows with the project-local compiler, and real Posting network race cases pass on all three. Windows manual menu examples pass 2/2 specs, 12/12 steps. Hang, unexpected exit, last output, redraw/resize, cancellation, output flood and descendant cleanup regression controls pass. The current-source native candidate has 74/74 Linux, 74/74 macOS and 42/42 Windows discovery observations; those expected-negative outcomes are admitted controls, not rewritten product passes.

## Remaining decision

E0/E1/E2 are accepted; E3–E5 are unstarted. This accepts measured investigation and the engineering candidate, not universal competitive leadership or a new release. The exact later E3 task is to reproduce the retained MICRO-08 wide Snow/stale-cell failure on native Linux/macOS with fixed geometry and UTF-8 locale, establish independent expected cells/reference capture, and compare the frozen fzf wide/combining/resize companion. Select one demonstrated cell-width family for repair or an explicit support boundary; do not infer a backend defect merely because emulators disagree.

Human accessibility, independent authoring effort/adoption, arbitrary retained homes, Posting query-edit semantics, wide/grapheme fidelity, residual RW1 readiness cost, holdouts and final-byte release qualification remain distinct later boundaries. No universal superiority, reliability percentage, isolation or new published-version claim follows.
