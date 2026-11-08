# Continuation checkpoint v43: 8 November 2026

Branch `work/p0-p2-implementation` is at pushed commit `b12c41ca706b08d4ffdf5131e0669c1671331884`; the scoped repairs and immutable run records are staged for the already-authorized commit/push. Campaign progress remains four new admissions (14/30 cumulative), with Taskell active and unadmitted.

The most recent hosted Taskell final run 42496545392 passed Linux source verification, 250 upstream tests, and native build but failed all twelve batches before target launch because Stack `.stack-work` generated files exceeded the bounded source identity walk. macOS ARM GHC 9.0.2 failed before upstream tests/build because LLVM `opt` was unavailable. Fault run 42496545430 built Linux target but refused its first baseline on undeclared evidence phase; macOS again missed LLVM. Exact run and artifact identities are recorded in Taskell attempt v34 and fault attempt v1.

Git Town run 42496545476 built both hosts but refused before candidate cases on a stale v23 harness hash; checked cleanup passed. Skim run 42496545584 built both hosts but refused before candidate cases on stale v22 acquisition hash; no-case cleanup also conservatively refused before deletion. Those failures remain unchanged in v24/v12 run records. Current staged declarations are Git Town v26 and Skim v25: v24/v23 and v25/v24 were generated but superseded before dispatch.

Final staged fixes: generated Stack `.stack-work` is excluded from source identity but frozen source files/modes stay bound; macOS obtains signature-verified MacPorts LLVM 12 ARM64 and records tool/symlink hashes; Taskell calibration phase is declared; Windows timeout cleanup waits for asyncio reaping of the owned child after taskkill; the engineering wrapper supports an explicitly owned `--raw-root`, used by synthetic regression scratch. Git Town v26/Skim v25 bind the exact staged harness.

The final scoped test suite passed 57 tests with two WMI-dependent native cleanup tests skipped locally because this token lacks WMI permission; the hosted Windows workflow must execute them. An additional wrapper regression passed with evidence redirected to tmp; Skim plan check passed on v25. Python compilation, four workflow YAML parses and diff checks passed. Full result is `local-regression-results-v3.json`.

Storage v41 passed all declared caps but leaves only 9,402 bytes under the combined retained cap. Do not add retained raw evidence locally; native workflow artifacts remain on GitHub until audited. All local unit-test/harness data was preserved under campaign tmp and mapped by SHA/path indexes. Previous over-cap observation remains retained.

## Next actions

1. Commit and push the scoped staged changes to the authorized branch.
2. Inspect the resulting exact Taskell final and source-fault workflows, Git Town/Skim v26/v25 workflows, and the existing native hosted checks.
3. Retrieve and audit all actual artifacts. Taskell requires 504 ordinary native exact-candidate invocations and 18 calibration phases before any admission. Preserve every partial/failed attempt.
4. Continue the remaining new-project admissions and original-ten carry-forward; do not claim 30/30 until all gates close.

No PR, issue, discussion, release, deployment, or outreach mutation is made.
