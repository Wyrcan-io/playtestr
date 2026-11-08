# Continuation checkpoint v31: 8 November 2026

Branch `work/p0-p2-implementation` points to pushed commit `9e555e1e60e57ad300dd0f03cd4ea1080ebf3fe4`. Four of twenty new projects are admitted (14/30 cumulative). Taskell remains the only active target and is not admitted.

## Run 42474684731: N05-N08 on two native hosts

Both hosts passed the pinned 250-test upstream suite, target/runner builds, N01 existing-task smoke, and every candidate in the loop was attempted. Linux job `128713237444` and Intel Mac job `128713237674` ended red only because N06 and N08 same-run state-byte assertions rejected the authored expected bytes. N05 reorder passed 6/6 on both hosts with exact state; N07 search-and-complete passed 11/11 on both hosts with exact state. N06 move-right showed the task under Doing; N08 showed the new Review column and task. Both had exit 0, all interaction steps passed, and process/workspace cleanup was confirmed, but their executed byte contracts were incomplete. The empty-list serializer joins each list with an additional newline. Corrected local N06/N08 specs include the missing separator; they have not run yet. Preserve both failed spec versions, reports, and actual screens in `taskell/first-use-attempts/42474684731-{linux,macos}/`; report and artifact identities are bound in `build-attempt-v26.json`.

N01-N04 remain one-shot cross-host passes in v25. N05 and N07 have one-shot cross-host evidence only. N06/N08 are first-route oracle misses pending corrected reruns. Candidate set is still unfrozen; there is no 20-case repeated series, fault/calibration credit, or Taskell admission.

## Edge-case candidate work

E01-E12 are drafted from the pinned app/runner source. E11 has two invocations (diagnostic and clean-workspace recovery); the actual scenario count remains twelve edge IDs. E01-E10 and E11/E12 are unrun and may need correction. N05-N08 are likewise tracked as authored candidates, with N06/N08 corrected local byte oracles. Dynamic workflow enumerates all case specs, skips only the separate existing-task smoke, runs through failure, and reports aggregate failure at the end. The next commit also adds an early job-start marker so an external Haskell installer failure still yields an artifact.

## Storage and cleanup

Fresh storage passed at 2026-11-08T11:52:50.446721+00:00. Receipt: `artifacts/runner-readiness-next-twenty-project-pass/storage/87a2a978219e4996b19a540592cc40d0/observed.json` (SHA-256 `75935029c8795b3bd36b001a2d7a6aed21dbabf1669421b59643ab755aafada5`). New raw 1997728825; combined raw 3906437397; combined retained 2147345261; new curated 12091083; combined curated 23747327; active project 1002 bytes; no cap failures. Combined retained headroom: 138387 bytes. Downloaded Linux/Mac extraction directories were hash-verified and removed from unique owned `tmp` children. Preserve unrelated tmp, ignored caches, `.tools`, `.cache`, and historical campaigns.

## Next actions

1. Commit and push the corrected N06/N08 byte oracles, E01-E12 specs, start-marker workflow change, v26 run receipt, and fresh storage checkpoint; validate all candidates on both native hosts and preserve first failures.
2. Inspect all edge results, repair first-route misses, and freeze only after exact same-run bytes/screens, cleanup, and source anchors are settled for all 20 scenario IDs.
3. Run the required 20 x 2 x 12 series, three real fault baseline/mutant/restored phases, calibrations, maintenance/relocation, original-ten closure, CI/archive, audits, storage and final cleanup before any admission.

No new Taskell project admission is claimed. No PR, issue, discussion, release or outreach mutation was performed.
