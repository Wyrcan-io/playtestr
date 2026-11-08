# Continuation checkpoint v27 — 8 November 2026

Branch `work/p0-p2-implementation`; last pushed candidate validation source
is `37b33a78d67ea313e67528d77b8d1e3e8cb4ecb3`. A new local correction makes
the create-task state assertion read `board-basic.md`, the file the candidate
launches. Campaign status remains 4/20 new project admissions (14/30 total).

## Taskell qualification

Pinned source is
`smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`;
151 primary source blobs are verified. Keep Taskell as the only active target
until its candidate, native series, faults, calibrations, audits and cleanup
are complete.

Historical first-use route run `42456298245` passed its 250-test suite,
existing-board smoke and public recorder/replay/export/ordinary-test path on
both Ubuntu and Intel macOS (receipts v18/v19). It remains first-use evidence
only.

The later candidate attempts each exposed and preserved a distinct issue:

- Run `42458747709`, receipt v20: fixture filename mismatch (`board.md` vs
  `board-basic.md`) caused Taskell to prompt to create a missing board on both
  hosts.
- Run `42460993289`, receipt v21: after the filename fix, Enter kept Taskell
  in INSERT mode; `q` became task text and exit timed out on both hosts.
- Run `42462915946`, receipt v22: runner rejected `expect_not INSERT` because
  the spec had no prior positive expectation. No Taskell process was launched.
- Run `42464484824`, receipt v23: Ubuntu failed before build because Stack
  download returned HTTP 504 twice. Intel macOS passed all 250 tests and
  existing-task smoke; create-task interactions, Escape-to-normal, natural
  exit 0, process cleanup and workspace cleanup passed. Step 12 failed because
  the state assertion looked for `board.md` although Taskell was launched on
  `board-basic.md`. Exact saved bytes were therefore not asserted. The Linux
  failure excerpt and Mac report/screen/identity hashes are retained.

The local candidate now checks the state of `board-basic.md`. It includes the
positive INSERT observation, Escape, negative INSERT assertion, normal quit,
exit 0 and exact expected serialized bytes. This final path correction has
not yet run on either native host. The duplicate candidate is prepared but
must not advance unless creation passes its state, exit and cleanup assertions.
Taskell remains at zero complete scenario credit, native-series credit, fault
calibration or admission.

The catalog remains an unfrozen eight-normal/twelve-edge draft with three
candidate source mutations. After actual observed routes are frozen, complete
the entire 20 x 2 x 12 native series, real baseline/mutant/restored fault
phases, calibrations, maintenance, relocation, audits, final candidate and
checked cleanup. Do not assign admission from first-use or candidate runs.

## Storage and next action

Storage v19 recorded 151,279 bytes of combined-retained headroom before later
small receipts/screens. Full artifact extractions were curated to text and
identity files, binary hashes were recorded, and temporary native-binary
directories were removed. Run the storage measurement before retaining a
larger packet. Historical storage observations remain losslessly archived.

Next: commit/push the corrected state path, then monitor both native jobs and
verify the report's saved-state match, exit 0, process termination and
workspace cleanup. Continue to the duplicate case only when that gate passes.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Standard GitHub-hosted validation and commit/push are authorized.
