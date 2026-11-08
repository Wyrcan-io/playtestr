# Continuation checkpoint v33: 8 November 2026

Branch `work/p0-p2-implementation` is at pushed commit `1163dcb4038e4a7d1594cfed280f3483d793de8c`. Four of twenty new projects are admitted (14/30 cumulative). Taskell remains the active target and has no admission credit.

## Run 42478754365

The corrected marker placement worked. Intel Mac job `128725852452` acquired the exact source, passed all 250 upstream tests, built Taskell 1.11.4 and Playtestr, and passed the existing-task smoke with cleanup. Its candidate batch attempted all 20 invocations: 18 passed once; E10 and E12 failed. E10 typed `n` but omitted Enter at the `(Y/n)` prompt, timed out waiting for exit 0, then cleanup observed exit 130. E12 only made the board file mode 0444; Taskell can replace a read-only file through its writable parent directory, so the target stayed open and the runner forced cleanup (exit 137). The batch correctly stopped the job before recorder validation. All 20 reports, host/binary identities, smoke report, and both failure screens are curated under `taskell/first-use-attempts/42478754365-macos/`; provider artifact and report hashes are in `taskell/build-attempt-v28.json`.

Ubuntu job `128725852774` passed toolchain setup but the pinned source download returned HTTP 503 before acquisition; it ran no target or scenario. Its diagnostic marker and provider identity are curated under `taskell/first-use-attempts/42478754365-linux/` and v28. This is a transient acquisition failure; the next two-host workflow will retry it.

E10 now sends Enter after `n`. E12 now denies writes at the fixture directory level and restores its permissions in a shell exit trap so runner cleanup can proceed. These changes are local, not yet tested or pushed.

## Candidate status and next gates

N01-N08 and E01-E12 have only exploratory first-route results so far. N06 and N08 corrected bytes pass on Intel Mac once; E10/E12 corrections are untested. Linux for this commit has no Taskell execution result. No scenario freeze, full 20 x 2 x 12 series, fault/mutant/restored phase, calibration, maintenance/relocation, complete audit, or Taskell admission credit exists.

Storage checkpoint v31 passed at 2026-11-08T12:43:44.756657Z; combined retained is 2,147,348,777 bytes with 134,871 bytes observed headroom. Receipt SHA-256: `58d20e9a8a29aa4968eee12ce46e32fbae92b1e8cd8f0a0073e880a3134b9b9a`.

Next: review the corrected JSON/shell inputs, push them with v28/v31/v33, and rerun both standard native hosts. Inspect all reports and screens before freezing. Continue Taskell's full series and all subsequent project gates, then work through the remaining 19 projects. No issue, PR, discussion, release, or outreach mutation was performed.
