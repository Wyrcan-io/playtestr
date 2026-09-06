# MVP delivery plan

## Working agreement

Develop one observable behavior at a time. State the intended outcome, implement a small change, run relevant success and failure checks, then provide a manual demo command and result. Stop at the sprint boundary for user testing and feedback unless the user asks to continue. Keep unrelated enhancements in the backlog. A sprint is an acceptance milestone, not a fixed calendar estimate or a large batch of code.

Tests that exercise process behavior should use real PTYs and deterministic fixtures. Unit tests cover parsing and pure screen transformations. Do not substitute mocks for proof of PTY lifecycle behavior. Never describe a configured CI matrix as a passing matrix until it has actually run.

## MVP promise

A developer can run a trusted interactive CLI, drive its keyboard flow, assert the rendered screen and expected exit status, compare a reviewed text snapshot, and receive a useful failure artifact and nonzero runner exit status. The test completes within its budgets and cleans up the processes it launched on supported platforms.

Out of scope: cloud accounts, billing, PR bots, autonomous agents, game mechanics, browser/desktop game testing, styled visual regression, GIF recording, parallel scheduling, and multiple SDKs.

## Sprint 0 — baseline and decisions (implemented locally)

- Connect this folder to the new GitHub repository.
- Select the implementation language and record the tradeoffs.
- Preserve the existing interactive menu and six-step spec as the baseline.
- Verify the baseline build, unit tests, and menu snapshot locally.

Acceptance: `go run ./cmd/playtestr test examples/menu.json` passes against the built demo. Windows was previously exercised through ConPTY. Linux/macOS execution and remote CI are still unverified. Current code is a prototype, not the complete MVP.

## Sprint 1 — correct process outcomes (implemented locally)

User-visible result: a CLI that exits unexpectedly cannot be mistaken for a passing test.

An explicit expected-exit step preserves process status and distinguishes a process failure from a missing-text timeout. An intentionally nonzero exit passes only when that exact code is declared. A process already observed to exit without an exit assertion fails; finite commands should end their specs with an exit assertion.

Acceptance: fixtures for exit 0, exit nonzero, text followed by a crash, and waiting for an exit that never happens. Retain the existing menu test. Each failure must return a nonzero runner status with the failing step and reason. Settle how an intentionally nonzero expected exit interacts with assertions before implementation.

## Sprint 2 — bounded sessions and cleanup (implemented locally)

User-visible result: a silent, hung, or output-flooding target ends predictably and leaves no launched target tree behind.

The terminal session now owns PTY I/O, process outcome, VT state, bounded final-output draining, output accounting, and idempotent cleanup. Specs support per-step, total-run, optional visible-startup, and raw-output limits. Ctrl+C cancellation stops the active spec and prevents later specs from starting.

Windows cleanup uses a Job Object and Unix cleanup uses a dedicated process group. Windows attachment happens immediately after xpty starts the target because the dependency does not expose a suspended-start hook; a child created in that narrow interval can escape the job. Unix children that deliberately create a new session can escape the original group. These are documented trusted-target boundaries.

`cwd`, `env`, and `inherit_env` make target launch configuration explicit. Relative working directories resolve from the spec directory. Ambient inheritance is restricted to an operational platform allowlist plus names selected by the spec.

Acceptance evidence: real-PTY tests cover natural exit, forced shutdown, no output, output flood, cancellation, blocked input, parent/child cleanup after a parent hang and natural parent exit, idempotent stop, environment filtering, working-directory resolution, and five bounded repeated sessions. Windows has been exercised locally; remote Linux and macOS execution remains unverified.

## Sprint 3 — useful screen regressions (implemented locally)

User-visible result: an intentional UI regression produces a readable expected/actual text diff.

Snapshot mismatches now print a bounded unified text diff and save expected/actual diff evidence alongside the captured screen. Baseline reads, diff output, and artifacts are bounded. Snapshot updates are staged until the spec and cleanup succeed; a selector can update one named baseline while all other snapshots continue to compare.

Snapshot readiness is explicit: an `expect` must succeed after the latest input or resize, or an exit assertion must succeed, before a snapshot can run. The existing quiet period settles a completed redraw but is not treated as readiness evidence.

Focused fixtures cover delayed redraw settling, carriage-return redraws, cursor movement and erasing, escape sequences split across writes, UTF-8 characters split across reads, basic Unicode text, alternate-screen entry and restoration, and PTY plus emulator resize. Playtestr buffers incomplete UTF-8 at its emulator boundary because vt10x otherwise drops a split code point.

Acceptance evidence: clean baselines pass; changed, added, and removed lines produce a readable diff; mismatch artifacts use the same captured screen; missing and oversized baselines fail distinctly; cancellation and later assertion failure do not commit staged updates; explicit update changes only the selected baseline; targets observe both larger and smaller viewport sizes. The emulator evaluation and unsupported behavior are documented in `docs/terminal-compatibility.md`.

## Sprint 4 — MVP packaging and external trial (implemented locally)

User-visible result: another developer can install a release binary and test an actual CLI from its README instructions.

Version the spec and machine-readable report, include target/viewport/step metadata and failure screens, exercise the GitHub Actions matrix, and trial an existing external TUI in addition to our fixtures. Choose the oldest Go version actually supported by the code and pinned dependencies before publishing installation instructions. Choose the project license before the first release.

Acceptance: recorded Linux/macOS/Windows CI results for advertised platforms, a deliberately failing CI example with downloadable evidence, and a successful user walkthrough. Unsupported platforms stay explicitly unsupported rather than being inferred from cross-compilation.

Implemented: required spec version 1 and canonical JSON Schema; structured runner outcomes; atomic machine report version 1 and schema; bounded transactional snapshot updates; an external Charm Gum `v0.17.0` trial; Go 1.25 minimum-version verification; Apache 2.0 licensing; version injection; native ZIP/tar.gz packaging with SHA-256 files; and a release-candidate workflow for Linux amd64, macOS arm64, and Windows amd64. The Windows packaged-binary walkthrough, full test suite, vet, race detector, expected-failure evidence, external trial, and checksum verification pass locally.

Remote status at implementation time: the prior commit passed Windows and macOS, while Ubuntu exposed an echoed-input flaw in `TestBlockedInputHonorsContext`. The fixture now disables terminal echo and passes repeatedly locally. The updated matrix and release-candidate workflow must run on the published Sprint 4 commit before those three release targets are advertised as verified.

## After the MVP

Replay files and reproduction, exact-failure minimization, styled snapshots, recordings, reusable CI integration, optional exploration, and hosted reports. Prioritize these using feedback from real CLI authors.
