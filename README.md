# playtestr

Headless, snapshot-based testing for interactive CLIs and terminal interfaces, written in Go.

Development follows [small, testable sprints](docs/sprints.md). The [language decision](docs/language-decision.md) records why the MVP uses Go. The current implementation includes Sprint 3 readable screen regressions and terminal resizing.

Playtestr starts a real pseudoterminal, sends keyboard input, and feeds output into a VT terminal emulator. Assertions inspect the rendered screen, including cursor movement and redraws.

## Try the demo

Requires Go 1.27 and a supported PTY host (Linux, macOS, or Windows with ConPTY).

```sh
go build -o bin/demo ./cmd/demo
go build -o bin/fixture ./cmd/fixture
go run ./cmd/playtestr test examples/menu.json
go run ./cmd/playtestr test examples/menu-exit.json
go run ./cmd/playtestr test examples/silent-input.json
go run ./cmd/playtestr test examples/screen-compat.json
go run ./cmd/playtestr test examples/resize.json
```

On Windows, add `.exe` to the two build output names. The same test commands work. Run `./bin/demo` to explore the demo manually: select an option with arrow keys and press Enter.

For development on this checkout, a project-local MinGW-w64 compiler can run Go's Windows race detector without changing the system PATH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
```

## Write a test

Specs are JSON. `command` is an executable followed by arguments and is executed directly without a shell. Executable lookup uses the environment that launches Playtestr. The `cwd` behavior is described below.

```json
{
  "name": "My CLI",
  "command": ["my-cli", "configure"],
  "width": 80,
  "height": 24,
  "timeout_ms": 3000,
  "run_timeout_ms": 30000,
  "max_output_bytes": 2000000,
  "steps": [
    {"expect": "Project name"},
    {"text": "hello"},
    {"key": "Enter"},
    {"expect": "Created hello"},
    {"exit": 0},
    {"snapshot": "created.txt"}
  ]
}
```

Each step has exactly one action. Supported keys: `Enter`, `ArrowDown`, `ArrowUp`, `ArrowLeft`, `ArrowRight`, `Escape`, `Tab`, `Backspace`, `CtrlC`. An `exit` step waits for the process and requires the exact exit code; intentionally nonzero expected codes are supported. Long-running TUIs do not need an exit step.

`expect` polls the current screen until the text appears or the per-step timeout expires. If the process exits first, the assertion reports the exit code instead of waiting for a timeout. Snapshots compare the rendered screen after at least 150 ms without output.

A snapshot must follow a successful `expect` since the most recent input or resize, or a successful `exit` assertion. This makes application readiness explicit; quiet output alone does not prove that an app has finished rendering. Choose expected text that identifies the new state rather than text left over from the previous screen.

Screen snapshots preserve leading spaces and internal blank lines while trimming trailing spaces and unused rows. They compare text rather than colors or styles. A mismatch prints a unified expected/actual diff and saves both `<spec>.actual.txt` and `<spec>.diff.txt` from the same captured screen.

Resize a running terminal with one action:

```json
{"resize": {"width": 100, "height": 30}}
```

The next snapshot requires a new successful `expect`, because resizing can trigger an asynchronous redraw.

### Session limits

`timeout_ms` limits each wait step and defaults to 3 seconds. `run_timeout_ms` limits the whole run and defaults to 30 seconds. `max_output_bytes` counts raw PTY output before terminal parsing and defaults to 2 MB. An optional `startup_timeout_ms` requires the target to render visible text within that interval; leave it unset for programs that legitimately wait for input before rendering.

Ctrl+C cancels the active spec, performs bounded cleanup, and prevents later specs from starting. Playtestr exits with status 130 for this interruption.

### Working directory and environment

When omitted, `cwd` remains the directory where Playtestr was invoked. A relative `cwd` is resolved from the test file's directory.

Targets receive a small operational environment including executable lookup, temporary-directory, home-directory, and locale variables appropriate to the operating system. Add literal values with `env`, or explicitly select more host variables with `inherit_env`:

```json
{
  "cwd": "../fixture-project",
  "env": {"APP_MODE": "test"},
  "inherit_env": ["CI"]
}
```

Environment values are never written to failure artifacts by Playtestr itself, although a target can still print them to its terminal.

```sh
go run ./cmd/playtestr test --update examples/menu.json
go run ./cmd/playtestr test --update --snapshot diagnostics.txt examples/menu.json
go run ./cmd/playtestr test examples/menu.json
go test ./...
```

`--update` explicitly writes baselines in a `snapshots` folder beside the spec. Updates stay in memory until the entire spec and process cleanup succeed. `--snapshot` updates one named baseline, requires `--update`, and accepts exactly one spec. Other snapshots still compare normally. Review baseline changes before committing.

A failure returns exit code 1. General failures save the final visible screen to `<spec>.actual.txt`; snapshot mismatches also save `<spec>.diff.txt`. Multiple spec paths can be passed to one invocation when no snapshot selector is used.

The repository includes deliberately failing fixtures for manual verification:

```powershell
go run ./cmd/playtestr test examples/hang.json
go run ./cmd/playtestr test examples/output-flood.json
go run ./cmd/playtestr test examples/child-cleanup.json
go run ./cmd/playtestr test examples/cancel.json
go run ./cmd/playtestr test examples/snapshot-mismatch.json
```

The first three commands fail promptly, report why they stopped, confirm their cleanup mechanism, and save the final screen. The cancellation example waits until you press Ctrl+C, then exits with status 130 after cleanup. The snapshot-mismatch example prints an intentional unified diff and saves matching screen and diff artifacts.

## Current scope

This is an initial local runner. The tested terminal behavior and known emulator gaps are recorded in [Terminal compatibility](docs/terminal-compatibility.md). It is not certification against every terminal application. Exact process exit-code assertions are supported.

Windows uses a Job Object and Unix uses a dedicated process group to terminate managed descendants. The current xpty API starts a Windows target immediately before Playtestr can attach it to the Job Object, leaving a small launch-to-attachment window in which a very early child could escape management. Unix descendants can deliberately detach into another session. Only test trusted applications; local PTY execution is not a sandbox.

The included GitHub Actions workflow runs the demo on Linux, macOS, and Windows and uploads failure screens. Local Windows validation does not establish that the remote matrix has passed.

Next milestone: versioned specs and machine-readable reports, release packaging, verified platform CI, and an external TUI trial. Recording and replay remain post-MVP work.

Built on [Charm's xpty](https://github.com/charmbracelet/x/tree/main/xpty) and [vt10x](https://github.com/hinshun/vt10x).
