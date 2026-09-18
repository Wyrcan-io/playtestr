# Repeatable workspaces

Specification version 2 gives each test a fresh copy of a small reviewed fixture. It is intended for local state such as first-run files, generated project files, application home data, and temporary files. It is opt-in: version 1 behavior is unchanged.

```json
{
  "version": 2,
  "name": "stateful first run",
  "command": ["../bin/fixture", "workspace"],
  "workspace": {
    "fixture": "workspace-fixture",
    "cwd": ".",
    "home": "temporary",
    "temp": "temporary"
  },
  "steps": [
    {"expect": "fresh workspace seed=reviewed home=true temp=true"},
    {"exit": 0}
  ]
}
```

`workspace.fixture` is required and resolves below the spec directory. Playtestr copies that directory to the `fixture` directory inside a unique runner-owned OS temporary root. `workspace.cwd` defaults to `.` and resolves inside the copy. It must exist as a directory. Top-level `cwd` is not part of spec v2, so there is no ambiguous precedence.

The executable is resolved before the working directory changes. A command containing `/` or `\` is relative to the spec directory unless absolute; a bare name is resolved through `PATH`. On Windows the ordinary executable extension lookup applies. A same-named program inside the fixture is never selected implicitly. Put fixture programs outside the workspace and select them explicitly if they are trusted.

`home` and `temp` may be omitted or set only to `"temporary"`. On Unix, managed home sets `HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `XDG_STATE_HOME`; managed temp sets `TMPDIR`. On Windows, managed home sets `USERPROFILE`, `HOME`, `APPDATA`, `LOCALAPPDATA`, `HOMEDRIVE`, and `HOMEPATH`; managed temp sets `TEMP` and `TMP`. A spec cannot declare or inherit a variable managed by its selected workspace options. Other `env` and `inherit_env` rules remain unchanged.

## Bounds and filesystem rules

The fixture may contain at most 2,000 filesystem entries including at most 1,000 regular files, 32 MiB total contents, 8 MiB per file, and 32 path components below its root. Copying has a 30-second ceiling and also consumes the spec's `run_timeout_ms`. Files and directories only are accepted: symbolic links, junctions, other reparse points, sockets, devices, and other special entries fail before target launch. Link-like fixture path components are rejected too.

Executable permission is retained on Unix. Ownership, privileged bits, and host-specific attributes are not copied. Windows and macOS case-insensitive name collisions are rejected. A fixture must remain unchanged while it is copied; detected type, identity, or size changes fail setup. These checks do not make a concurrent filesystem snapshot atomic.

## Cleanup, evidence, and retention

Playtestr first stops and confirms the target process tree, captures failure evidence outside the workspace, and only then removes workspace files. Cleanup verifies the exact temporary parent, generated name, ordinary-directory type, and a random ownership marker immediately before bounded recursive removal. It never follows links created by the target. If target exit cannot be confirmed, the workspace is retained rather than deleting beneath a possibly running process.

Use `--keep-workspace-on-failure` to retain a failed or cancelled v2 workspace for local inspection. The path is printed and recorded in report v2. Successful runs are always removed. Retained directories may contain target data; Playtestr does not upload them or sweep them later. Remove an inspected path yourself only after confirming the target is stopped and the path is the exact one printed by the run.

Setup and cleanup have distinct `workspace_setup_failure` and `workspace_cleanup_failure` categories. A cleanup failure retains the directory and prevents staged snapshot updates from being committed. Existing screen and diff artifacts live outside the workspace and survive normal cleanup.

A workspace is repeatable setup, not a sandbox. The trusted target still runs with the user's permissions and can access other files, the network, registries, or services. External accounts and databases require their own explicit test lifecycle.

See [specification version 2](spec-v2.md), [machine report version 2](report-v2.md), and the runnable [`examples/workspace.json`](../examples/workspace.json).
