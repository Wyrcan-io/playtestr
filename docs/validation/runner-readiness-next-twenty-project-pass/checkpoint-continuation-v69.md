# Continuation checkpoint v69

## Current count

Five of twenty new-project admissions are credited; fifteen of the overall
thirty are complete. The historical ten remain at zero current-candidate
requalification. mg remains zero credit.

## Native build run 42703483568 on commit d922a18

Linux completed successfully. macOS passed all 12 helper tests and exact source
acquisition, then failed while building pinned GNU M4. Its release archive
contains generated `aclocal.m4`, but safe extraction writes ordinary source
inputs afterward with newer filesystem timestamps. Make consequently tried to
regenerate `aclocal.m4` using `aclocal-1.18`, which cannot exist before the
Automake stage. The retained macOS artifact (13712192819) passes ZIP CRC and
its local SHA-256 agrees with the GitHub provider digest. Receipt
`mg/native-macos-build-receipt-v3.json` records the failure precisely.

The build helper now refreshes timestamps on each pinned release's generated
`configure`, `Makefile.in` and `aclocal.m4` after safe extraction, preserving
the signed/released build inputs rather than invoking not-yet-built bootstrap
tools. A targeted regression checks this behavior. The full bounded helper
suite passes locally (13 tests, three POSIX-only skips on Windows), as do Python
compilation, whitespace and storage checks. The next push will rerun both
native hosts; inspect M4, Autoconf, Automake and mg outputs separately before
starting behavior pilots.

Storage at this checkpoint: combined raw 3,963,035,333 bytes and combined
retained 2,121,434,590 bytes, within the configured caps. No mg scenarios,
source faults, or admission credit have been earned.
