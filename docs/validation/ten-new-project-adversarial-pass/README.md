# Ten new projects: adversarial validation

Invoked 10 October 2026. **Final scoped terminal/state qualification passed.** Usability measurement limits and unresolved historical risks remain explicit.

Frozen source `e8682f866622442c421005c7f477cd45fcc66fc5` / [native run 38802794545](https://github.com/Wyrcan-io/playtestr/actions/runs/38802794545): 10 projects, 130 distinct scenarios, 21 native project/host pairs, 2,740 ordinary final repetitions and 2,740 separately executed state probes. All qualified owned application trees were removed. Full-product launch credit remains **0/100**.

Read the [final report](final-report.md), [strict audit](final-audit.json), [usability assessment](usability-assessment.md), [limitations](limitations.md), and [attempt accounting](all-attempt-accounting.json).

## Historical development chronology

The following entries preserve discovery-time status, failures and later corrections. Their pending statements describe earlier stages; the final audit above governs current scoped qualification.

Current development progress: Cookiecutter and Copier completed their native
Linux/Windows journeys and owned teardown. Copier's successful source/run is
`6df8c37cd7ffb2a6e8021cf9a0b4fa16c3b06583` / `38117318191`, with 120 ordinary
and 120 separate state executions per host. lf completed its development pass at
`cb34cc3f8bc7d90eabca2b5cb6db233b571939ef` / native run `38311988432`: all five
jobs passed, including 120 ordinary plus 120 separate state executions per
Linux/Windows host, actual mutations, restoration and verified owned teardown.
Superfile completed Linux/macOS development qualification at
`4c90d39ba32489cae2db89565690c14abe3d7165` / `38319592021`, with 120 ordinary
and 120 separate state executions per host, actual faults/restoration and
confirmed hosted and local teardown. All three native core jobs and standard
smoke passed. Windows superfile remains unqualified because a real repetition
failed and its pinned input dependency has a confirmed data race. The explicit
host adjustment adds Windows to Glow's planned matrix; that future gate is not
yet satisfied. Glow's actual pristine Windows race diagnostic subsequently
failed, so that provisional fifth Windows gate now belongs to Yazi. Helix
completed development qualification with full Windows run `38324763718` and
corrected Linux run `38469407174`; all twelve cases, 120 ordinary and 120
separate state repetitions, actual faults/restoration and qualified-run owned
deletion are evidenced per host. Its redundant Windows retry was mistakenly
cancelled after misleading live API metadata; the actual archive corrects that
interpretation, and the interrupted retry receives no qualification credit.
Glow completed development qualification at `ad7f00a` / native run
`38485822527`: Linux/macOS each passed twelve scenarios, 120 ordinary and
120 separate state repetitions, actual faults/restoration, and verified owned
deletion. All three native core/race jobs and standard CI passed. Its Windows
upstream race remains an explicit unqualified path. Broot completed thirteen-case Linux/macOS development qualification at `b50d7d8` / `38518046090`, with 130 ordinary and 130 separate state repetitions per host, all source faults/restoration and confirmed hosted/local teardown. Ten development projects are complete. Yazi qualified all fourteen scenarios on native Linux/macOS/Windows at `0f85370f115571165a8c72954e462c74b343fbfe` / `38634382707`: 140 ordinary and 140 separate state executions per host, all three real faults and exact restoration, and verified hosted/local owned removal. Its corrected scroll checkpoints preserve the original snapshot bytes. All applicable 86 product-control definitions, native race checks and the strengthened 26-test harness passed at `0d41e26` / `38637442983`. Ranger completed sixteen-case Linux/macOS development qualification at 18bb8618742874b9d4065feed402396a2a914ab2 / native run 38715026817: 160 actual ordinary repetitions and 160 separate final-group state probes per host, three exact-source fault/restoration controls, and verified hosted/local removal. Both failed native attempts and bounded diagnostics remain retained, including a diagnosed comparison-label error with zero comparison credit. Prepared UX, maintenance and rerecord routes passed. All 88 mapped controls have applicable native evidence (80 Linux, 80 macOS, 86 Windows); the strengthened 28-test private audit harness passed locally on Windows and WSL and awaits its next native CI source. nnn completed seventeen-case native Linux/macOS development qualification at `496d6d7308f468992b779da1caabbf92bc949323` / `38728097151`: 170 ordinary and 170 separate state repetitions per host, four compiled source faults with exact source/binary restoration, public UX/maintenance/rerecord and owned hosted/local removal. The same run contains a separate macOS core race-test failure under investigation; this is not counted as green core qualification. No external application checkout remains active. The corpus has 130 distinct scenarios and 21 planned project-host pairs. The first final frozen campaign at `be139a3` / `38793208349` stopped on a Copier Windows Git-update preparation timeout and remains rejected. A traced twenty-probe calibration established the Windows-only 20-second scenario budget without changing assertions or snapshots. Corrected full Copier qualification passed at `087ec53` / `38799866153` on both native hosts. The second all-ten single-source campaign is running at `e8682f866622442c421005c7f477cd45fcc66fc5` / `38802794545`; acceptance remains pending its strict actual-evidence audit.
The earlier lf investigation follows:
its twelve reviewed contracts passed 120 local Windows ordinary repetitions
plus 120 state executions and exploratory WSL ordinary/state checks. Hosted
source `5188978057d4a31aaf752a1dafb9fbb73488f1ea` passed all three product-control
jobs, but both lf application jobs failed at a Go compiler prerequisite mismatch.
The exact owned target-toolchain repair compiled lf successfully on both native
hosts at `425288a`, but their first scenario then accurately failed because Git
omitted the empty synthetic fixture directories. The declared directory
prerequisite passed a real local before/after regression with unchanged
contracts; the successful native run above subsequently verified that repair.
Final single-source campaign qualification remains pending; completed full-product launch credit remains zero.

The original `attempts.jsonl` is frozen after a diagnosed concurrent append
collision. Its original bytes, exact fragment and checksum remain retained in
[the quarantine record](core/ledger-quarantine.json). New serialized attempts
append to `attempts-v2.jsonl`; `adversarial_process.read_attempts()` reads both
epochs and rejects unknown damage. The affected imported identity was restored
only from the actual native archive, with an appended audit. This migration
does not turn incomplete, failed or corrupted attempts into qualification.

This executes the [full prompt](../../plans/ten-new-project-adversarial-validation-prompt.md). The earlier campaign remains separate and unchanged. Full-product launch campaign credit remains **0/100**.

Before acquiring applications, primary GitHub metadata and pinned READMEs were screened. [Candidate registry](candidates.json) and append-only [screening attempts](screening-attempts.jsonl) retain unavailable identities, exclusions and reserves. Pins are immutable; platform assignments remain provisional until actual execution.

Required gates: ten new projects; five useful normal plus five different edge scenarios each; ten final fresh repetitions on every qualified host; two real target mutations per project; persisted-state corruption controls; forty distinct product controls; ten native Linux plus at least five Windows and five macOS qualifications; documented user-flow assessments; final frozen source and cleanup.

## Execution and resource policy

One application repository is active at a time. A native CI matrix may run that same application on isolated hosts. Public target builds use synthetic state and bounded task-owned paths, with explicit dependency installation. No upstream mutations, releases, outreach or paid infrastructure.

Build/setup deadlines: twenty minutes. Scenario deadline: 120 seconds; step deadline: at most thirty seconds. Intentional hangs: one to five second product budget, thirty second independent harness ceiling. Independent probes bound each file read to four MiB. Command output and time have independent harness limits. The 64 MiB synthetic state, four GiB target storage and 128 MiB/project raw evidence budgets require explicit inventory checks; these are campaign budgets, not OS disk quotas or proven peak resource limits. No resource isolation is claimed.

Operator UX assessment includes prior knowledge and warm-cache confounders; it is not a beginner user study. Source-candidate commands require the documented source build, rather than older published archives.

## Initial harness review

Previous `user_journeys.py` uses an unbounded `subprocess.run(..., stdout=PIPE)` capture for ordinary commands. Its final repeated public `test` executions confirm terminal/cleanup results, while saved-state checks occur through separate recorder executions. Those results remain accurate to their published scope, but do not satisfy this pass's stronger same-execution state and append-only requirements. The new campaign must bound command capture, register attempts before launch, and bind state checks to actual execution identities. Old helpers have hardcoded campaign paths and must not overwrite the prior corpus.

The historical Windows wizard failure remains unexplained. New green repetitions alone cannot establish a causal repair.

## Verified development checkpoint

Native run [38045564217](https://github.com/Wyrcan-io/playtestr/actions/runs/38045564217) at 3b27ffa72d97712e90bc5eec9515a9d5e802b8db passed all five jobs. Cookiecutter ran 100 ordinary tests plus 100 separately counted state probes on each of Linux and Windows, both actual source regressions, saved-state corruption and restoration, and confirmed hosted deletion. All 56 mapped product controls passed on Linux, macOS and Windows. [Retained native manifest](native/38045564217/manifest.json) includes exact binaries, actual events, cleanup and mutation reports. This is development evidence, not final frozen qualification.

The separate standard smoke run 38045564219 failed the Windows wizard recovery sequence. The [investigation](wizard-investigation/manifest.json) preserves the hosted failure and a local reproducer. Native Enter encoding was tried and rejected after a full 500-run series still failed. The resize acknowledgment repair passed 500 local unchanged-action replays, then [native run 38049042627](https://github.com/Wyrcan-io/playtestr/actions/runs/38049042627) passed 100 reproductions on each OS, all core checks, and Cookiecutter's Linux/Windows journeys, mutations and teardown. The separate [standard smoke run 38049042653](https://github.com/Wyrcan-io/playtestr/actions/runs/38049042653) passed all three OS jobs. Both ran source `3154500e1e2a576378a951366cfa8e008f6c3441`. Precise internal ConPTY causality and the earliest historical failure remain unproven.

Before moving to the second application, a new real startup control found two detached Windows descendant generations surviving cleanup that the runner reported confirmed. [Before/after evidence](core/startup-repair.json) removes only the suspended-start barrier to reproduce the failure, then runs ten fresh repaired sessions. Targets now enter their Job Object before executing. Local full Go tests, vet and race checks passed; native requalification of this later repair remains pending. Cookiecutter's local Windows and WSL-owned source/runtime trees have been removed; hosted reacquisition uses the same pin for affected requalification. Final batch acceptance remains zero until the complete ten-project frozen-source run.

Native startup requalification [38051205443](https://github.com/Wyrcan-io/playtestr/actions/runs/38051205443) and standard smoke [38051205435](https://github.com/Wyrcan-io/playtestr/actions/runs/38051205435) both passed on source `d9c5c46130f67e6e99d76ae289afa6ce439f1154`. The [retained manifest](native/38051205443/manifest.json) includes native before/after startup logs, every ordinary report summary/hash, every successful state-oracle observation/hash and both actual application deletion receipts. Synthetic cleanup faults in harness calibration are intentional failures, separately counted; they are not failed app teardown receipts. Cookiecutter development journey is complete; final frozen batch credit remains zero. Copier is the next active application.

Copier now has twelve reviewed substantive contracts on Windows and exploratory Linux/WSL, a bounded corrected public authoring assessment, real source-fault/state-corruption controls and maintenance evidence. [Project report](copier/README.md). Hosted native repetitions and owned deletion remain pending. During expansion a continuously redrawing target exposed a second Windows resize defect: the target changed dimensions without emitting another CSI 8 confirmation. The candidate transport fence passed ten fresh twelve-resize controls and 500 unchanged historical wizard sequences locally. [Retained investigation](core/continuous-resize-investigation.json). This later repair requires actual native requalification; final accepted-project credit remains zero.
