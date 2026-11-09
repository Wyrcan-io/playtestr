# Continuation checkpoint v73

## Campaign count

The campaign remains at **15/30**: five of the twenty new-project admissions
have credit; the original ten have zero current-candidate requalification.
mg is one candidate in progress and has not earned an admission.

## mg N01 pilot passed on both native hosts

Run 42712723851 executed the reviewed v3 first-use spec on the exact frozen
`v0.4.0-rc.6` candidate and pinned mg build. Linux (`ubuntu-24.04`, x86_64) and
macOS (`macos-15`, arm64) each reported one passing case, all ten actions
passed, exact-state outcome matched, and target exit code 0. Both targets exited
gracefully with confirmed process cleanup; both Playtestr runner process groups
were absent after completion. Candidate/build input removal passed on both
hosts, including the 115-file macOS input tree.

The two downloaded evidence ZIPs match their GitHub provider digests and pass
local archive extraction. Receipts, attempt identities, report and runner-log
hashes, host outputs, and cleanup receipts were independently cross-checked in
`mg/pilot-n01-native-readback-v1.json`. The captured target mode was `0644` on
both hosted runners; restoring the owner execute bit to `0744` fixed the PATH
lookup failure from the prior Linux attempt.

The state report says the exact saved-byte assertion matched, but it retains
only that outcome, not the observed file bytes or hash. Do not describe these
reports as containing an independently captured `pilot.txt` copy. The public
spec and report do provide positive evidence that the rc.6 runner evaluated its
exact-byte assertion successfully.

The curated native build summaries have a one-character source-pin
transcription error. The exact reviewed pin is `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`;
the downloaded build receipts agree. Errata and preserved failures are linked
from `mg/pilot-attempt-accounting-v2.json`.

The project work also exposed a stale named-key list in `docs/writing-tests.md`:
the runner and spec contract support every `CtrlA` through `CtrlZ`, but the
author guide listed only a subset. The guide is corrected to match the existing
contract; the mg pilot exercised `CtrlX`, `CtrlS`, and `CtrlC` on both hosts.

## Remaining mg qualification gates

This was one first-use pilot on each host, not the project qualification. Keep
mg at zero credit while completing the frozen 20-scenario package, repeated
ordinary trials on each planned host, at least three real source-fault
calibrations, independent report/accounting audit, and final storage and
cleanup checks. Preserve every attempt and unsupported boundary.

## Next action

Review the 20-scenario draft against real mg behavior and the rc.6 public author
workflow. Freeze the ordinary and edge contracts before qualification runs; do
not count the pilot as an ordinary matrix execution. Then run the matrix and
fault calibrations on Linux and macOS, retain all evidence, and repeat the
required legacy-project and migration gates for the eventual candidate claim.

The latest storage check passed with combined raw 3,972,526,519 bytes, combined
retained 2,130,925,776 bytes, and combined curated 35,044,374 bytes.
