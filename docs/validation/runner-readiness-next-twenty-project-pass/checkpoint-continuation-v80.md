# Runner readiness continuation checkpoint v80

Campaign remains at **15/30 project admissions**. Five new projects are admitted on the recorded candidate; ten original projects have no current-candidate requalification credit; the mg candidate remains at zero admission credit.

## mg candidate state

Pinned source `troglobit/mg` at `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`, candidate `v0.4.0-rc.6`. N01 first-use and N02/N03/N04 development probes passed on Linux/macOS. Current N02-N04 development attempts across the initial and repeat workflows total 32 host attempts, 24 passed and 8 failed.

N05 first native attempt was run on workflow `42722834841` (commit `9cbecad19460e5fe5c7b84798eb4b38626e1addb`) and failed on both native hosts at step 10. First undo of an insertion returned the buffer to `seed`; the second undo could not redo it and displayed ?No further undo information?. Both target groups were forcibly stopped and confirmed exited, and owned workflow inputs were removed. Downloaded host artifacts were retained as 41-member CRC-checked ZIPs. Full evidence is in `mg/n05-first-attempt-readback-v1.json`.

Pinned `src/undo.c` explains the failure. Its inverse recording supports redo for undoing a deletion, not for undoing an insertion. The corrected N05 contract begins with `seed changed`, deletes the suffix with eight Backspace actions, asserts `seed`, then performs two `C-x u` operations to restore `seed changed` and redo deletion to `seed`. The fixture and exact final state now use `seed changed\n` and `seed\n`, respectively. Local focused contract/build/pilot tests passed (16 tests, 4 POSIX-only skips).

The corrected N05 native workflow has **not** run. Next: inspect the contract/source-review diff and hash, commit and push the focused correction, run the authorized Linux/macOS native matrix, download and CRC audit both host artifacts, preserve every attempt, then update counters/readbacks/checkpoint. Do not credit N05 or mg admission until the stated higher qualification gates are met.

Unrelated untracked Codex caches, Skim artifacts, draft evidence, and the existing v46 checkpoint remain preserved.
