# Continuation checkpoint v25 — 8 November 2026

Current pushed qualification source is `5ec01145e2c9b1ddcbf0ac203bd8d843397c5a0b`;
the branch also contains checkpoint-only commit `b61638766b77b3cea4ae204b23caad24d21313bd`.
The next local change adds an Escape/normal-mode boundary to Taskell's create
candidate. Campaign status remains four of twenty new admissions (14/30
cumulative); the campaign is incomplete.

## Taskell status

Pinned source: `smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`
(151 primary blobs); BSD-3-Clause. Taskell remains the sole active project.
Do not begin another target before its full admission and cleanup audit.

Run `42456298245` previously passed the pinned 250 tests, one authored
first-use smoke and the public recorder/replay/export/ordinary-test route on
Ubuntu 24.04 and Intel macOS. This is first-use evidence only, not a native
scenario cell, series, fault calibration or admission. Its receipts are v18
and v19.

Run `42458747709` passed the 250-test suite and existing-task smoke on both
hosts, but failed the creation candidate at step 1 because its spec requested
`board.md` while the fixture supplies `board-basic.md`. The final screen on
each host was Taskell's prompt to create the missing board. Failure reports,
screens, host identities, artifact digests and hashes are in
`taskell/build-attempt-v20.json` and the `first-use-attempts/42458747709-*`
directories. This was a candidate setup error and earns no creation credit.

Run `42460993289` used the corrected filename. Both hosts passed the 250
upstream tests, existing-task smoke and create-case steps 1-7. Both then timed
out waiting for exit at step 8; the final screen shows the typed `q` in a new
task row and the UI still in INSERT mode. Forced process-group termination
was confirmed and workspaces were removed, but exit and saved-state
assertions did not pass. The duplicate candidate was not reached. Exact
artifacts, identities, reports and screens are retained in v21. This failure
revealed an interaction sequence issue, not a target defect.

Pinned Taskell source `Taskell.Events.Actions.Insert` confirms Enter stores a
created task and enters another insert row. Escape calls `finishTask`, removes
the blank row and returns to normal mode. The locally corrected sequence
adds Escape, asserts `INSERT` is absent, then sends `q`; exact post-exit board
bytes remain required. This sequence has not yet run on either native host.
The duplicate spec is prepared but is uncredited and must not advance if
creation fails.

The catalog remains a draft (eight normal cases, twelve edge/adversarial,
three candidate faults). No full scenario series, native-cell, fault
calibration, or Taskell admission credit exists. After the candidate
interactions are observed, freeze exact contracts, then complete the entire
20 x 2 x 12 native series, real baseline/mutant/restored phases, calibrations,
maintenance, relocation, audits, final candidate, and checked cleanup.

## Storage and next action

Storage v19 measured 151,279 bytes combined-retained headroom before the v20
and v21 curated evidence was added. Full Linux and Mac artifact extractions
were reduced to hashed JSON reports, final screens and runner/host identities;
the binary identities were verified and all temporary extractions removed.
Storage must be measured again before retaining a larger evidence packet.
Historical storage observations remain archived and indexed.

Next: commit/push the Escape sequence and preserve v21 evidence, then monitor
the fresh Ubuntu/Intel Mac native run. Verify the create report, exact board
bytes, natural exit and cleanup before attempting any candidate beyond it.
Do not claim project credit from this one-case exercise.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Standard GitHub-hosted validation and commit/push are authorized.
