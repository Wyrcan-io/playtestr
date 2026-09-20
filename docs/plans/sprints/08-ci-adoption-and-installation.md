# Sprint 8 — Install the chosen release with less effort

Status: engineering implemented locally on 18 September 2026. The selected
route is the setup-only GitHub Action owned by the Playtestr repository
maintainers. Publication, three-host public-action execution, a later real
release upgrade, and independent adoption remain explicitly open; maintainer
adoption/outside feedback is deferred until A1, after the complete engineering batch and R6 by product decision.
See the [engineering record](../../validation/sprint-8-engineering-2026-09-18.md)
and [installation contract](../../ci-installation.md).

Engineering/native/publication follow-up now runs through [Sprint 13](13-native-ci-and-release-hardening.md) and [R6](../release/06-qualified-release.md). Independent adopter portions below are deferred to [A1](../release/07-maintainer-adoption.md) and do not gate engineering.

## User result and entry case

A maintainer chooses an exact Playtestr release and installs it using one
documented route, with the expected binary available to the next test command.

Record two setup-friction observations, or one blocked participant whose
platform/CI requirements identify the needed route. Existing direct archive
installation remains a valid fallback. Scope follows where users actually work.

## Choose one delivery route

Choose a setup-only GitHub Action when repeated CI jobs need verified downloads.
Choose one package channel when local installation is the demonstrated obstacle.
Do not ship both routes in this milestone. Record the maintenance owner and
how future releases update that route.

The route only installs Playtestr. Target installation, test execution,
baseline review, and artifact upload remain ordinary explicit workflow steps.
No caching layer, self-update, hosted upload, or repository write permissions
are needed for the first implementation.

## Installation contract

- Require an exact version for CI. Pin the installer/action independently of
  the runner version. Use only commands available in that runner release.
- Verify the exact supported OS/architecture mapping from published assets.
- Bound downloads, retries, and archive size; keep TLS verification enabled.
- Verify the published checksum and archive members before exposing the binary.
  A same-origin checksum is integrity evidence, not an independent signature.
- Extract into a fresh owned directory and invoke the absolute binary for its
  version check. Validate the next step resolves that version even if another
  Playtestr is already on PATH.
- Handle spaced paths and executable permissions natively. Avoid elevation or
  persistent machine-wide changes for a CI job.
- Failure must leave no partially installed binary presented as ready.
- Package metadata must have a named update process. If upgrade/uninstall is
  in scope, prove it touches only owned files.

Use the smallest implementation consistent with supported hosts. A setup action
may use platform shell scripts; it must call the released Go runner and does not
introduce a second runner implementation.

## Checkpoints

### 8.1 — Select the route

Capture installation attempts, prerequisites, time, assistance, and concrete
errors. Choose action or package channel, version policy, ownership, asset
mapping, and limits.

Acceptance: one route removes the identified work and has a maintenance owner.

### 8.2 — Implement and verify installation

Run fresh native checks for the promised targets. Cover a normal install,
missing release, wrong checksum, corrupt or escaping archive, unsupported
architecture, network timeout, spaced paths, and stale executable on PATH.

Acceptance: only the expected verified version becomes available. A configured
workflow alone is not execution evidence.

### 8.3 — Finish the actual adopter workflow

For engineering, have the operator use the route to run a known-good test, reject a controlled
regression, find the existing evidence, and recover. In CI, use finite artifact
retention, explicit artifact paths, and minimal permissions. Ordinary failures
must remain failed; do not teach blanket continue-on-error.

Acceptance: setup and assertions are distinguished, and the maintainer can
change the version pin without rebuilding the integration.

### 8.4 — Prepare publication and maintenance

Prepare exact metadata, instructions, and any external submission for review.
Publication, upstream PRs, and contacting recipients need their existing
explicit authority; a planning edit cannot claim they happened.

Acceptance: local preparation, actual publication, and independent adoption
are recorded separately. Verify a later real release upgrade when available;
do not publish dummy versions for the test.

## Definition of done

- [x] One route and its owner selected from an observed obstacle.
- [x] Fresh Windows amd64 installation and failure checks recorded; Linux/macOS public-action runs remain open and are not inferred from workflow configuration.
- [x] Correct released binary runs the adopter's pass/failure/recovery flow on the locally available Windows amd64 host.
- [x] Version selection, fallback, maintenance, and applicable removal documented.
- [x] Uncompleted publication or adoption steps remain explicitly open.

Review the next task on its own evidence. Installation does not determine the
order of workspace or terminal compatibility work.
