# Troubleshooting Playtestr

Start with the runner exit status, failed step, failure category, and final rendered screen. Do not update a snapshot merely to turn a failure green.

| Result | Meaning | First useful check |
| --- | --- | --- |
| `invalid_spec` | The test does not satisfy spec v1 | Read the reported field/path and compare it with [spec v1](spec-v1.md) |
| `launch_failure` | The target could not start | Check the executable, `cwd`, target runtime, and selected environment |
| `assertion_timeout` | Expected screen text did not appear in time | Inspect the final screen and confirm the expected text identifies the new state |
| `unexpected_exit` | The target exited before the required result, or without an exit assertion | Check target output and add the exact `exit` step for a finite command |
| `exit_mismatch` | The observed exit code differs from the declared code | Reproduce the target manually and decide which code is correct |
| `snapshot_mismatch` | Rendered text differs from the reviewed baseline | Read both the actual screen and unified diff before changing the baseline |
| `output_limit` | Raw PTY output exceeded `max_output_bytes` | Check for a repaint loop or unintended log flood before changing the limit |
| `run_timeout` | The complete test exceeded its budget | Identify the stalled step or cleanup path; do not hide a hang with an unbounded wait |
| `cancelled` | The user or parent context cancelled the run | Confirm exit 130 and the report's cleanup evidence |
| `cleanup_failure` | Playtestr could not confirm managed process cleanup | Treat it as a correctness issue and preserve a sanitized reproduction |
| `artifact_failure` or report write failure | Evidence/report output could not be written | Check destination type, permissions, path, and available space |

## A target never appears

Run the target command manually from the same directory. Playtestr executes the command directly, so shell aliases, pipelines, redirection, and shell built-ins do not apply unless the command explicitly starts a shell. Confirm the architecture and runtime required by the target separately from the Playtestr runner.

## An assertion sees the wrong screen

Inspect `<spec>.actual.txt`. Confirm the viewport size and starting state. Look for text carried over from an earlier screen, asynchronous redraws, environment-dependent output, or state written by a previous run. Use a positive `expect` after input or resize. Use `wait_for_redraw` only for the documented resize sequence.

## A pass leaves an old failure file

This is expected in v0.1.0. Adjacent `.actual.txt` and `.diff.txt` files are historical evidence; a later pass does not delete them. The latest exit status and requested machine report determine the current result.

## Before reporting a bug

Reduce the case to one trusted target and a small spec. Record `playtestr --version`, archive filename and checksum, OS/version/architecture, target version, exact exit status and category, and sanitized evidence. Remove credentials, command arguments, typed values, personal paths, and sensitive screen output. Follow [Support and compatibility](../SUPPORT.md) for public and private reporting routes.
