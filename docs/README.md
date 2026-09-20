# Playtestr documentation

Playtestr is a local runner for deterministic end-to-end tests of trusted interactive CLIs and TUIs. Stable `v0.1.0` accepts test specification version 1 and emits machine report version 1.

## Start here

1. [Install the stable binary and run a first test](releases/v0.1.0-installation-walkthrough.md).
2. [Write a test for your own application](writing-tests.md).
3. [Adapt a complete real-application recipe](recipes/README.md).
4. [Add and review text snapshots](snapshots.md) when a complete rendered screen is useful.
5. [Diagnose a failure](troubleshooting.md) using its category, failed step, final screen, and diff.
6. [Run a deterministic suite](suites.md) and collect isolated CI evidence.
7. [Install an exact release in GitHub Actions](ci-installation.md) after the action revision is published.
8. [Use a repeatable workspace](workspaces.md) when a local stateful flow needs fresh reviewed files.

## Reference

- [Test specification version 1](spec-v1.md) defines every input field, action, default, and limit.
- [Machine report version 1](report-v1.md) defines structured outcomes and evidence references.
- [Test specification version 2](spec-v2.md) and [machine report version 2](report-v2.md) define the opt-in development workspace contract.
- [Offline failure reports](failure-reports.md) explains safe, bounded HTML export and diagnosis.
- [Test suites and CI evidence](suites.md) defines directory selection, summaries, limits, and artifact layout.
- [CI installation](ci-installation.md) defines exact version selection, verification, fallback, removal, and action maintenance.
- [Platform support](platform-support.md) records exact release targets and native evidence.
- [Terminal compatibility](terminal-compatibility.md) records rendered-screen behavior and known limits.
- [Support and compatibility policy](../SUPPORT.md) explains stable-contract and reporting expectations.

## Examples and help

- [`examples/menu.json`](../examples/menu.json) drives the repository's small interactive demo.
- [`examples/snapshot-mismatch.json`](../examples/snapshot-mismatch.json) is deliberately different from the reviewed baseline and should fail.
- [`examples/workspace.json`](../examples/workspace.json) runs a state-writing fixture from fresh project, home, and temp directories.
- [Troubleshooting](troubleshooting.md) maps common results to the next useful check.
- [Support](../SUPPORT.md) links the bug and private security-report routes.
- [Project trials](trials/README.md) are optional and intended for maintainers testing one real, repeatable workflow.
- [`v0.3.0-rc.1` release notes](releases/v0.3.0-rc.1.md) record the published offline-report binaries, hashes, and verification runs.

Development plans describe possible future work and are not released functionality. Contributors can start with [Development and repository checks](development.md).

## Product planning

- [Current delivery roadmap and completed releases](../roadmap.md).
- [Competitive and user-needs research](research/competitive-user-survey-2026-09-19.md).
- [Real-application validation program](plans/validation-program.md) and [120 proposed workflows](plans/corpus-catalog.md).
- [Maintainer adoption after engineering](plans/release/07-maintainer-adoption.md).
