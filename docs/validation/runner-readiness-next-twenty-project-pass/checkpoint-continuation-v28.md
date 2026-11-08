# Continuation checkpoint v28 — 8 November 2026

Branch `work/p0-p2-implementation`; latest qualified candidate source revision
is `40735055c65cf1e1e49b620b881778078223501b`. Four of twenty new projects
are admitted on rc.6 (14/30 cumulative); the campaign is incomplete.

## Taskell progress

Pinned target:
`smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`
(151 verified primary source blobs, BSD-3-Clause). Taskell remains the only
active project until its full series, faults, audits and checked cleanup close.

After four preserved candidate corrections, run `42467040351` completed the
creation and duplication candidates on both Ubuntu 24.04 x86-64 and Intel
macOS 15 x86-64. Linux passed the initial run. Mac's first job hit HTTP 504
while installing Stack 3.11.1; the failed Mac job alone was rerun and passed.
Both hosts passed all 250 pinned upstream tests and the existing-task smoke.

On each host, creation passed 12/12 steps: observe the board and initial task,
create the new task, press Enter, positively verify INSERT mode, press Escape,
verify INSERT is absent, quit in normal mode, assert exit 0, and match exact
saved bytes for `board-basic.md`. The separate duplicate case passed 7/7,
asserting its exact `board.md` bytes. Reports confirm graceful process-group
termination and workspace cleanup for both cases on each host.

The same jobs completed public recorder review, fresh replay, export and
ordinary `playtestr test` on both hosts (one case, six of six steps, exact
state and cleanup). Per-host provider digests, native binary hashes, spec
hashes, report hashes, controls and console evidence are in
`taskell/build-attempt-v24.json` and `first-use-attempts/42467040351-linux/`
and `...-macos/`. The retained Mac directory also preserves the first
attempt's Stack 504 diagnostic; it does not overwrite or obscure the
successful Mac-only rerun.

These are one-shot cross-host candidate observations for two scenarios, not
the required native 20-case x 2-host x 12-repeat series or project admission.
The eight-normal/twelve-edge catalog is still an unfrozen draft. The three
candidate source faults remain untested. No Taskell native-cell, fault
calibration, final-candidate, complete maintenance/relocation/audit, or
admission credit is recorded.

## Next actions and constraints

1. Review the Taskell draft against observed screens/source, expand the
   remaining candidate specs/fixtures and adversarial cases, and freeze only
   after all exact transitions and saved bytes have been observed.
2. Build a bounded native-series workflow that repeats all 20 frozen cases 12
   times on each native host while reusing one pinned build per host; preserve
   each run/report and prove no order-dependent state leakage.
3. Implement and execute each of the three real target-source mutations with
   required baseline/mutant/restored phases on both hosts. Preserve every
   failure and exact mutation diff.
4. Complete calibration, candidate-case negative controls, maintenance and
   relocation, original-ten closure, all audits, final candidate, and checked
   source/artifact cleanup before admitting Taskell or moving to the next
   project.

Fresh storage checkpoint v20 (`storage-checkpoint-v20.json`) passed all
declared logical caps after the v20-v24 Taskell receipts were curated. It
records 151,107 bytes combined-retained headroom and 14,336,408 bytes new
curated headroom. Artifact downloads were reduced to text/JSON and hashes;
temporary binary extraction folders were removed. Measure storage again
before the next larger evidence packet and retain historical observations as
already archived. Do not delete evidence to recover cap space.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Commit/push and standard GitHub-hosted validation remain
authorized.
