# Superfile development validation — complete; final freeze pending

Pinned MIT source: `yorukot/superfile` at
`66fe169b87021f7424522ed5aadd711c5676601e`. The target uses Bubble Tea v2;
Playtestr has no framework-specific code. The private build selects Go 1.27.0
and owns all target dependencies and caches. No updates, image previews,
external editors/openers, system clipboard, trash operations or user home are
needed for the admitted workflows. Targets remain trusted, unsandboxed programs.

Six normal and six edge scenarios have been recorded, inspected and replayed
through the public Windows recorder and CLI. Each also has a separate exact
file-state probe in its actual fresh managed workspace. These development
results did not by themselves qualify a native hosted campaign. The same twelve
ordinary contracts and separate state probes subsequently passed WSL exploration
without baseline variants. Hosted Linux/macOS later completed the development
qualification documented below; final frozen-source qualification is pending.

Normal workflows rename a spaced Unicode filename, search a noninitial nested
file and read its preview, create a nested Unicode file, copy across panels,
move across panels and copy exactly two nonadjacent selected files. Edge cases
exercise empty-directory recovery, no-match recovery, edited-rename
cancellation, permanent-delete cancellation, occupied-name refusal and repeated
resize with initially offscreen files and newly exposed Unicode preview rows.
Expected bytes include every unmodified neighbor; a clipboard caption alone is
never accepted as proof of a saved operation.

Reviewed row snapshots cover rows 4–20, retaining file lists, cursor and preview
state. Random managed path headers, host metadata and timing/clipboard paths
are excluded explicitly. Unique preview and transition checkpoints and exact
independent file probes complement that narrower screen region. Style, mouse,
image, full-grapheme fidelity and arbitrary external integrations are outside
this application qualification.

[Original first failures](first-failures/manifest.json) preserve unmodified
consoles. The welcome overlay required an observed disappearance before using
the preview beneath it. The pinned application displays “No such file or
directory” for an existing empty directory; this is a target presentation
finding, not a missing fixture. That caption was already visible in the second
panel, so the recorder correctly rejected it as a stale post-Tab anchor. A fresh
metadata transition is used instead. Selection mode requires explicit Enter
toggles; mode switching alone does not prove selection. Resizing required a
newly exposed preview row rather than reasserting an already visible line.

The real recorder also rejected the ordinary `CtrlR` rename shortcut. The
general product repair supports all Ctrl+A–Z terminal bytes, with schemas and
migration documentation updated. Ten native Windows and ten WSL reduced
controls verified all 26 exact bytes. A Windows helper initially interpreted
Ctrl+Z as Go standard-input EOF; its test-only reader now observes the native
console bytes directly. This is a helper correction, not a ConPTY data-loss
claim. Native Linux/macOS/Windows checks of this repair subsequently passed
at sources `e2a6b8c` and `4c90d39`.

Two actual source mutations—wrong rename destination and search cancellation
that retains the no-match filter—were detected without contract changes. A
third source mutation corrupts the copied, nonpreviewed `charlie.txt`: ordinary
terminal replay stays green, while the independent exact-file probe rejects
the saved corruption. All three restored exact source bytes and reproducible
target binary identity, then passed ordinary and independent-state recovery.
[Definitions](faults/definitions.json) and licensed minimal patches retain the
reproduction; compact native evidence will be retained after hosted runs.

Manual text editing, intentional mismatch, HTML diagnosis, selected update,
ordinary recovery, spaced Unicode relocation, workflow preview and meaningful
suffix rerecord passed while preserving primary contracts. The prepared public
operator route used four commands and 17 recorder controls with no manual JSON
edits; 4.094 seconds excludes acquisition, engineering and prior corrections.
It is an automated warm-cache operator measurement, not beginner authoring time.
Native development repetitions and owned teardown completed at `4c90d39`.
Final single-source qualification remains pending. This report makes no beginner
usability, complete application coverage or launch-readiness claim.

First native run `38317936008` at `e2a6b8c` passed all three product-control
jobs; the separate standard smoke also passed all three hosts. Neither
application job qualified. Linux's search state probe exposed P08: a genuinely
new filtered result was rejected when it rendered before Enter. A real reduced
regression reproduced this timing-dependent recorder defect. The general fix
retains the screen before the first input since the last checkpoint, including
prefix reconstruction, while still rejecting captions unchanged throughout the
sequence. The same reviewed superfile contract passed ten fresh Windows state
probes after the fix. Native requalification subsequently passed all three
core jobs at `4c90d39` / `38319592021`; the same run completed 120 ordinary
and 120 separate state repetitions on Linux and macOS, actual faults,
restoration and confirmed owned teardown. Local Windows/WSL source, binaries,
dependencies and retained diagnostic workspaces were also removed. Exact
host/runner identities are in [the result](result.json) and compact actual
evidence in [the native manifest](../native/38319592021/manifest.json).

Windows ordinary copy repetition six instead timed out with an unrequested
help overlay. A separately race-instrumented, otherwise unchanged target
confirmed an actual shared-buffer race inside its pinned Ultraviolet Windows
input dependency. [Original race stack](first-failures/confirmed-upstream-input-race.txt)
records the concurrent producer write and consumer read. This confirms a target
dependency fault without establishing that particular overlay's precise cause.
No target patch, silent retries, artificial input sleeps or accepted failure
snapshot replace the original result. Windows superfile remains unqualified.
[The explicit host-plan adjustment](../native-host-adjustments.json) uses
Linux/macOS for this project and adds Windows to Glow's planned Linux/macOS
matrix. Ten Linux, five Windows, five macOS and at least twenty actual
project-host qualifications remain mandatory gates.

## Final frozen qualification

Final source `e8682f866622442c421005c7f477cd45fcc66fc5` / [run 38802794545](https://github.com/Wyrcan-io/playtestr/actions/runs/38802794545) passed the strict batch audit on Linux, macOS: 120 ordinary plus 120 separate final-group state probes per host, real source-fault/restoration controls and verified owned removal. [Machine receipt](final-frozen-qualification.json). Earlier pending text records development-time status; this receipt qualifies only the stated terminal/state matrix. [Usability limits](../usability-assessment.md) and [remaining limitations](../limitations.md) still apply.
