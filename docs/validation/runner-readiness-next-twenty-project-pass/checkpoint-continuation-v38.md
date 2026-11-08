# Continuation checkpoint v38: 8 November 2026

Workspace `work/p0-p2-implementation` was clean of tracked edits at pushed commit `58efe0d3` before the current Taskell qualification changes. The campaign remains at 14/30 admissions (four new projects admitted in this batch). Taskell remains unadmitted.

## Taskell frozen input and exact candidate

The Darwin arm64 rc.6 archive is in the active Taskell input folder, 1,855,437 bytes, SHA-256 `132152710ade2c01cac7558f75212121f01af8ab02c5735dc9c7de1c33dbe625`, matching `replacement-candidate-freeze-native-exit-v1.json`. First-use run `42489015452` passed all 20 candidate invocations on Ubuntu 24.04 x86-64 and Intel macOS 15, plus the N01 smoke and public recorder route. It is exploratory evidence, not exact-candidate repetition credit.

The catalog is now represented in `taskell/host-contracts/`: eight normal workflows, twelve semantic edge families, and twenty-one invocation contracts because E11 malformed input and fresh recovery are separate. All 20 first-use case spec hashes match the two host results in `build-attempt-v32.json`; all 21 fixture-file bytes are separately hash-frozen. Final declaration `taskell/final-series-declaration-native-exit-v1.json` binds the exact private rc.6 archive, native runtime lock, scenarios, fixtures, twelve batches, 504 ordinary invocations across Ubuntu and macOS arm64, and 18 source-fault calibration invocations. No repetitions or fault phases have run.

The final workflow `.github/workflows/runner-readiness-next20-taskell-final.yml` is prepared to fetch the exact audited Linux and macOS candidate archives, build pinned Taskell with Stack 3.11.1, run its 250 upstream tests, and execute all twelve batches on standard free native runners. `next20_jrnl_final.py` now verifies candidate/runtime/spec/fixture freezes, launches PATH-based native apps from a hash-verified copied runtime, attempts every case in each batch without retries, and retains passed and failed outcomes. Python compile, YAML parse, scenario/fixture structure, exact Darwin archive digest, and `git diff --check` passed locally. Workflow is not yet pushed or executed.

Storage checkpoint v36 observed at 2026-11-08T15:09:48.156776+00:00; combined retained bytes 2147357057, headroom 126591. Receipt `artifacts/runner-readiness-next-twenty-project-pass/storage/83988174cc104fcea402ed442d29166f/observed.json` SHA-256 `cc8c865c11812548e0d89d242a654c86ddbfe786870128d3a39377cada5cb362`.

## Next actions

1. Re-review exact-case and workflow code, run the scoped source/mutation and workflow checks, then commit and push this prepared qualification on the already authorized branch.
2. Inspect actual workflow job identities and logs; retain both native packets and every partial/failed attempt. Do not count the run unless all 504 ordinary outcomes pass and all cleanup is confirmed.
3. Implement three real Taskell source faults with baseline/mutated/restored phases on both exact-candidate hosts; then run maintenance/relocation, candidate/public compatibility and audit gates.
4. Continue the other sixteen new applications; do not report 30/30 until all twenty complete packages and the original ten's candidate-current requirements are actually satisfied.

No PR, issue, discussion, release, or outreach mutation was performed. Commit/push authorization remains specific to this scoped branch and campaign.
