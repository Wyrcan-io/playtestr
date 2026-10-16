# Machine report version 3

Source candidate only. A suite containing spec v3 produces report v3; all-v1
and v1/v2 suites keep their existing formats. The
[schema](../schema/playtestr-report-v3.schema.json) retains report v2 fields and
adds `state_assertion_failure`, action `state`, optional result `invocation_id`,
workspace `id`, and step `state` metadata.

Each attempted state step records `path`, `kind`, `outcome` (`matched` or
`rejected`), `invocation_id`, and `workspace_id`. The identities bind checkpoints
to the freshly created workspace in this execution. They are random correlation
identifiers, not cryptographic attestations. A failed/skipped setup has no state
observation. Reports omit expected/observed file bytes and unselected names.

The offline HTML renderer accepts v3 and shows selected paths/outcomes/identities.
It rejects inconsistent state identities. Primary test failure and process or
workspace cleanup errors remain separate. Older renderers must refuse v3 rather
than reinterpret it as v2.
