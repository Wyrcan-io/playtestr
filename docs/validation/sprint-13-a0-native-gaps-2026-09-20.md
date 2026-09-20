# Sprint 13-A0 native gap evidence — 20 September 2026

Status: the available Windows amd64 checkpoint is complete. Linux amd64 and
macOS arm64 remain unavailable in this workspace and have concrete native jobs
prepared in `.github/workflows/native-gaps.yml`. A configured job is not a
passing result.

## Scope and identity

The checkout started at commit
`f08a5cc55c0f5a798a3bcdfc20fb115cc524907c`. The evidence below includes the
working-tree changes named in this record, so it is development evidence rather
than immutable release evidence. The available host was Windows amd64,
Windows build `26200.9457` (25H2), with Go `1.27.0` and Windows PowerShell
`5.1`.

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
| Action-source installer | `f08a5cc` + recorded patch | Windows amd64, build `26200.9457` | `go test -count=1 -json ./internal/setupaction` | Three required top-level tests pass; no skip | exit 0, passed | 3 | 0 | 0 | `artifacts/sprint13-a0/current/installer.jsonl` and `summary.json` | None |
| Workspace v2 and native filesystem cleanup | same | Windows amd64, build `26200.9457` | `go test -count=1 -json -run '^TestWorkspace' ./internal/runner` | Required common and Windows-specific cases pass; privilege limits visible | exit 0, passed | 13 | 0 | 1 | `artifacts/sprint13-a0/current/workspace.jsonl` and `summary.json` | `TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs/symbolic_link` skipped because this host cannot create an ordinary symlink. Junction rejection, junction no-follow cleanup, and locked-file cleanup passed. Obtain ordinary-symlink proof on a privilege-enabled Windows host before extending that claim. |
| Report v1/v2 rendering | same | Windows amd64, build `26200.9457` | `go test -count=1 -json -run '^TestRenderHTML' ./internal/report` | Mixed suite and report-v2 workspace facts pass; no skip | exit 0, passed | 9 | 0 | 0 | `artifacts/sprint13-a0/current/report-v2.jsonl` and `summary.json` | Browser presentation remains part of integrated A1, not this focused source checkpoint. |
| Process lifecycle and cleanup | same | Windows amd64, build `26200.9457` | focused lifecycle regex recorded in `summary.json` | Natural/expected exits, timeouts, cancellation, flood, descendants, repeated sessions, blocked input and idempotent stop pass | exit 0, passed | 14 | 0 | 0 | `artifacts/sprint13-a0/current/lifecycle-cleanup.jsonl` and `summary.json` | None |
| Installer, workspace, report-v2, lifecycle and cleanup | same prepared source | Linux amd64 | `./scripts/test-native-gaps.ps1 -EvidenceDirectory artifacts/native-gaps` in `ubuntu-latest` job | Same contract plus Unix symlink cleanup; no skip | unavailable; not run | 0 | 0 | 0 | `.github/workflows/native-gaps.yml`, artifact name `native-gaps-linux-amd64` when run | No native Linux host is attached to this workspace. Commit/push or explicit workflow dispatch is an external action and was not authorized. Run the prepared job and attach its JSONL and summary before closing Linux evidence. |
| Installer, workspace, report-v2, lifecycle and cleanup | same prepared source | macOS arm64 | `./scripts/test-native-gaps.ps1 -EvidenceDirectory artifacts/native-gaps` in `macos-15` job | Same contract plus Unix symlink cleanup; no skip | unavailable; not run | 0 | 0 | 0 | `.github/workflows/native-gaps.yml`, artifact name `native-gaps-darwin-arm64` when run | No native Apple-silicon host is attached to this workspace. Commit/push or explicit workflow dispatch is an external action and was not authorized. Run the prepared job and attach its JSONL and summary before closing macOS evidence. |

## Repair and verification

Source inspection found that a corrupt archive with a matching checksum used
different diagnostics in the ZIP and tar paths. The existing cross-platform
integration test requires `cannot inspect release archive`, but the Unix tar
path returned `cannot list release archive`. The tar path now uses the common
diagnostic, so the prepared Linux and macOS installer tests exercise the same
contract as Windows.

The final Windows working tree also passed `go test -count=1 ./...`,
`go vet ./...`, and
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1`.
The race run used the project-local GCC and completed every package. No Linux or
macOS pass is inferred from these Windows results, from cross-platform source
inspection, or from the prepared workflow.

A built-binary walkthrough ran `examples/workspace.json`, emitted a passing
report-v2 document with `prepared=true` and `cleaned=true`, and rendered it to a
6,488-byte offline HTML report. The local outputs are
`artifacts/sprint13-a0/workspace-report-v2.json` and
`artifacts/sprint13-a0/workspace-report-v2.html`. The documentation site build
and its link, metadata and size validation also passed.
