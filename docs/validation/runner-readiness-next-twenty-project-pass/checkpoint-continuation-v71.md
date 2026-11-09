# Continuation checkpoint v71

## Progress count

Five of the next twenty new-project admissions have credit; the overall total
is fifteen of thirty. The historical ten have zero current-candidate
requalification. mg remains a candidate with zero admission credit.

## Native mg build completed

GitHub run 42705501183 passed on both Ubuntu 24.04 x86_64 and macos-15-arm64.
Both hosts passed 12/12 native helper checks, exact pinned mg source acquisition,
source build, install, `mg -h`, storage limits, evidence upload and cleanup.
On macOS, pinned M4, Autoconf and Automake were built under the owned target
prefix; all three source archive hashes and the Automake signature/checksum
discrepancy remain recorded in the toolchain evidence.

Artifacts 13713367836 (Linux) and 13713766830 (macOS) were downloaded. Their
local SHA-256 values match the GitHub provider digests and each ZIP passes CRC
validation. Independent readback verified the exact mg source archive and map,
binary/runtime hashes, every installed file, all command output lengths/hashes,
the hidden `.mg` file, and clean command process groups. The Linux and macOS
receipts are `mg/native-linux-build-receipt-v3.json` and
`mg/native-macos-build-receipt-v5.json`.

The current candidate remains exactly `v0.4.0-rc.6`. This native build did not
run mg through Playtestr and proves no PTY behavior, canonical scenario,
repetition, source fault or admission. Next: use the frozen exact candidate
archive on each native host for an N01 first-use PTY pilot, independently
review screen and saved bytes, then freeze the public 8-normal/12-edge matrix.

The original Linux and macOS candidate workflow artifacts were fetched and
verified against their provider digests. Their embedded archive and runner
hashes match the frozen manifest and already retained canonical archive files.
The redundant outer ZIP copies were removed after this check; exact identities
are in `mg/candidate-archive-preflight-v1.json`.

The N01 pilot contract `mg/pilot-n01.json`, bounded runner `next20_mg_pilot.py`,
input cleanup helper, focused tests and native Linux/macOS workflow
`runner-readiness-next20-mg-pilot.yml` are prepared. The workflow downloads the
successful mg build packet and the exact frozen rc.6 candidate artifacts by
their original run IDs, verifies the exact archive/binary hashes, and exercises
the public v3 PTY, visible save confirmation, exact state and cleanup paths.
No pilot result exists yet.

Latest local storage audit: combined raw 3,972,480,238 bytes and combined
retained 2,130,879,495 bytes, within limits.
