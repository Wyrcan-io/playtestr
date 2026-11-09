# Continuation checkpoint v68

## Current count and candidate

Five of the next twenty new projects have candidate admission credit; the
overall thirty-project request therefore has fifteen of thirty credits so far.
The ten historical projects have zero requalification credit for the current
candidate. The current candidate is `v0.4.0-rc.6`; the prior aggregate remains
the exact `v0.4.0-rc.5` record. mg is acquired and has no scenario, fault or
admission credit.

## Native mg attempt on commit 02b2326

GitHub run 42701808766 completed Linux successfully and failed on macOS during
the locally built Automake 1.18.1 toolchain. Linux job 129448144389 passed the
12-test native helper suite, exact source acquisition, pinned source build,
install, runtime smoke, hidden-file inventory, process-tree cleanup and
storage check. Its retrieved ZIP hash and payload checks are recorded in
`mg/native-linux-build-receipt-v2.json`.

macOS job 129448145020 passed the same helper suite and source acquisition.
Artifact 13712171222 was downloaded and hash-checked against GitHub's digest;
the ZIP passes CRC validation. Its Automake build log shows the out-of-tree
bootstrap trying to create `build_dir/t/testsuite-part.tmp` before that build
directory exists. The verified Automake release archive has a source `t/`
directory; the missing path is specifically the separate build directory.
Receipt `mg/native-macos-build-receipt-v2.json` preserves this failure and
artifact identity.

The build helper now creates the owned Automake build-side `t/` directory
after configure and before `make`. Targeted Windows tests pass for the helper's
portable cases; three POSIX process/output tests are skipped on Windows and
were already observed passing on the native Linux/macOS hosts in run
42701808766. Python compilation and whitespace checks pass. The next commit is
authorized to push and will trigger a fresh dual-host build. Review the new
macOS logs and artifact completely before starting an mg PTY pilot.

The macOS artifact is retained locally at
`artifacts/runner-readiness-next-twenty-project-pass/native/mg/next20-mg-build-darwin-42701808766.zip`.
An additional copy of the pinned Automake source archive was used to inspect
its directory layout, its verified hash matched, and the copy was removed.
Current local storage audit passes: combined raw 3,960,452,147 bytes and
combined retained 2,118,851,404 bytes, both within their campaign limits.
