# Continuation checkpoint v50: 8 November 2026 20:26 UTC

The branch is pushed at `5196a214551651af315affa7ce5cff9feb5117cb`. Campaign
accounting remains **4/20 new rc.6 projects (14/30 cumulative)**; the original
ten have zero current-candidate requalification. Protected `.codex-go-cache/`
and `.codex-test-tmp/` remain untouched.

V32 Skim (`42517430006`) passed and was independently audited for all 240
ordinary cases and nine fault phases on Linux and Windows. Both public routes
passed first-use and seeded diagnosis, then stopped before maintenance target
execution at an immutable `selection.json` overwrite. Checked source, cache and
target cleanup passed. Readback v10 and attempt ledger v13 preserve the complete
failed-route evidence; V32 receives no admission credit.

V33 preserves the first-use export and writes the changed query to a distinct
`selection-maintenance.json`; relocation now runs that maintained spec. Its two
focused route tests pass. The full local hosted-preflight-equivalent suite ran
48 tests: 44 passed and four skipped because Windows cannot create a symlink,
Unix socket or FIFO. Python compilation and staged-hash checks passed for all 59
declared harness files; no mismatches. V33 commit `5196a214` is pushed.

Fresh exact V33 workflow `42520096920` is running on the standard Ubuntu 24.04
and Windows 2025 hosts. Both have passed acquisition and are fetching locked
dependencies/building the target. No V33 candidate target cases have launched
yet. Push-triggered helper workflow `42520096896` has Linux success; Windows and
macOS are still running. Continue monitoring these actual jobs, preserve any
preflight/first failure and all cleanup, then retrieve and independently audit
the two native packets before considering Skim credit.

Taskell remains unadmitted. Its Linux E11M failure in 11/12 batches and the
macOS signed LLVM dependency failures for `libxml2.16.dylib` and `libz.1.dylib`
are unresolved. Keep that exact evidence and investigate the native output and
signed dependency closure after the current two-host target jobs complete.

Next steps: finish V33 and its artifact readback; resolve Taskell; continue the
selected new apps; requalify the original ten; complete applicable migrations,
88+33 whole controls, archive/free-CI triplets, tamper controls, storage,
fresh-checkout and cleanup gates. Do not infer 30/30 from historical admissions
or V32's passing subseries. No PR/issue/discussion/release/outreach or paid
infrastructure action is authorized.
