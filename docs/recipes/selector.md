# Selector: exact Gum result

Goal: Gum v0.17.0 selects the second item, emits exactly `Beta`, and exits 0.
The admitted Windows binary SHA-256 is recorded in the
[corpus manifest](https://github.com/Wyrcan-io/playtestr/blob/main/corpus/manifest.json). Runtime execution is offline.

## Setup and pass

```powershell
$env:GOBIN = Join-Path (Get-Location) '.tools\external'
go install github.com/charmbracelet/gum@v0.17.0
go run ./cmd/playtestr test examples/recipes/selector.json
```

Review [`selector.json`](https://github.com/Wyrcan-io/playtestr/blob/main/examples/recipes/selector.json): it waits for the
header, moves once, accepts, checks exit 0, then compares the exact reviewed
snapshot. The snapshot is evidence of the emitted selection, not merely the
presence of the candidate text in the menu.

## Intentional failure and recovery

```powershell
go run ./cmd/playtestr test examples/recipes/selector-wrong.json
go run ./cmd/playtestr test examples/recipes/selector.json
```

The first command must exit 1 with `snapshot_mismatch` and a `Beta -> Alpha`
diff. That failing runner report is a correctly detected campaign control, not a
passing Playtestr run. The unchanged original spec and baseline then recover.

Cleanup: Gum writes no recipe state. Remove only ignored reports/evidence created
for the attempt after reviewing them.
