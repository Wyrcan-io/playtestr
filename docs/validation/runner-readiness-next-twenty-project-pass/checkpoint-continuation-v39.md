# Continuation checkpoint v39: 8 November 2026

Branch `work/p0-p2-implementation` is on pushed base commit `58efe0d3`; the scoped Taskell qualification changes are staged locally and the user's campaign commit/push authorization remains active. Campaign progress is four new admissions (14/30 cumulative); Taskell has no admission credit.

## Current Taskell work

The exact Darwin arm64 v0.4.0-rc.6 archive was verified at 1,855,437 bytes, SHA-256 `132152710ade2c01cac7558f75212121f01af8ab02c5735dc9c7de1c33dbe625`. Exploratory run `42489015452` passed the upstream suite, N01 smoke, all 20 authored candidates and recorder first-use route on Linux amd64 and Intel macOS. That is one-shot source-build evidence only.

`taskell/host-contracts/` now freezes eight normal workflows, twelve edge families, and 21 invocation contracts (E11 malformed plus separate recovery), with 21 fixture files. Every first-use contract hash matches paired run 42489015452; fixture manifest and exact candidate/runtime/scenario digests are bound by the final declaration. The exact-candidate workflow is set up for free hosted Ubuntu 24.04 amd64 and macOS 15 arm64, twelve batches each, 504 ordinary invocations total. It builds/tests pinned Taskell, installs the frozen private rc.6 archive, and retains every outcome. Three genuine source-fault baseline/mutated/restored phases per host remain unimplemented/unrun. No final-series run has started.

The shared journal runner now verifies candidate freeze, canonical scenario bytes, runtime lock, fixture file membership/content and per-case specs. For native targets it prepends the hash-verified binary directory to PATH, preserves supported target launchers, records all attempted outcomes without retries, and stops launching if process/workspace cleanup is not confirmed. Local validation so far: source-built first-use spec hashes match both host receipts; all frozen state oracles resolve to fixture bytes; 21 scenario/fixture checks, Python compile, workflow YAML and embedded-Python compile, exact arm64 archive digest, and `git diff --check` have been checked. Hosted execution remains required.

Storage v37 observed at 2026-11-08T15:16:29.961345+00:00; combined retained `2147358267` bytes, headroom `125381` bytes. Receipt `artifacts/runner-readiness-next-twenty-project-pass/storage/f53db43a45d744a096b92f8c59c5bce5/observed.json` SHA-256 `a48687adf88ef7686f70f806e80b87cca65126da003b248cd233602ba296b7d9`.

## Next actions

1. Commit and push the staged scoped changes under the explicit authorization; verify the resulting workflow actually starts.
2. Inspect both native jobs and retrieve their full packets. Audit reports, state bytes, candidate/target identities, runtime copies and cleanup; do not count partial or exploratory results.
3. Implement and execute the three pinned Taskell source mutations with exact baseline/restored outcomes on both native hosts. Finish public recorder/maintenance/relocation, compatibility, audit and cleanup evidence.
4. Advance the other sixteen new applications. The 30-project gate also requires current qualification of the original ten on the claimed final archive.

No PR, issue, discussion, release, or outreach mutation was performed. Do not claim thirty admissions until every required project, fault, native cell, audit and carry-forward gate is evidenced.
