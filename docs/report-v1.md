# Machine report version 1

`playtestr test --report results.json spec.json [...]` writes a JSON report atomically after every requested spec has passed, failed, or been marked `not_run`. The report is also written after Ctrl+C; the active result is `cancelled`, later paths are `not_run`, and the process exits with status 130.

The canonical JSON Schema is [`schema/playtestr-report-v1.schema.json`](../schema/playtestr-report-v1.schema.json).

The top level contains `report_version`, `runner_version`, `os`, `arch`, `summary`, and the ordered `results` array. Each result records the spec version and path, initial viewport and successful resizes, per-step action/status/duration, target exit status when known, primary failure, cleanup outcome, and paths to screen or diff evidence. Cleanup and evidence-write failures remain separate from the primary test failure.

Failure categories in version 1 are `invalid_spec`, `launch_failure`, `assertion_timeout`, `run_timeout`, `unexpected_exit`, `snapshot_mismatch`, `output_limit`, `cancelled`, `cleanup_failure`, `artifact_failure`, `snapshot_update_failure`, and `internal_error`.

Reports are limited to 8 MB. They omit command arguments, environment data, typed input, expected text, and embedded terminal screens. Evidence remains in bounded files referenced by the report. Consumers should branch on version, status, and category fields rather than parsing human-readable messages.
