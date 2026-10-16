# Development and repository checks

Use this guide for a source checkout. New users installing the standalone runner should follow the [stable installation walkthrough](releases/v0.1.0-installation-walkthrough.md).

On Windows, enable Git long-path handling when cloning this source repository; retained validation screens have deep provenance paths:

```powershell
git clone -c core.longpaths=true https://github.com/Wyrcan-io/playtestr.git
```

For an existing checkout, run `git config core.longpaths true` before changing revisions. This is a source-checkout prerequisite; standalone binary installation does not clone the evidence tree. Native CI supplies this Git setting through workflow-scoped environment variables before checkout.

Playtestr product code uses Go 1.25 or newer. Build the runner, deterministic fixture, and interactive demo from the repository root:

```powershell
go build -o bin/playtestr.exe ./cmd/playtestr
go build -o bin/fixture.exe ./cmd/fixture
go build -o bin/demo.exe ./cmd/demo
```

On Unix, omit `.exe` from output names.

This source includes `record` and `workflow`; see [recording](recording.md) and [workflow generation](generated-workflows.md). Native recorded-example validation is `python scripts/acceptance/recorded_journey.py` after installing pinned Gum v0.17.0 under `.tools/external`. It produces ignored synthetic evidence and ten fresh, delay-varied runs per example; it does not perform outreach or add campaign credits.

Run the core checks:

```powershell
go test ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
go run ./cmd/playtestr test --list examples/suite
go run ./cmd/playtestr test --artifacts-dir artifacts/playtestr --report artifacts/results.json examples/suite
```

The race script requires the ignored project-local compiler under `.tools`. If it is absent, record the prerequisite as missing instead of reporting a successful race check.

The deliberately failing fixtures in `examples/` exercise timeouts, output limits, cancellation, cleanup, and snapshot mismatch. Their expected nonzero status is part of the check; do not treat an intended failure as a failed validation without inspecting its category and evidence.

Website development and validation are documented in [Repository website](website.md). Release packaging and publication evidence are documented in [Releasing](releasing.md).
