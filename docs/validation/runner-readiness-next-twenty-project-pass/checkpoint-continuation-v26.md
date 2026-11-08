# Continuation checkpoint v26 — 8 November 2026

Branch `work/p0-p2-implementation`; latest pushed implementation/evidence
commit is `80a2e8a069c20b6fbd80ebdd898fe96049f955e0`. A new local change adds
the positive `INSERT` observation required by the runner before the candidate's
negative assertion. Four of twenty new projects are admitted (14/30 total);
the full campaign remains incomplete.

## Active Taskell sequence

Taskell remains pinned to
`smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`, with
151 primary source blobs verified. It is the only active target.

- `42456298245`: first-use route passed on Ubuntu and Intel macOS; see
  build-attempt v18/v19. No scenario-series, fault or admission credit.
- `42458747709`: task-creation candidate requested missing `board.md` instead
  of fixture `board-basic.md` on both hosts. Final screens, reports, cleanups
  and hashes are in build-attempt v20. Candidate setup error; no credit.
- `42460993289`: after correcting the board filename, both hosts passed the
  task-entry assertions, then timed out because `q` was entered in INSERT
  mode. Both reports confirm forced process-group cleanup and workspace
  cleanup; saved-state assertions did not run. Reports and final screens are
  in build-attempt v21. The Taskell source confirms Enter leaves a blank row
  in INSERT mode and Escape calls `finishTask` and returns to normal mode.
- `42462915946`: both hosts passed the existing-task smoke but rejected the
  create spec before launch. Exact diagnostic: `step 8 expect_not "INSERT"
  requires an earlier expect for the same text`. No target launch or cleanup
  attempt; no creation credit. Receipt and native report identities are in
  build-attempt v22.

The local spec now expects INSERT before Escape, asserts INSERT disappears,
then sends `q`, checks exit 0, and asserts exact board bytes. This runner-valid
sequence has not been tried on Linux or macOS yet. The duplicate candidate is
prepared but must not run unless creation passes every step, state, process
and workspace assertion. No Taskell scenario-series, native-cell,
fault-calibration or admission credit exists.

The 8-normal/12-edge catalog is still an unfrozen draft and the three source
mutations are only candidates. After actual interactions are verified, freeze
the exact catalog and execute all required native repetitions, real
baseline/mutant/restored phases, calibration, maintenance, relocation,
audits, final candidate and checked cleanup. Do not round partial evidence
into an admission.

## Storage and next action

Storage v19 had 151,279 bytes of combined-retained headroom before v20-v22
receipts and reports. Full hosted artifacts were reduced to text reports and
runner/host identities; all temporary native binaries were hashed and their
extraction directories removed. Measure again before adding a larger packet.
Historical storage observations remain losslessly packed and indexed.

Next: commit and push the positive INSERT observation, then monitor a fresh
Ubuntu/Intel macOS run. Verify actual Escape transition, normal quit, exact
saved bytes and cleanup before evaluating the following candidate.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Standard GitHub-hosted validation and commit/push are authorized.
