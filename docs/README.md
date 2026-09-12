# Playtestr documentation

Playtestr is a local runner for deterministic end-to-end tests of trusted interactive CLIs and TUIs. Stable `v0.1.0` accepts test specification version 1 and emits machine report version 1.

## Start here

1. [Install the stable binary and run a first test](releases/v0.1.0-installation-walkthrough.md).
2. [Write a test for your own application](writing-tests.md).
3. [Add and review text snapshots](snapshots.md) when a complete rendered screen is useful.
4. [Diagnose a failure](troubleshooting.md) using its category, failed step, final screen, and diff.

## Reference

- [Test specification version 1](spec-v1.md) defines every input field, action, default, and limit.
- [Machine report version 1](report-v1.md) defines structured outcomes and evidence references.
- [Platform support](platform-support.md) records exact release targets and native evidence.
- [Terminal compatibility](terminal-compatibility.md) records rendered-screen behavior and known limits.
- [Support and compatibility policy](../SUPPORT.md) explains stable-contract and reporting expectations.

## Examples and help

- [`examples/menu.json`](../examples/menu.json) drives the repository's small interactive demo.
- [`examples/snapshot-mismatch.json`](../examples/snapshot-mismatch.json) is deliberately different from the reviewed baseline and should fail.
- [Troubleshooting](troubleshooting.md) maps common results to the next useful check.
- [Support](../SUPPORT.md) links the bug and private security-report routes.
- [Project trials](trials/README.md) are optional and intended for maintainers testing one real, repeatable workflow.

Development plans describe possible future work and are not released functionality. Contributors can start with [Development and repository checks](development.md).
