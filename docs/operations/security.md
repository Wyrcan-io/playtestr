# Execution security

## Local PTY backend

The local backend is for trusted developer-owned targets. It must:

- inherit only a small operational environment allowlist plus explicitly requested names;
- avoid writing environment values into reports;
- enforce wall-clock and output budgets;
- classify cleanup failures;
- require explicit CLI trust acknowledgement;
- state that the target retains the caller's filesystem and network permissions.

These controls reduce accidents. They are not containment.

## Isolated backend release gate

Untrusted or hosted execution is forbidden until a disposable backend demonstrates:

- no ambient cloud, source-control, package-registry, or user credentials;
- unprivileged identity and a fresh worker per job;
- read-only target inputs and quota-limited writable scratch space;
- default-deny outbound and inbound networking;
- CPU, memory, process-count, file-size, disk, output, and wall-clock limits;
- complete process-tree termination and resource accounting;
- no host socket/device mounts or privileged mode;
- bounded artifact type, size, retention, and download policy;
- dependency/image provenance, patching, and audit logs;
- adversarial escape and denial-of-service tests.

Containers improve isolation and resource control but are not automatically sufficient. Backend choice and active capabilities must be recorded in every report.

## Secrets

Manifests opt into additional inherited variables by name. Reports may record names but never values. Provider credentials for future semantic agents remain in the supervisor process and are never passed to the target. External model calls require explicit redaction and retention policy.
