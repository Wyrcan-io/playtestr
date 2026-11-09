# Continuation checkpoint v67: Linux build passed; macOS toolchain gap repaired

Date: 10 November 2026 (Asia/Calcutta). Current-candidate admissions remain
**5/20 new projects** (15/30 cumulative); original-ten current-candidate
requalification remains **0/10**. mg remains zero-credit and has not launched.

## Native attempt on commit 50f08e1

GitHub run 42697606643 passed all native helper tests and exact source
acquisition on both hosts. Linux job 129433514356 passed the pinned source
build, install, help smoke and storage check in 10.8843 seconds. Its binary
SHA-256 is 6eb334f5ea96687983c51b073b1b8a11434ea85a46e69ca6e28e57b76b4e88e5.
The retrieved artifact SHA-256 matches provider digest
d0ee74b91e672368b97770cea5a7f9d693575c9c39aec97c55956f68a6f00779. A
readback verified the source archive, provenance, binary/runtime, all five
command logs and visible installed-file hashes.

Mac job 129433513867 passed the native helper tests and source acquisition but
failed before compiling mg: the macos-15-arm64 image has no autoreconf. Its
failed-command log and source/acquisition packet are retained locally in the
ignored campaign evidence path; receipt mg/native-macos-build-receipt-v1.json
records the provider attempt. This is a missing build prerequisite, not an mg
runtime result.

The Linux artifact also omitted the upstream hidden file doc/.mg because the
uploader defaults to excluding hidden files. The pinned file was inspected and
contains only mg editor mode settings. Receipt
mg/native-linux-build-receipt-v1.json records the successful build and this
evidence omission; the workflow now enables hidden-file retention for its
reviewed, bounded paths.

## Repair and next validation

When Autotools are absent, the build helper now downloads and SHA-256 verifies
official GNU M4 1.4.21, Autoconf 2.73 and Automake 1.18.1 archives, extracts
them under the owned mg target, builds into an owned prefix and records the
inputs and commands. Their exact URLs, release commits and checksums are
declared in mg/toolchain-dependencies-v1.json. The build receipt now records
compiler, make and Autotools version output. Linux can continue using the
host-provided tools while recording exact versions.

The three GNU xz archives were downloaded and their detached signatures
verified with gpgv and the official GNU keyring. Their tar layouts contain no
symlinks, hard links or special files and expand to 34.8 MB total. The official
Automake announcement's xz checksum disagrees with the bytes served by GNU FTP;
those bytes have a good signature from the announced release key. The observed
signed-byte SHA-256 is pinned and the discrepancy is retained in
mg/toolchain-source-preflight-v1.json. The bounded Windows scratch directory
was hash-checked and removed.

The next authorized push will rerun both native hosts with complete retained
hidden files and exact toolchain identities. The macOS source-built toolchain,
full native artifact readback and storage closure must pass before the mg PTY
pilot. No mg scenario, source fault or admission credit exists yet. The first
preflight failure and macOS missing-tool failure remain preserved.
