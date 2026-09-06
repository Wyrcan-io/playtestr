# Playtestr

**End-to-end testing for the terminal.**

Press the keys. Check the screen. Catch the regression. Playtestr drives interactive CLIs and TUIs through a real pseudoterminal, compares rendered text snapshots, and produces readable diffs when something changes.

[Get started](#install-and-try-the-demo) · [Write a test](#write-a-test) · [Spec v1](docs/spec-v1.md) · [Report v1](docs/report-v1.md)

- **Keyboard-driven tests:** describe an interaction in a small JSON spec.
- **Rendered screen assertions:** test text after cursor movement, redraws, and resizing.
- **Reviewable regressions:** compare snapshots and deliberately update a selected baseline.
- **Bounded execution:** set deadlines and output limits, with cancellation and process cleanup.

Written in Go. The MVP has a versioned test contract and machine-readable reports for trusted local applications.

Development follows [small, testable sprints](docs/sprints.md). The [language decision](docs/language-decision.md) records why the MVP uses Go.

Playtestr starts a real pseudoterminal, sends keyboard input, and feeds output into a VT terminal emulator. Assertions inspect the rendered screen, including cursor movement and redraws.

## Install and try the demo

Release archives contain one native `playtestr` binary, this README, the Apache 2.0 license, and an adjacent SHA-256 checksum. Download the archive for your host from [GitHub Releases](https://github.com/Wyrcan-io/playtestr/releases), verify the adjacent `.sha256` file, extract it, and put `playtestr` (or `playtestr.exe`) on your `PATH`.

Release-candidate targets are Linux amd64, macOS arm64, and Windows amd64. A target is published only after its native test and packaged-binary walkthrough pass. Until the first release is published, build from source with Go 1.25 or newer:

```sh
git clone https://github.com/Wyrcan-io/playtestr.git
cd playtestr
go build -o bin/demo ./cmd/demo
go build -o bin/fixture ./cmd/fixture
go build -o bin/playtestr ./cmd/playtestr
./bin/playtestr test --report results.json examples/menu.json examples/menu-exit.json
```

On Windows, add `.exe` to all three build output names and invoke `./bin/playtestr.exe`. Run `./bin/demo.exe` to explore the demo manually: select an option with arrow keys and press Enter.

For development on this checkout, a project-local MinGW-w64 compiler can run Go's Windows race detector without changing the system PATH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
```

## Write a test

Specs are JSON. `command` is an executable followed by arguments and is executed directly without a shell. Executable lookup uses the environment that launches Playtestr. The `cwd` behavior is described below.

```json
{
  "version": 1,
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

`version` is required. Playtestr rejects missing or unsupported versions before it launches a target. The complete defaults, limits, normalization rules, and JSON Schema are in [Test specification version 1](docs/spec-v1.md).

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

Write an ordered machine report with `--report results.json`. It includes stable status and failure categories, step metadata, target exit, cleanup evidence, and artifact paths. It deliberately excludes command arguments, environment data, typed text, and terminal-screen contents. See [Machine report version 1](docs/report-v1.md).

### Working directory and environment

When omitted, `cwd` remains the directory where Playtestr was invoked. A relative `cwd` is resolved from the test file's directory.

Targets receive a small operational environment including executable lookup, temporary-directory, home-directory, and locale variables appropriate to the operating system. Add literal values with `env`, or explicitly select more host variables with `inherit_env`:

```json
{
  "version": 1,
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

Sprint 4 also exercises the independently maintained Charm Gum TUI at a pinned version. See the [external Gum trial](docs/external-gum-trial.md) for its install and test commands.

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

The tested terminal behavior and known emulator gaps are recorded in [Terminal compatibility](docs/terminal-compatibility.md). Compatibility with one application does not certify every terminal application.

Windows uses a Job Object and Unix uses a dedicated process group to terminate managed descendants. The current xpty API starts a Windows target immediately before Playtestr can attach it to the Job Object, leaving a small launch-to-attachment window in which a very early child could escape management. Unix descendants can deliberately detach into another session. Only test trusted applications; local PTY execution is not a sandbox.

The GitHub Actions matrix runs native tests on Linux, macOS, and Windows and retains machine reports, screens, and diffs from its deliberate-failure check. Sprint 4's native results are recorded in [Platform support](docs/platform-support.md). Release candidates are packaged by a separate workflow; the process is documented in [Releasing](docs/releasing.md).

Recording, replay, exact-failure minimization, and styled snapshots remain post-MVP work.

Built on [Charm's xpty](https://github.com/charmbracelet/x/tree/main/xpty) and [vt10x](https://github.com/hinshun/vt10x).
