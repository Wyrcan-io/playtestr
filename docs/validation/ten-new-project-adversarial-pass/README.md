# Ten new projects: adversarial validation

Invoked 10 October 2026. **In progress; no projects accepted yet.**

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
yet satisfied. Helix is now the sole active application. Four development
projects are complete; final frozen-source credit remains zero.
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
Final single-source campaign qualification and the remaining six development
journeys are pending; completed full-product launch credit remains zero.

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
