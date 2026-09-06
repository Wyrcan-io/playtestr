# External TUI trial: Charm Gum

Sprint 4 tests Playtestr against [Charm Gum](https://github.com/charmbracelet/gum), an independently maintained Bubble Tea TUI. The trial is pinned to Gum `v0.17.0`; runtime execution is local and needs no network access.

Install the pinned binary into the ignored project tool directory:

```powershell
$env:GOBIN = Join-Path (Get-Location) '.tools\external'
go install github.com/charmbracelet/gum@v0.17.0
go run ./cmd/playtestr test examples/external-gum.json
```

On Unix, use the same `GOBIN` path with shell syntax. The spec opens `gum choose`, moves from Alpha to Beta, confirms the selection, asserts exit 0, and snapshots Gum's selected output. This proves one concrete external application and Bubble Tea path. It does not imply compatibility with every Gum command, Bubble Tea application, or terminal behavior.
