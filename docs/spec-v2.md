# Test specification version 2

Specification version 2 adds a required repeatable `workspace` and otherwise preserves the version 1 actions, terminal semantics, defaults, and limits. Its canonical JSON Schema is [`schema/playtestr-spec-v2.schema.json`](../schema/playtestr-spec-v2.schema.json).

Required top-level fields are `version: 2`, a nonempty `command`, `workspace`, and nonempty `steps`. Optional `name`, `env`, `inherit_env`, viewport, timing, startup, and output-limit fields have the same meaning and bounds as [spec v1](spec-v1.md). Unknown fields are rejected. Top-level `cwd` is deliberately unavailable.

`workspace.fixture` is a nonempty relative path below the spec directory. `workspace.cwd` is relative to the copied fixture and defaults to `.`. `workspace.home` and `workspace.temp` each accept only `"temporary"` when present. Managed environment names cannot also appear in `env` or `inherit_env`.

Path containment, link/reparse rejection, copy limits, command resolution, exact environment mappings, lifecycle order, and retained-directory behavior are normative in [Repeatable workspaces](workspaces.md).

## Migrating from version 1

Keep a v1 spec when it intentionally uses the invocation directory or a stable external `cwd`; v1 remains supported and still emits report v1 when every selected spec is v1. To opt in:

1. Put only the required reviewed starting files in a directory below the spec directory.
2. Change `version` to `2` and remove top-level `cwd`.
3. Add `workspace.fixture`; move the old working-directory suffix to `workspace.cwd` if needed.
4. Select temporary home/temp only when the target writes there, and remove conflicting `env` or `inherit_env` entries.
5. Confirm executable paths: relative paths now resolve from the spec directory before the copied `cwd` is selected.
6. Run without snapshot update first and verify the source fixture and known personal-state sentinels remain unchanged.

Playtestr never guesses a workspace for a v1 spec and never downgrades a v2 spec.
