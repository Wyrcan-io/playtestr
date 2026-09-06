# Platform support evidence

Sprint 4 release candidate `v0.1.0-rc.1` is verified on these native GitHub-hosted runners:

| Release target | Native runner | Terminal tests | Release package |
| --- | --- | --- | --- |
| Linux amd64 | `ubuntu-latest` | Passed | Passed |
| macOS arm64 | `macos-latest` | Passed | Passed |
| Windows amd64 | `windows-latest` | Passed | Passed |

The [terminal-test run](https://github.com/Wyrcan-io/playtestr/actions/runs/34035410517) for commit `bcd1b6e` passed unit and real-PTY integration tests, vet, the demo specs, the pinned Charm Gum trial, the deliberate snapshot mismatch, and evidence upload on all three hosts. Its artifacts are `terminal-evidence-ubuntu-latest`, `terminal-evidence-macos-latest`, and `terminal-evidence-windows-latest`.

The [release-candidate run](https://github.com/Wyrcan-io/playtestr/actions/runs/34048585717) validated each host's OS and architecture, built a versioned native binary with Go 1.25.0, ran the packaged-binary walkthrough, generated an archive and SHA-256 file, and uploaded `playtestr-linux-amd64`, `playtestr-darwin-arm64`, and `playtestr-windows-amd64`.

Windows amd64 also passes the race detector locally with the project compiler. Race-detector coverage has not been recorded for Linux or macOS.

This evidence supports only the targets in the table and the terminal behavior described in [Terminal compatibility](terminal-compatibility.md). It does not imply support for other architectures, every OS version or distribution, or every CLI/TUI framework.
