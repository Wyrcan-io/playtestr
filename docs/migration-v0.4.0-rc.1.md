# Migrating to or from v0.4.0-rc.1

Upgrade by installing the new version beside the old executable, verifying its
SHA-256, then changing PATH explicitly. Run an unchanged v1 pass, deliberate
failure, and recovery before migrating a stateful test. The qualification used
public `v0.3.0-rc.1` and the candidate this way and preserved the reviewed
baseline SHA-256
`96bbce2386a3ab5e113225d126bbedbd674e1bcc28f33c657c4d621604aa3eb4`.

To adopt workspaces, copy a reviewed fixture into a spec-v2 `workspace`; do not
retrofit a v1 spec in place if older runners must still execute it. V1-only
suites continue to produce report v1. A suite containing v2 produces report v2,
which an older strict reader may reject.

To downgrade, restore the previous executable and its PATH entry. Keep v1
specs and v1 reports as the interchange boundary. V2 specs cannot be safely
"downgraded" by changing the version number: remove workspace reliance only
after reviewing paths, environment, state isolation, and cleanup. Preserve
failure evidence and snapshots; never overwrite a published tag or baseline as
a rollback mechanism.

For setup-action source, inspect `action.yml`, `setup-playtestr/install.ps1`,
and the exact immutable action commit before use. The runner version pin and
action commit are independent identities. To remove it, delete the workflow
step and remove only the install directory added by that step after resolving
and checking its exact path. A failed install must not be treated as ready and
must not publish a PATH entry or successful outputs.
