# Continuation checkpoint v41: 8 November 2026

Branch `work/p0-p2-implementation` is at pushed commit `b12c41ca706b08d4ffdf5131e0669c1671331884`; the scoped repairs and immutable failure records are staged but not yet committed. Existing explicit commit/push and standard hosted workflow authorization remains active. Progress remains four new admissions (14/30 cumulative). Taskell is still active and unadmitted.

## Latest hosted evidence

Taskell exact candidate run 42496545392: Linux verified source, passed 250 upstream tests and built Taskell 1.11.4, but 12 batches were rejected before Taskell target launch because `.stack-work` compiler output exceeded the bounded source identity scan. macOS ARM acquired source and selected GHC 9.0.2, then stopped before tests/build because GHC required LLVM `opt`. Fault workflow 42496545430: Linux built the pristine target but refused at undeclared evidence phase before any fault case; macOS again stopped on missing LLVM. Immutable records are `taskell/build-attempt-v34.json` and `taskell/fault-attempt-v1.json`.

Git Town run 42496545476: both Linux and Windows built candidate and target, then stopped before any case because the v23 harness declaration had stale bytes for shared `next20_jrnl_final.py`; checked source/runtime cleanup passed. `git-town/final-series-attempts-v24.json` preserves the failures and v24 binds the staged corrected harness.

Skim run 42496545584: both Linux and Windows built source/runtime, then refused before candidate launch on a stale acquisition-helper hash in v22. Cleanup preflight also refused because no reports existed, despite a proved empty case-evidence root. `skim/candidate-native-attempts-v12.json` preserves both zero-launch failures; v23 binds current harness and uses the cleanup helper's explicit empty-case-evidence path.

## Local fixes and validation

- Exclude only generated Stack `.stack-work` from source identity; frozen target source remains hash- and mode-bound.
- For macOS ARM, keep the frozen Taskell resolver, lock, and source while selecting GHC 9.0.2; acquire the exact MacPorts LLVM 12 ARM64 package, verify its signify signature using the MacPorts base key, constrain extraction to the owned toolchain root, and record hashes for files and symlinks. Fault builds retain the override and dynamic-library path.
- Declare the `fault-calibration` evidence phase. Harden Windows timeout cleanup to wait for asyncio to reap the exact owned child after `taskkill`, with `proc.kill()` fallback under a bounded wait.
- Git Town v24 and Skim v23 declarations are regenerated from staged bytes.
- Targeted local suite: 55 passed, 2 Windows WMI observer tests skipped because this token receives access denied; hosted Windows check remains required. Python compilation passed. Full record: `local-regression-results-v1.json`.
- A local storage observation first found test scratch over the retained cap. Preserved its bytes and path/hash index while moving only local synthetic test/harness diagnostics to the existing temporary area, then remeasured under every cap. Storage v39 receipt leaves 121,724 retained bytes of headroom. See `storage-checkpoint-v39.json`; over-cap observation remains retained as audit history.

## Next actions

1. Commit and push these scoped repairs on the authorized branch; inspect the four relevant native hosted workflow runs.
2. Audit full Linux/macOS Taskell artifacts and require exact 21 contracts x 12 batches x 2 hosts plus 18 fault phases with cleanup before admission. Audit Git Town and Skim reruns separately; never infer success from build or preflight.
3. Continue the remaining projects and original-ten carry-forward under the exact frozen candidate; current progress is 14/30, not complete.
4. Recheck storage after each new evidence batch and preserve all failed attempts.

No PR, issue, discussion, release, deployment, or outreach mutation is authorized or claimed.
