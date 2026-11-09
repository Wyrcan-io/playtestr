# Continuation checkpoint v65: mg source acquired; native build pending

Date: 10 November 2026 (Asia/Calcutta). Current-candidate admissions remain **5/20 new projects** (15/30 cumulative). The original ten remain **0/10 requalified** on rc.6. Taskell remains a zero-credit rejection under its macOS build-time ceiling. No mg scenarios or source faults have been run.

## mg source and review

Selected canonical project `troglobit/mg`, exact commit `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`, Unlicense, C, Emacs-style terminal editor. The pinned archive is 483,574 compressed bytes and 1,349,286 expanded bytes across 126 files; archive SHA-256 is `bd8aff8ddbf55f7d37067a9f01e6bef887a2b0f2c0699aaa08a73d7dfd6069a8`. Every extracted source file matches the acquisition map. Primary-source license, build/install hooks, secure-mode boundary, supported platforms and candidate scenario/fault sites are recorded in `mg/preflight-review-v1.md`; 20 draft journeys and three tentative faults are in `mg/scenario-catalog-draft-v1.md`.

Two immutable acquisition attempts are preserved. Attempt 1 failed before source launch after three local socket-denied requests. Attempt 2 used the already authorized bounded network escalation and succeeded. No source build or target process has run. `projects.json` now records mg as acquired but unadmitted; admission/execution counters are unchanged.

## Current storage and build plan

The latest storage receipt is `artifacts/runner-readiness-next-twenty-project-pass/storage/18bad3a452e2453ebe47a2da31b83e3d/observed.json` (SHA-256 `0200d3a0c7d5630cdf370c51078539773d501aa8ba6c572eb4ac3f663eca0ec1`). It passes all declared caps with 2,110,985,431 combined retained bytes, 3,952,586,174 combined raw bytes, 34,982,176 combined curated bytes and one active mg target of 1,844,881 bytes. Combined retained headroom is 36,498,217 bytes. Forecast no more than 24 MiB for mg's complete package and remeasure at each retention milestone.

The new workflow `.github/workflows/runner-readiness-next20-mg-build.yml` builds the pinned source on standard `ubuntu-24.04` and `macos-15` runners. Its shared 20-minute acquisition/build deadline, command output limit, owned `HOME`/temporary/build/install paths, exact source hash checks and process-group cleanup are implemented in `scripts/acceptance/next20_mg_build.py`. The local focused suite reports 7 passed and 3 POSIX-only skips on Windows; native process-group tests are included in the Linux/macOS workflow. Workflow YAML and Python syntax parse locally.

This workflow has not yet been pushed or executed. Next: commit/push the scoped changes, inspect both real native build results, then pilot and revise the PTY contract before freezing mg cases. No mg admission is claimed at this checkpoint. Unrelated caches and Skim drafts remain untouched; no PR, issue, discussion, release, tag, outreach or paid infrastructure action occurred.
