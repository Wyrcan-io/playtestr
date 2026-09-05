# playtestr

Headless, snapshot-based testing for interactive CLIs and terminal interfaces, written in Go.

Development follows [small, testable sprints](docs/sprints.md). The [language decision](docs/language-decision.md) records why the MVP uses Go. The current implementation includes the Sprint 1 process-outcome prototype.

Playtestr starts a real pseudoterminal, sends keyboard input, and feeds output into a VT terminal emulator. Assertions inspect the rendered screen, including cursor movement and redraws.

## Try the demo

Requires Go 1.27 and a supported PTY host (Linux, macOS, or Windows with ConPTY).

```sh
go build -o bin/demo ./cmd/demo
go run ./cmd/playtestr test examples/menu.json
go run ./cmd/playtestr test examples/menu-exit.json
```

On Windows, build with `go build -o bin/demo.exe ./cmd/demo`. The same test command works. Run `./bin/demo` to explore the demo manually: select an option with arrow keys and press Enter.

For development on this checkout, a project-local MinGW-w64 compiler can run Go's Windows race detector without changing the system PATH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
```

## Write a test

Specs are JSON. `command` is an executable followed by arguments; it is executed directly without a shell. Command paths and the app's working directory are relative to the directory where you invoke playtestr.

```json
{
  "name": "My CLI",
  "command": ["my-cli", "configure"],
  "width": 80,
  "height": 24,
  "timeout_ms": 3000,
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

`expect` polls the current screen until the text appears or the per-step timeout expires. If the process exits first, the assertion reports the exit code instead of waiting for a timeout. Snapshots compare the screen after at least 150 ms without output and retry until timeout. Put an `expect` before snapshots to establish application readiness; quiet output alone does not prove an app has finished work.

```sh
go run ./cmd/playtestr test --update examples/menu.json
go run ./cmd/playtestr test examples/menu.json
go test ./...
```

`--update` explicitly writes baselines in a `snapshots` folder beside the spec. Review these changes before committing. A failure returns exit code 1 and saves the visible screen to `<spec>.actual.txt`. Multiple spec paths can be passed to one invocation.

## Current scope

This is an initial local runner. Text snapshots trim trailing spaces and blank rows; they do not compare colors or text styles. The emulator implements a subset of terminal behavior, so this is not certification against every terminal app. Exact process exit-code assertions are supported. The launched process is terminated after the test; descendant process-tree cleanup is not guaranteed. Only test trusted applications.

The included GitHub Actions workflow runs the demo on Linux, macOS, and Windows and uploads failure screens. Local Windows validation does not establish that the remote matrix has passed.

Next milestones: bounded sessions and process-tree cleanup, styled screen diffs, resize actions, recording/replay artifacts, then a reusable GitHub Action. A hosted PR reporting service and game-specific testing can share this runner later.

Built on [Charm's xpty](https://github.com/charmbracelet/x/tree/main/xpty) and [vt10x](https://github.com/hinshun/vt10x).
