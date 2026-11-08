# Continuation checkpoint v42: 8 November 2026

Branch `work/p0-p2-implementation` is at pushed commit `b12c41ca706b08d4ffdf5131e0669c1671331884`; the current scoped repairs and zero-credit hosted-attempt records are staged for the authorized commit. Progress is four new admissions (14/30 cumulative); Taskell remains active/unadmitted. Explicit commit/push and standard hosted workflow authorization remains applicable.

## Preserved hosted failures and fixes ready for dispatch

- Taskell final run 42496545392: Linux passed source verification, 250 upstream tests, and native target build but all twelve candidate CLI batches stopped in the source identity preflight because generated Stack `.stack-work` exceeded the bounded source scanner. No Taskell scenarios launched. macOS ARM selected GHC 9.0.2 and stopped before tests/build because `opt` was missing. Fault run 42496545430: Linux built target then refused the undeclared `fault-calibration` evidence phase before any calibration; macOS again missed LLVM. See `taskell/build-attempt-v34.json` and `taskell/fault-attempt-v1.json`.
- Git Town run 42496545476: both native hosts built candidate and target, but stale v23 shared-harness hash stopped the series before cases; checked source/runtime cleanup succeeded. V24 was prepared but not dispatched. V25 binds the final staged helper/test bytes.
- Skim run 42496545584: Linux and Windows built but stale v22 acquisition hash stopped before cases; the no-report cleanup guard also refused before deletion. V23 was prepared but not dispatched. V24 binds final staged bytes and enables checked cleanup only after empty case-evidence verification.

## Repairs and checks

- Stack `.stack-work` is excluded as generated build cache only; actual frozen source files/modes remain bound. Apple Silicon uses the frozen Taskell resolver/lock/source with GHC 9.0.2 and obtains MacPorts LLVM 12 from its signed ARM64 package. The helper verifies the pinned base key and package signature, safely bounds extraction, verifies LLVM tools and records hashes for regular files and symlink targets. Source-fault builds retain Stack and loader environment.
- `fault-calibration` is a declared evidence phase. Windows timeout shutdown now waits for asyncio to reap the owned direct child after `taskkill`, with bounded exact-child force/reap fallback; its regression passes. Synthetic LLVM archive tests exercise bounded extraction, traversal refusal, inventory and changed-byte rejection.
- Local regression suite passed 57 tests; two Windows WMI process-observer tests skipped because local token access is denied. Workflow YAML and Python compile checks passed. See `local-regression-results-v2.json`; standard hosted Windows remains required for those exact tests.
- Local unit-test outputs are not project qualification evidence. All generated test/harness bytes are preserved under campaign `tmp` with per-file SHA-256/path indexes v1/v2; test writers now target the temporary area to avoid retained-storage growth. Storage v40 is within caps with 119,277 bytes retained headroom. The immediately prior over-cap observation remains preserved.

## Next actions

1. Commit/push scoped staged files and monitor Taskell final/fault, Git Town final, Skim final and their existing native workflow checks.
2. Retrieve the full actual artifacts, audit them independently, and only count exact target launches/reports/cleanup supported by evidence.
3. Taskell admission requires all 21 contracts x 12 batches x 2 hosts and 18 fault phases; partial build or zero-launch failures never qualify. Then continue remaining new projects and original-ten exact-candidate carry-forward.
4. Keep storage below caps and preserve every new failure. Do not claim 30/30 until all acceptance gates close.

No PR, issue, discussion, release, deployment or outreach mutation has been made.
