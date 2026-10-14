# Test specification version 1

Current-source named input also accepts `Home`, `End`, `PageUp`, and `PageDown`.
They send `ESC [ 1 ~`, `ESC [ 4 ~`, `ESC [ 5 ~`, and `ESC [ 6 ~`, respectively.
Live recording recognizes these sequences and the common CSI/SS3 Home/End
variants; a Windows operator console translates the corresponding native keys.
This adds key names without changing existing spec versions or key encodings.

Current-source named input accepts every letter control from `CtrlA` through
`CtrlZ`, encoded as ASCII bytes `0x01` through `0x1a`, plus `CtrlSpace` (`0x00`).
`CtrlJ` is LF; `CtrlM` and `Enter` are CR. Existing navigation/key names and
bytes remain unchanged. This compatible enum expansion also applies to spec v2;
older published runners may reject names outside their documented subset.
The target's terminal mode and reader define the resulting action, including
signal handling and Windows console readers that treat Ctrl+Z as EOF.

Every Playtestr test is one UTF-8 JSON object with a required `"version": 1`. The canonical JSON Schema is [`schema/playtestr-spec-v1.schema.json`](../schema/playtestr-spec-v1.schema.json). Playtestr rejects a missing version, an unsupported version, unknown fields, files larger than 1 MB, and specs with more than 1,000 steps before launching the target.

`command` contains the executable and arguments. Playtestr executes it directly, without a shell. `cwd` is resolved from the spec file when relative. The target receives Playtestr's small operational environment, values declared in `env`, and host values explicitly named by `inherit_env`. Reports do not include command arguments, environment names, environment values, input text, or expected text.

`TERM` defaults to `xterm-256color` without implicitly inheriting the host's
terminal profile. Explicit inheritance overrides the default, and an explicit
literal value overrides inheritance. This also applies to v2 and recording.
Current source corrects older runners that silently overwrote a declared
`TERM`. To retain that earlier forced value, declare `xterm-256color` explicitly.
This is an environment-precedence repair under the existing literal-value
contract, not a new terminal protocol capability.

The viewport defaults to 80 columns by 24 rows. `timeout_ms` defaults to 3,000, `run_timeout_ms` to 30,000, and `max_output_bytes` to 2,000,000. `startup_timeout_ms` is disabled when omitted or zero. Dimensions, time budgets, output, snapshots, diffs, artifacts, staged snapshot updates, and cleanup waits are bounded by the runner.

Each step has exactly one action: `key`, `text`, `expect`, `expect_not`, `wait_for_redraw`, `snapshot`, `exit`, or `resize`. An `exit` action requires the exact process exit code. `expect_not` waits for previously observed text to leave the rendered screen: the same text must appear in an earlier `expect`, with input or resize between the two assertions. This prevents an absence check from passing before the application reaches the state being tested. `{"wait_for_redraw": true}` must immediately follow `resize`; it requires target output after that resize and allows a one-second redraw window before subsequent input is sent. The bounded window also works for targets that repaint continuously and never become output-quiet. It is synchronization evidence rather than a content assertion, so a snapshot still requires a later `expect` or `expect_not`. A snapshot needs positive readiness evidence from an `expect` or `expect_not` after the latest input or resize, or from an `exit` assertion. A spec can reference at most 100 distinct snapshots.

Snapshots contain the normalized rendered screen. Line endings are converted to LF, trailing spaces and unused rows are removed, and the file ends in one newline. This keeps checked-in snapshots stable across hosts. Styles and colors are outside the version 1 contract.

Version 1 is frozen for backward-compatible additions only. A change that alters existing meaning requires a new spec version and migration notes.

Version 1 remains the non-workspace contract. Tests that need a bounded fresh fixture copy can explicitly migrate to [specification version 2](spec-v2.md); the runner never changes v1 path or environment behavior implicitly.

## Migrating an unversioned prototype spec

Add `"version": 1` as a top-level field. The Sprint 3 prototype fields otherwise retain their meaning. Run the spec once without `--update`, then review any failure evidence before changing a baseline. Unsupported nonzero versions require a runner that explicitly supports that version; Playtestr does not guess or silently downgrade them.
