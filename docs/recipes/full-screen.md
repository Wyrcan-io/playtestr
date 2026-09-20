# Full-screen modal and resize: bottom

Goal: bottom 0.14.9 filters to one harness-owned marker process, opens and closes
help, redraws at `80x24` and `120x40`, then exits 0. The binary/archive identities
are recorded in the [corpus manifest](https://github.com/Wyrcan-io/playtestr/blob/main/corpus/manifest.json).

## Setup and pass

Place the verified Windows binary at `.tools\recipes\bottom\btm.exe`. Build the
deterministic helper under the exact searchable filename, start it hidden, and
retain its process object:

```powershell
New-Item -ItemType Directory -Force .tools\recipes | Out-Null
go build -o .tools\recipes\PLAYTESTR-RS01X.exe ./cmd/fixture
$marker = Start-Process -FilePath (Resolve-Path .tools\recipes\PLAYTESTR-RS01X.exe) -ArgumentList hang -WindowStyle Hidden -PassThru
go run ./cmd/playtestr test examples/recipes/full-screen.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recipes/check-process.ps1 -ProcessID $marker.Id -ExpectedPath .tools\recipes\PLAYTESTR-RS01X.exe
```

The sequence proves the modal appeared before asserting disappearance. Each
resize is immediately followed by `wait_for_redraw` and a new positive marker;
an old pre-resize screen is not accepted as proof.

## Intentional failure and recovery

Stop the exact marker after verifying its executable path, run the spec and
require an assertion timeout at the marker lookup. Start a fresh exact helper and
rerun the unchanged spec and process oracle. An unrelated launch error, crash or
timeout at another step is not the intended control.

Cleanup: before stopping the marker, resolve its live PID to the expected helper
path. Stop only that PID and remove only the owned `.tools\recipes` files. On
Unix use the matching pinned bottom binary and helper name; historical WSL
evidence does not constitute a current native Linux or macOS claim.
