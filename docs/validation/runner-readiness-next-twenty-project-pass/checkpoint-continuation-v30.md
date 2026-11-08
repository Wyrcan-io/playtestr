# Continuation checkpoint v30: 8 November 2026

Branch `work/p0-p2-implementation` currently points to pushed commit `8ddd97c50e32abaaa44ca5fd3410829492c380ec`. Four new projects are admitted (14/30 cumulative). Taskell remains the sole active, unadmitted project; do not substitute an admission for its required full gates.

## Native run 42471306905

The pushed candidate loop runs every authored top-level `taskell-*.json` case, except the existing-task smoke already run separately; it continues after a case failure and returns failure if any candidate fails. Linux job `128702451256` passed the pinned upstream 250-test suite, build, smoke, existing N02/N03 cases, N04 rename, and public recorder review/replay/export/ordinary route. Linux N04 report has all 22 steps passed, exact fixture-state match, exit 0, graceful process-group termination, and confirmed workspace cleanup. Its curated reports and host/runner packet are in `taskell/first-use-attempts/42471306905-linux/`. GitHub artifact 13614380125 is 11,207,425 bytes with SHA-256 `ab7fdb367246b061e0d71f9028efc40f7b88380369efa46a21900e988aad9f96`.

Initial Intel Mac job `128702451038` failed before target acquisition: GHCup's pinned Stack 3.11.1 download returned HTTP 504 twice, and the always-upload step also failed because no packet existed yet. Exact hosted logs remain available. Only the failed Mac job was retried. Latest retry job is `128705624609`; the retry passed the pinned suite, build, all four candidate cases, and recorder route. Mac artifact 13614303128 is 6,785,461 bytes with SHA-256 `182f1a549935c9751b9d732c95b9c77d36952303da1192bc8a2d56fdd20687db`. N04 is now one-shot cross-host evidence, recorded in `build-attempt-v25.json`; the initial setup failure remains preserved.

N05 reorder through N08 list creation/task candidates are drafted at `taskell/first-use-v1/`, grounded in pinned bindings and reducers with exact byte oracles. None have run yet. Candidate catalog is still unfrozen.

## Storage and workspace

Fresh storage script passed after both host report curation, N05-N08 drafting and checked temporary-download cleanup at 2026-11-08 11:09:44.448076 UTC. Receipt: `artifacts/runner-readiness-next-twenty-project-pass/storage/1565c826d0e74162b08d2f99fb13b770/observed.json`. It measured new raw 1,997,724,137; combined raw 3,906,432,709; combined retained 2,147,340,573; new curated 11,997,167; combined curated 23,653,411 bytes; one 1,002-byte active Taskell project; no failures. Combined retained headroom was 143,075 bytes. Both downloaded Linux and Mac artifact extractions were hash-verified against curated reports and binary identity records, then removed from their unique directories under campaign `tmp`; a fresh storage check passed afterward. No unrelated tmp entries, `.codex-go-cache/`, `.codex-test-tmp/`, `.tools`, `.cache`, or historical campaign files were touched.

## Next actions

1. Commit/push the N05-N08 candidate specs, source grounding, v25 run receipt,
   curated Linux/Mac reports, and fresh storage checkpoint; validate both native
   hosts and preserve any first misses.
2. Continue E01-E12 from source-backed interactions and exact byte oracles, then
   freeze the catalog only after every candidate and risk pair has been inspected.
3. Complete the full 20-case, 12-repeat two-host series, source baseline/mutant/
   restored phases for all three real faults, calibration, migrations,
   maintenance, relocation, original-ten closure, audits, CI/archive, storage,
   cleanup and final reports before any Taskell admission.
Current limits: zero Taskell series, fault, calibration or admission credit. No project 5 admitted and no 30-project gate complete. Commit/push and standard GitHub-hosted workflows are authorized; no PR, issue, discussion, release or outreach action was performed.
