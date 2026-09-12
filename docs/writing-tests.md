# Writing a Playtestr test

Start with one user goal that can run repeatedly against synthetic or disposable local state. Run the target manually first and record its starting screen, meaningful inputs, resulting screen, and expected exit behavior.

## A complete finite test

```json
{
  "version": 1,
  "name": "choose the staging environment",
  "command": ["my-cli", "configure"],
  "width": 80,
  "height": 24,
  "timeout_ms": 3000,
  "run_timeout_ms": 30000,
  "max_output_bytes": 2000000,
  "steps": [
    {"expect": "Choose environment"},
    {"key": "ArrowDown"},
    {"expect": "> Staging"},
    {"key": "Enter"},
    {"expect": "Saved staging"},
    {"exit": 0}
  ]
}
```

`command` is an executable followed by arguments and runs directly without a shell. Executable lookup uses the launch environment documented in [spec v1](spec-v1.md). Use a shell explicitly in `command` only when the workflow itself needs shell behavior.

## Prove each new state

Use `expect` for text that positively identifies the screen you need. After sending input, choose text that appears in the new state instead of text left over from the previous screen.

`expect_not` proves that text seen by an earlier `expect` disappears after input or resize. It cannot pass from an initially absent string. This is useful for closing a modal without adding an arbitrary sleep.

Finite applications should end with `{"exit": 0}` or the exact expected nonzero code. A target that exits without an exit assertion fails, even if earlier screen assertions passed. A long-running TUI does not need an exit step; Playtestr performs bounded cleanup when its steps finish.

Supported named keys are `Enter`, `ArrowDown`, `ArrowUp`, `ArrowLeft`, `ArrowRight`, `Escape`, `Tab`, `Backspace`, and `CtrlC`. A `text` action sends literal text.

## Working directory and environment

When `cwd` is omitted, the target starts in the directory where Playtestr was invoked. A relative `cwd` is resolved from the spec file's directory.

Targets receive a small operational environment. Add literal values with `env`, and explicitly select additional host variables with `inherit_env`:

```json
{
  "version": 1,
  "cwd": "../fixture-project",
  "env": {"APP_MODE": "test"},
  "inherit_env": ["CI"]
}
```

Do not put credentials in a spec. Playtestr excludes configured environment values and typed text from its report, but a target can print sensitive values to its screen and therefore into failure evidence.

## Time and output limits

- `timeout_ms` limits each wait step and defaults to 3 seconds.
- `run_timeout_ms` limits the complete spec and defaults to 30 seconds.
- `max_output_bytes` counts raw PTY output and defaults to 2 MB.
- `startup_timeout_ms`, when set, requires visible target text within that interval.

Keep timeouts long enough for the documented environment, but investigate inconsistent readiness before increasing them. Every passing assertion needs positive screen or exit evidence.

## Resize and redraw

Resize with `{"resize": {"width": 100, "height": 30}}`. A following `{"wait_for_redraw": true}` requires output after the resize and provides a bounded redraw window. It must immediately follow the resize and does not replace a content assertion.

## Run and report

```text
playtestr test --report results.json path/to/test.json
```

A passing run exits 0. Test failures exit 1 and identify the failed step and category. Ctrl+C cancellation exits 130 after bounded cleanup. The complete public contract is [Test specification version 1](spec-v1.md).
