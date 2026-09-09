# Platform support evidence

Release candidate `v0.1.0-rc.2` is verified on these native GitHub-hosted runners:

| Release target | Native runner | Terminal tests | Release package |
| --- | --- | --- | --- |
| Linux amd64 | `ubuntu-latest` | Passed | Passed |
| macOS arm64 | `macos-latest` | Passed | Passed |
| Windows amd64 | `windows-latest` | Passed | Passed |

The [terminal-test run](https://github.com/Wyrcan-io/playtestr/actions/runs/34035410517) for commit `bcd1b6e` passed unit and real-PTY integration tests, vet, the demo specs, the pinned Charm Gum trial, the deliberate snapshot mismatch, and evidence upload on all three hosts. Its artifacts are `terminal-evidence-ubuntu-latest`, `terminal-evidence-macos-latest`, and `terminal-evidence-windows-latest`.

The historical [Sprint 4 packaging run](https://github.com/Wyrcan-io/playtestr/actions/runs/34048585717) built and exercised binaries before packaging. It established the initial packaging path but did not execute the extracted archives.

The [v0.1.0-rc.1 release run](https://github.com/Wyrcan-io/playtestr/actions/runs/34052977944) closed that gap at commit `1dde372282a574025957c4bf1b603287cbef93e4`. Each native job built and packaged the runner, verified its SHA-256 checksum and exact archive member list, extracted it into a path containing spaces, and invoked that extracted binary. Version/help output, passing specs, a deliberate `snapshot_mismatch`, its report, and screen/diff evidence passed before the assets were uploaded.

The published [v0.1.0-rc.1 prerelease](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.1.0-rc.1) contains the three native archives and their checksum files. All six files were downloaded again through their public release URLs and matched the workflow artifacts byte-for-byte. The tag resolves to the commit above.

The repaired [published-install run](https://github.com/Wyrcan-io/playtestr/actions/runs/34332701717) downloaded rc.1 again and passed checksum rejection, spaced-path extraction, version/help, good → bad → recovered behavior, missing-target and invalid-spec handling, report-write failure, and cleanup on Linux amd64, macOS arm64, and Windows amd64. The run used workflow commit `9cf00e89f378703d66b6bc05978777c6dc8e2ec1`. Its Unix `/dev/tty` gate was explicitly disabled because rc.1 is the known-bad baseline; this run validates installation behavior, not the missing controlling terminal.

A later real-application trial found that the rc.1 Linux asset does not provide a controlling terminal to targets that open `/dev/tty` directly. Lazygit v0.65.0 therefore exits during launch even though the original release fixture suite passed. That defect remains part of rc.1's historical record.

The published [v0.1.0-rc.2 prerelease](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.1.0-rc.2) replaces those bytes. [Native packaging run 34333242993](https://github.com/Wyrcan-io/playtestr/actions/runs/34333242993) built it from `583352ad381df15f0fda652dae9ef819f5f24c9a`; every native job exercised the extracted archive, and Linux and macOS passed a target that opens `/dev/tty`. [Published install run 34333615063](https://github.com/Wyrcan-io/playtestr/actions/runs/34333615063) then downloaded the public candidate with controlling-terminal verification enabled and passed on all three hosts. The public archives matched the workflow artifacts byte-for-byte.

Downloaded rc.2 passed natural exit, cancellation, total timeout, output limit, and descendant-cleanup release fixtures on Windows and Linux. Candidate-specific real-application evidence includes 10/10 Lazygit stage attempts on each of Windows and Linux, plus 10/10 Lazydocker log attempts on Windows, with independent exact-state oracles. Linux Lazygit also passed stage/unstage, commit, branch, help/resize, and a separately labeled second session. Docker/Kubernetes candidate cells remain unexecuted because the Docker daemon became unavailable during the sample. This is an infrastructure interruption, not compatibility evidence. The historical six-cell campaign remains separate because its Linux runner came from a checkout.

Windows amd64 also passes the race detector locally with the project compiler. Race-detector coverage has not been recorded for Linux or macOS.

Current source passed the complete [three-host Terminal tests run](https://github.com/Wyrcan-io/playtestr/actions/runs/34331447263) at commit `6c378a5cc34efb481bc61bd4ce1cad2862a82ef9`. The immediately preceding [failed run](https://github.com/Wyrcan-io/playtestr/actions/runs/34330189067) is retained: it exposed a macOS cleanup exit race and a cold-start budget issue in the external Gum sample. Both causes were corrected before the green run.

This evidence supports only the targets in the table and the terminal behavior described in [Terminal compatibility](terminal-compatibility.md). It does not imply support for other architectures, every OS version or distribution, every CLI/TUI framework, or the pending real-application candidate cells.
