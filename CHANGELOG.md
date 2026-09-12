# Changelog

All notable user-visible changes are recorded here. Playtestr is pre-1.0; the
compatibility rules for released specs, reports, and patches are in
[`SUPPORT.md`](SUPPORT.md).

## Unreleased documentation

- Build a complete static website with dedicated installation, authoring,
  snapshots, troubleshooting, compatibility, examples, releases, support, and
  project-trial pages.
- Add a recorded interactive terminal example connecting authored steps to a
  passing rendered screen and an intentional snapshot-mismatch diff.
- Add direct stable-download choices, documentation search, social-preview
  metadata, mobile layouts, accessibility behavior, and build/link checks.

These presentation changes do not alter the runner, specification v1, report
v1, release assets, supported targets, or existing compatibility claims.

## v0.1.0

First stable release of the standalone Playtestr runner.

### Added

- Versioned JSON test specification v1 and machine report v1.
- Real-PTY execution on Linux amd64, macOS arm64, and Windows amd64.
- Text and key input, rendered-screen assertions, exact exit assertions,
  resize/redraw synchronization, and reviewed text snapshots.
- Bounded step and run time, raw-output limits, signal cancellation, managed
  process-tree cleanup, and atomic bounded evidence/report writes.
- Single-baseline updates with all-or-nothing commit and rollback behavior.
- Native release archives with license, dependency notices, and SHA-256 files.

### Fixed since v0.1.0-rc.1

- Unix targets receive the PTY slave as their controlling terminal, including
  applications that open `/dev/tty` directly.
- `expect_not` requires prior positive observation and a later interaction.
- `wait_for_redraw` provides a bounded post-resize synchronization point.
- Failure screens are captured before cleanup restores an alternate screen.

### Compatibility and migration

- v0.1.0 accepts spec version 1 and emits report version 1.
- Specs written for rc.1 or rc.2 remain valid. Prototype specs without a
  `version` field must add top-level `"version": 1`.
- The report does not include command arguments, environment data, typed text,
  expected text, or embedded terminal screens.

### Known limitations

- Styled snapshots and precise grapheme, emoji, combining-mark, and East Asian
  wide-character cell layout are outside the v1 contract.
- A very early Windows descendant can escape before Job Object attachment;
  Unix descendants can deliberately detach into another session.
- Playtestr runs targets with the user's permissions and is not a sandbox.
