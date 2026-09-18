# Machine report version 2

When a selected result uses spec v2, `playtestr test --report` writes machine report version 2. Mixed v1/v2 suites also use report v2; each result retains its own `spec_version`. Suites containing only v1 specs continue to write the unchanged [report v1](report-v1.md).

The canonical JSON Schema is [`schema/playtestr-report-v2.schema.json`](../schema/playtestr-report-v2.schema.json). Report v2 retains all v1 fields and adds optional per-result `workspace` metadata plus `workspace_setup_failure` and `workspace_cleanup_failure` categories.

Workspace metadata records whether preparation was attempted and completed, the declared fixture path, whether cleanup was attempted and completed, whether the directory was retained, its local retained path, and separate setup/cleanup failures. It does not embed fixture contents, environment values, command arguments, terminal input, or screen text.

A test assertion can remain the primary `failure` while `workspace.cleanup_failure` records a second cleanup problem. Cleanup failure prevents an otherwise successful result and retains the workspace. `retained_path` is present exactly when `retained` is true. Consumers must branch on `report_version` before interpreting these fields.

`playtestr report` accepts report versions 1 and 2 and renders workspace preparation, cleanup, retention, and failure status without reading the test spec or launching a target. The same evidence-root, resource, privacy, and atomic-output rules apply.
