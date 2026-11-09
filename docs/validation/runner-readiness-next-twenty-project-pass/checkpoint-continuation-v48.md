# Continuation checkpoint v48: 9 November 2026

The campaign remains in progress at **5/20 new admissions (15/30 cumulative)**;
the original ten have **0/10 current-candidate requalifications**. Taskell is
project six and has not been admitted. Do not describe the thirty-project goal as
complete.

## Taskell exact attempt and repair

Exact candidate run `42542688174` used source `cb626596d512c1882cfbbfff1327b172423d4e43`.
Linux job `128923747474` passed upstream tests, built Taskell, and completed all
twelve exact-candidate batches (21 scenario invocations per batch). Its artifact
is `13643260552`, 11,751,678 bytes, provider SHA-256
`96bf84d4fea50c30dd4510bdadcbb0a5d9a04c19d72a9af14fa51edcddf4d8d0`. macOS
ARM64 job `128923747069` failed before Taskell runtime/case launch: experimental
GHC 9.2.8 does not compile packages in the frozen nightly-2021-07-14 dependency
set (including `iproute`/`random` unboxed Word mismatches and `semigroupoids`
references to `Option`). Its artifact is `13642617508`, 264,145,183 bytes,
provider SHA-256 `b710794f6cd54d04af3c30617c24d7faaa4abf6d12db26a24259b985eab586f9`.
The attempt is preserved in `taskell/final-series-attempts-v39.json`; it adds no
admission credit. The earlier GHC 9.2.8 fault attempt v6 is separately retained.

The local repair restores GHC 9.0.2 and resolves
`$(xcrun --show-sdk-path)/usr/include/ffi/ffitarget_arm64.h` on macOS. It sets
`C_INCLUDE_PATH` only on Stack/compiler build commands. The fault helper removes
that setting before launching Taskell. This addresses the missing GHC ARM64 FFI
header described in [GHC issue 20592](https://gitlab.haskell.org/ghc/ghc/-/issues/20592)
without changing Taskell's pin, resolver or lock. The focused helper suite passed
25 tests with three expected Windows symlink-capability skips; both workflow YAML
files parsed, Python files compiled, and `git diff --check` passed.

An exact-rc.6 public route helper and an `always()` exact-hash cleanup step have
been added to the Taskell final workflow.
It records from the public CLI without hand-writing the first-use spec, reviews,
freshly replays, saves and runs the candidate test; then it seeds a wrong screen
expectation, performs documented file-state maintenance, tests a spaced Unicode
relocation and reviews a generated free workflow preview. This route has not yet
run on a hosted native machine. Its output and scenario artifacts must be
independently audited before any Taskell admission claim.

Next: commit and push only the scoped Taskell fix, public-route helper/workflow,
the v39 exact attempt, and previously prepared honest Git Town/fault receipts.
Inspect both native workflows after push. The exact and fault workflows share a
concurrency group: preserve queued/cancelled statuses and execute the second only
after the first completes. The next exact run must pass both Linux amd64 and
macOS ARM64, include the public route, and be followed by independent artifact
readback; the new fault run must pass all three fault calibrations and recovery
on both. Continue sequentially with the nine remaining selected projects
(mg, joe, pick, fzy, percol, ne, sc-im, btop, htop), then original-ten current
candidate transfer, migrations, controls, delivery, storage, audit and closure.

Keep unrelated local material untouched. In particular preserve `.codex-go-cache/`,
`.codex-test-tmp/`, checkpoint v46, Skim model-control and draft receipts, existing
compaction-temp subdirectories, and the untracked Skim V14 drafts/readbacks.
Only explicitly reviewed campaign receipts and implementation files belong in
the next commit. Do not delete archives/caches through a blanket clean.
