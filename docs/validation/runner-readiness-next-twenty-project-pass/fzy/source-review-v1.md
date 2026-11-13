# fzy pinned source review v1

## Identity

- Project: `jhawthorn/fzy`
- Selected pin: `34b88869d022e861da4846c4463aea3ddfb3ff30`
- Language/runtime: native C99 executable; upstream Makefile links pthreads.
- Declared native hosts: Linux amd64 and macOS arm64.
- License in screening metadata: MIT; verify the pinned license file after
  source acquisition before executing build hooks.
- The pinned `LICENSE` file is MIT, blob `8039af7550c567bdfa4ac002fab7738e2386163c`.
- Primary sources reviewed at the exact selected commit:
  [README](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/README.md),
  [Makefile](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/Makefile),
  [options.c](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/src/options.c),
  [tty_interface.c](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/src/tty_interface.c),
  [choices.c](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/src/choices.c),
  and [test/test_choices.c](https://github.com/jhawthorn/fzy/blob/34b88869d022e861da4846c4463aea3ddfb3ff30/test/test_choices.c).

## User behavior and observable contract

The README describes fzy as a terminal fuzzy selector that can be inserted in a
pipeline. It reads candidates from stdin and opens `/dev/tty` for interactive
keyboard input by default. Enter closes/resets the terminal before writing the
selected candidate plus a newline to stdout and returns success. If no candidate
matches, Enter emits the typed query plus a newline and also returns success.
Escape, Ctrl-C, Ctrl-D and Ctrl-G exit with failure without emitting a selected
line. The tests must assert the emitted line and process result, not infer
selection from the highlighted row alone.

Useful documented controls include `--query`, `--lines`, `--prompt`,
`--show-matches`, `--show-scores`, `--read-null`, and `--show-info`. The upstream
Makefile's `test` target runs the native C suite, including 100,000 generated
property trials for matching positions and availability.

## Scope, safety, and initial risk map

The observed command has no persistent application state: its result is stdout.
The provisional selection declaration's `stateful_proposed` flag is not
evidence of saved-state behavior and must be corrected in the project contract.
The scenario shell adapter will redirect stdout to a harness-owned `result.txt`
capture. The runner checks its exact bytes in the same invocation after the
declared target exit, alongside positive rendered checkpoints. That file is an
output capture, not target-saved-state coverage. No assertion logic or
shell-produced expected value is part of the target oracle.

Planned case dimensions include query ranking and replacement, no-result
completion, each documented cancellation control, empty and NUL-delimited
inputs, CRLF data, UTF-8 candidate output, small viewport paging, list redraw,
score display, and option validation. NUL-delimited input carries no claim that
the selected C string itself may contain NUL. Wide-character rendering and
Unicode case folding remain unclaimed unless verified against the actual native
screen and emitted bytes.

This source review grants no build, scenario, native-cell, fault, route or
project admission credit. Recheck the actual downloaded archive, full source
tree, license and build scripts before running upstream build/test commands.
