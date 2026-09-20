---
title: "Playtestr documentation"
description: "Install Playtestr, write deterministic CLI and TUI tests, review snapshots, diagnose failures, and read the version 1 contracts."
---

Playtestr drives trusted interactive terminal applications with authored keyboard input and checks their rendered text. Start with the stable binary, prove one passing and one failing case, then adapt the small spec to your own application.

## Learn the workflow

1. [Install v0.1.0 and run a first test](/playtestr/docs/installation/).
2. [Write a test for your CLI or TUI](/playtestr/docs/writing-tests/).
3. [Adapt a complete real-application recipe](/playtestr/docs/recipes/).
4. [Add a reviewed text snapshot](/playtestr/docs/snapshots/) when a complete screen is useful.
5. [Diagnose failures](/playtestr/docs/troubleshooting/) by category, failed step, screen, and diff.
6. [Reproduce a CI failure locally](/playtestr/docs/ci-failure-handoff/) from reviewed identities and ordinary rerun commands.
7. [Install an exact release in GitHub Actions](/playtestr/docs/ci-installation/) after the action revision is published.
8. [Use a repeatable workspace](/playtestr/docs/workspaces/) for a stateful local flow.

## Use the reference

- [Test specification v1](/playtestr/docs/spec-v1/) defines inputs, actions, defaults, and limits.
- [Machine report v1](/playtestr/docs/report-v1/) defines structured outcomes and evidence references.
- [Test specification v2](/playtestr/docs/spec-v2/) and [machine report v2](/playtestr/docs/report-v2/) define opt-in workspace execution and its outcomes.
- [Offline failure reports](/playtestr/docs/failure-reports/) explains safe, bounded HTML export and diagnosis.
- [CI installation](/playtestr/docs/ci-installation/) defines exact version selection, verification, fallback, removal, and maintenance.
- [Compatibility and evidence](/playtestr/docs/compatibility/) records exact supported downloads and terminal limits.

Stable v0.1.0 uses spec/report version 1. Workspace v2 describes the current development runner and is not part of that stable binary. Development plans are proposals until their behavior is implemented and evidenced.
