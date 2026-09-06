# Test specification version 1

Every Playtestr test is one UTF-8 JSON object with a required `"version": 1`. The canonical JSON Schema is [`schema/playtestr-spec-v1.schema.json`](../schema/playtestr-spec-v1.schema.json). Playtestr rejects a missing version, an unsupported version, unknown fields, files larger than 1 MB, and specs with more than 1,000 steps before launching the target.

`command` contains the executable and arguments. Playtestr executes it directly, without a shell. `cwd` is resolved from the spec file when relative. The target receives Playtestr's small operational environment, values declared in `env`, and host values explicitly named by `inherit_env`. Reports do not include command arguments, environment names, environment values, input text, or expected text.

The viewport defaults to 80 columns by 24 rows. `timeout_ms` defaults to 3,000, `run_timeout_ms` to 30,000, and `max_output_bytes` to 2,000,000. `startup_timeout_ms` is disabled when omitted or zero. Dimensions, time budgets, output, snapshots, diffs, artifacts, staged snapshot updates, and cleanup waits are bounded by the runner.

Each step has exactly one action: `key`, `text`, `expect`, `snapshot`, `exit`, or `resize`. An `exit` action requires the exact process exit code. A snapshot needs positive readiness evidence from an `expect` after the latest input or resize, or from an `exit` assertion. A spec can reference at most 100 distinct snapshots.

Snapshots contain the normalized rendered screen. Line endings are converted to LF, trailing spaces and unused rows are removed, and the file ends in one newline. This keeps checked-in snapshots stable across hosts. Styles and colors are outside the version 1 contract.

Version 1 is frozen for backward-compatible additions only. A change that alters existing meaning requires a new spec version and migration notes.

## Migrating an unversioned prototype spec

Add `"version": 1` as a top-level field. The Sprint 3 prototype fields otherwise retain their meaning. Run the spec once without `--update`, then review any failure evidence before changing a baseline. Unsupported nonzero versions require a runner that explicitly supports that version; Playtestr does not guess or silently downgrade them.
