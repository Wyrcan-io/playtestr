# Continuation checkpoint v72

## Progress

The campaign remains at 15/30: five of the next twenty new-project admissions
have credit, and none of the original ten has current-candidate requalification.
mg remains unadmitted with zero credit.

## mg build and exact-candidate pilot

Native Linux and macOS mg builds passed on GitHub run 42705501183. The exact
frozen Playtestr candidate remains v0.4.0-rc.6. The first two PTY workflow runs
(42710258730 and 42710906900) refused both hosts before launching mg because the
pilot's hard-coded commit string had one incorrect character. Linux cleanup
passed; macOS cleanup initially rejected the combined downloaded inputs because
the file-count cap was 100. The pilot constant now comes from the reviewed
`mg/source-provenance.json` value in a focused unit check; cleanup accepts up to
256 regular files while retaining its 32 MiB byte limit. The observed macOS
artifact input tree had exceeded the old cap.

On run 42711988263, Linux passed the native helper tests, downloaded both
artifacts, installed and hash-verified the frozen candidate, and started the
runner. The rc.6 report then recorded `workspace_setup_failure`: it could not
resolve `mg` through PATH, so all ten PTY steps were `not_run` and the target
was not attempted. Runner process cleanup and exact input cleanup passed. The
4,630-byte job artifact was downloaded and independently matched GitHub's
SHA-256; its report and log hashes are in `mg/pilot-attempt-accounting-v1.json`.
Inspection of the original mg build ZIP found the target entry stored with mode
100755, but the hosted post-download mode was not captured before cleanup. The
latest pilot code records both modes, restores the owner execute bit, and checks
that the target is executable after matching its receipt hash; treating artifact
permission loss as the cause remains a hypothesis until the next hosted result.

The macOS job from 42711988263 remained queued at readback. The updated retry
from commit 90ad40a0 is run 42712723851 and was pending without jobs at readback.
No PTY target journey has passed and mg receives no admission credit.

The independent build receipts `native-linux-build-receipt-v3.json` and
`native-macos-build-receipt-v5.json` contain a transcription error in their
top-level pin (`...a62...`). The reviewed source provenance and the downloaded
Linux artifact `build.json` identify `...d62...`; the artifact receipt hash is
recorded in the attempt accounting erratum. Preserve the original summaries and
use the erratum, source provenance, and downloaded build packet for the exact
pin identity.

## Storage and next steps

The last local mg storage audit passed: combined raw 3,972,494,912 bytes,
combined retained 2,130,894,169 bytes, and combined curated 35,025,275 bytes.
The retained Linux attempt ZIP and its extracted report are inside the campaign
raw tree. Next inspect the queued native jobs, verify the captured downloaded
mode on each host, then require the public N01 PTY journey, exact saved bytes,
confirmed target exit, repeated host matrix, source-fault calibration, and
independent report audit before granting any project credit.
