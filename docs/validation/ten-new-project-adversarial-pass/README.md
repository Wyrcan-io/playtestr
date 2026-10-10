# Ten new projects: adversarial validation

Invoked 10 October 2026. **In progress; no projects accepted yet.**

This executes the [full prompt](../../plans/ten-new-project-adversarial-validation-prompt.md). The earlier campaign remains separate and unchanged. Full-product launch campaign credit remains **0/100**.

Before acquiring applications, primary GitHub metadata and pinned READMEs were screened. [Candidate registry](candidates.json) and append-only [screening attempts](screening-attempts.jsonl) retain unavailable identities, exclusions and reserves. Pins are immutable; platform assignments remain provisional until actual execution.

Required gates: ten new projects; five useful normal plus five different edge scenarios each; ten final fresh repetitions on every qualified host; two real target mutations per project; persisted-state corruption controls; forty distinct product controls; ten native Linux plus at least five Windows and five macOS qualifications; documented user-flow assessments; final frozen source and cleanup.

## Execution and resource policy

One application repository is active at a time. A native CI matrix may run that same application on isolated hosts. Public target builds use synthetic state and bounded task-owned paths, with explicit dependency installation. No upstream mutations, releases, outreach or paid infrastructure.

Build/setup deadlines: twenty minutes. Scenario deadline: 120 seconds; step deadline: at most thirty seconds. Intentional hangs: one to five second product budget, thirty second independent harness ceiling. Independent state probes: ten seconds and four MiB. Task state: at most 64 MiB. Target disk: at most four GiB. Raw evidence: at most 128 MiB/project. Limits are independently enforced; output is never captured without a bound.

Operator UX assessment includes prior knowledge and warm-cache confounders; it is not a beginner user study. Source-candidate commands require the documented source build, rather than older published archives.

## Initial harness review

Previous `user_journeys.py` uses an unbounded `subprocess.run(..., stdout=PIPE)` capture for ordinary commands. Its final repeated public `test` executions confirm terminal/cleanup results, while saved-state checks occur through separate recorder executions. Those results remain accurate to their published scope, but do not satisfy this pass's stronger same-execution state and append-only requirements. The new campaign must bound command capture, register attempts before launch, and bind state checks to actual execution identities. Old helpers have hardcoded campaign paths and must not overwrite the prior corpus.

The historical Windows wizard failure remains unexplained. New green repetitions alone cannot establish a causal repair.

## Verified development checkpoint

Native run [38045564217](https://github.com/Wyrcan-io/playtestr/actions/runs/38045564217) at 3b27ffa72d97712e90bc5eec9515a9d5e802b8db passed all five jobs. Cookiecutter ran 100 ordinary tests plus 100 separately counted state probes on each of Linux and Windows, both actual source regressions, saved-state corruption and restoration, and confirmed hosted deletion. All 56 mapped product controls passed on Linux, macOS and Windows. [Retained native manifest](native/38045564217/manifest.json) includes exact binaries, actual events, cleanup and mutation reports. This is development evidence, not final frozen qualification.

The separate standard smoke run 38045564219 failed the Windows wizard recovery sequence. The [investigation](wizard-investigation/manifest.json) preserves the hosted failure and a local reproducer. Project acceptance remains pending this common-flow investigation, final freeze and local deletion. Native Enter encoding was tried and rejected after a full 500-run series still failed; no repair is claimed from the earlier passing reduced probe. A resize acknowledgment candidate is under validation.
