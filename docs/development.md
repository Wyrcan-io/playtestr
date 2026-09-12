# Development and repository checks

Use this guide for a source checkout. New users installing the standalone runner should follow the [stable installation walkthrough](releases/v0.1.0-installation-walkthrough.md).

Playtestr product code uses Go 1.25 or newer. Build the runner, deterministic fixture, and interactive demo from the repository root:

```powershell
go build -o bin/playtestr.exe ./cmd/playtestr
go build -o bin/fixture.exe ./cmd/fixture
go build -o bin/demo.exe ./cmd/demo
```

On Unix, omit `.exe` from output names.

Run the core checks:

```powershell
go test ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
go run ./cmd/playtestr test examples/menu.json examples/menu-exit.json
```

The race script requires the ignored project-local compiler under `.tools`. If it is absent, record the prerequisite as missing instead of reporting a successful race check.

The deliberately failing fixtures in `examples/` exercise timeouts, output limits, cancellation, cleanup, and snapshot mismatch. Their expected nonzero status is part of the check; do not treat an intended failure as a failed validation without inspecting its category and evidence.

Website development and validation are documented in [Repository website](website.md). Release packaging and publication evidence are documented in [Releasing](releasing.md).
