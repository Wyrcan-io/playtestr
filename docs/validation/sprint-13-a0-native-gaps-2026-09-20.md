# Sprint 13-A0 native gap evidence — 20 September 2026

Status: complete on Windows amd64, Linux amd64 and macOS arm64. Native gap run
[`35507925555`](https://github.com/Wyrcan-io/playtestr/actions/runs/35507925555)
and complete terminal run
[`35507925481`](https://github.com/Wyrcan-io/playtestr/actions/runs/35507925481)
passed from commit `4298fe2ed3765c78f2f5f57716c162f31012eb3c`.

## Scope and identity

The local checkpoint started at commit
`f08a5cc55c0f5a798a3bcdfc20fb115cc524907c`; the final native evidence is tied
to immutable commit `4298fe2ed3765c78f2f5f57716c162f31012eb3c`. The local host
was Windows amd64, Windows build `26200.9457` (25H2), with Go `1.27.0` and
Windows PowerShell `5.1`. The workflow used the Go version selected by `go.mod`
on `windows-latest`, `ubuntu-latest` and Apple-silicon `macos-15`.

`scripts/test-native-gaps.ps1` runs each focused group with `go test -json`,
requires the named tests to finish as passes, inventories every terminal test
event, and fails on missing tests or unexpected skips. It first requires a
PowerShell executable, closing the path where installer tests could return a
green package result after silently skipping. On Windows, the one permitted
privilege skip is the ordinary symlink subtest; the native junction copy and
no-follow cleanup tests and the locked-file cleanup test remain mandatory.

## Evidence table

| Path | Source | Host | Command | Expected | Observed | Passes | Failures | Skips | Evidence | Exact blocker / next action |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Action-source installer | `4298fe2` | Windows amd64, `windows-latest` | `go test -count=1 -json ./internal/setupaction` | Three required top-level tests pass; no skip | exit 0, passed | 3 | 0 | 0 | Run `35507925555`, artifact `native-gaps-windows-amd64`; local JSONL under `artifacts/sprint13-a0/current` | None |
| Workspace v2 and native filesystem cleanup | same | Windows amd64, `windows-latest` | `go test -count=1 -json -run '^TestWorkspace' ./internal/runner` | Required common and Windows-specific cases pass; privilege limits visible | exit 0, passed | 13 | 0 | 0 remote; 1 local | Same Windows artifact and local JSONL | The local host skipped ordinary symlink creation because it lacked privilege. The native workflow ran it without a skip; junction rejection, junction no-follow cleanup and locked-file cleanup also passed. |
| Report v1/v2 rendering | same | Windows amd64, `windows-latest` | `go test -count=1 -json -run '^TestRenderHTML' ./internal/report` | Mixed suite and report-v2 workspace facts pass; no skip | exit 0, passed | 9 | 0 | 0 | Same Windows artifact | Browser presentation remains part of integrated A1, not this focused source checkpoint. |
| Process lifecycle and cleanup | same | Windows amd64, `windows-latest` | focused lifecycle regex recorded in `summary.json` | Natural/expected exits, timeouts, cancellation, flood, descendants, repeated sessions, blocked input and idempotent stop pass | exit 0, passed | 14 | 0 | 0 | Same Windows artifact | None |
| Installer, workspace, report-v2, lifecycle and cleanup | same | Linux amd64, `ubuntu-latest` | `./scripts/test-native-gaps.ps1 -EvidenceDirectory artifacts/native-gaps` | Three installer, eleven workspace, nine report and fourteen lifecycle tests pass; no skip | exit 0, passed | 37 | 0 | 0 | Run `35507925555`, artifact `native-gaps-linux-amd64`, digest `sha256:78ee9d260471b070a02e82d734245f9f464d901527201d5163880c31d5350813` | None |
| Installer, workspace, report-v2, lifecycle and cleanup | same | macOS arm64, `macos-15` | `./scripts/test-native-gaps.ps1 -EvidenceDirectory artifacts/native-gaps` | Three installer, eleven workspace, nine report and fourteen lifecycle tests pass; no skip | exit 0, passed | 37 | 0 | 0 | Run `35507925555`, artifact `native-gaps-darwin-arm64`, digest `sha256:a799a929865f098706f2735f6b39f790a6631afb0dae713bca0bcbe97b221a58` | None |

## Repair and verification

Source inspection found that a corrupt archive with a matching checksum used
different diagnostics in the ZIP and tar paths. The existing cross-platform
integration test requires `cannot inspect release archive`, but the Unix tar
path returned `cannot list release archive`. The tar path now uses the common
diagnostic, so the prepared Linux and macOS installer tests exercise the same
contract as Windows.

The first native run, `35507466220`, then exposed a test-only PowerShell 7
formatting difference: its rendered exception inserted ANSI-decorated source
context between `failed` and `after 1 attempts`. The bounded timeout itself
worked and left no installation outputs. The assertion now checks the stable
attempt-count phrase. The replacement native run passed that test on all three
hosts. The initial failure remains linked here rather than being hidden.

The final Windows working tree also passed `go test -count=1 ./...`,
`go vet ./...`, and
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1`.
The race run used the project-local GCC and completed every package. The
separate complete terminal run `35507925481` passed repository-wide tests, vet,
builds, native acceptance specs, the external Gum trial and deliberate-failure
evidence on all three hosts.

A built-binary walkthrough ran `examples/workspace.json`, emitted a passing
report-v2 document with `prepared=true` and `cleaned=true`, and rendered it to a
6,488-byte offline HTML report. The local outputs are
`artifacts/sprint13-a0/workspace-report-v2.json` and
`artifacts/sprint13-a0/workspace-report-v2.html`. The documentation site build
and its link, metadata and size validation also passed.
