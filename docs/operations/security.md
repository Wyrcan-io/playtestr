# Running arbitrary terminal targets safely

Playtestr launches programs supplied by the user. A future service must treat every target as untrusted code.

Minimum controls before hosted execution:

- run as a low-privilege account or inside a disposable container;
- restrict the working directory to a temporary target workspace;
- allowlist environment variables and never inherit secrets;
- impose CPU, memory, output, process-count, wall-clock, and filesystem limits;
- default network access to disabled;
- capture stdout/stderr through bounded channels;
- kill the complete process tree on timeout;
- retain artifacts with an explicit retention policy;
- record runner version and platform metadata for reproducibility.

The local CLI may launch a target with the user’s permissions, but its documentation must make that trust boundary explicit.
