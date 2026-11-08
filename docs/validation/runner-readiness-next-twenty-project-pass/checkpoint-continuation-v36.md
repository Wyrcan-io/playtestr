# Continuation checkpoint v36: 8 November 2026

Branch `work/p0-p2-implementation` was at pushed commit `9eddb112748953c0e4842ae91a18167078be1985` for run `42486569216`. Four of the twenty new applications are admitted (14/30 cumulative). Taskell remains active and unadmitted.

## Run 42486569216

Ubuntu job `128749633533` and Intel Mac job `128749633785` both acquired the pinned Taskell source, passed all 250 upstream tests, built Taskell 1.11.4 and Playtestr, and passed the existing-task smoke. Each attempted all 20 candidate invocations: 19 passed and E12 failed on each host. The full reports, host/runner identities, and both failure screens are curated under `taskell/first-use-attempts/42486569216-{linux,macos}/`; v31 binds the 40 report hashes and provider artifact IDs/digests. Curated members were checked byte-for-byte against the downloaded artifacts. Linux artifact 13619164456 was 11,222,124 bytes (SHA-256 `f1ab1c3b3d7ac3ff2003c748b7573f8ac901b87d4169733f0345ea71abfba417`); macOS artifact 13620960385 was 6,800,242 bytes (SHA-256 `aea01128a2a7547a3dc2ecf4da75bd4a39fb8203c281fab6c33e2cbdbd3cdec0`).

The directory and `board.md` were read-only. Both Taskell builds returned exit 1 with `UnexpectedClosedException ... openBinaryFile: permission denied` after the save attempt; process and workspace cleanup succeeded. The run expected exit 0, so the E12 state step did not run. The local spec now expects exact exit 1 before checking the original board bytes. This corrected expectation has not yet run on either host.

The candidate batch failure skipped the recorder route. No candidate set freeze, native 20 x 2 x 12 series, fault/mutant/restored phases, calibration, maintenance/relocation, full audit, or Taskell admission credit exists. The other 19 cases are exploratory only.

Storage checkpoint v34 passed at 2026-11-08T14:15:49.578305+00:00 with combined retained 2,147,352,293 bytes and 131,355 bytes observed headroom. Receipt SHA-256: 390a5529610ca35395e548a2dec32199b3fa909dda705bf0265601280dce3bb2.

Next: commit and push v31, v34, v36 and the exact-exit/state spec correction; verify both hosted jobs. If the state step confirms unchanged bytes after the expected exit, proceed to review and run the public recorder route, then continue Taskell's remaining qualification gates and the other selected projects. No issue, PR, discussion, release, or outreach mutation was performed.
