# MVP delivery plan

## Working agreement

Develop one observable behavior at a time. State the intended outcome, implement a small change, run relevant success and failure checks, then provide a manual demo command and result. Stop at the sprint boundary for user testing and feedback unless the user asks to continue. Keep unrelated enhancements in the backlog. A sprint is an acceptance milestone, not a fixed calendar estimate or a large batch of code.

Tests that exercise process behavior should use real PTYs and deterministic fixtures. Unit tests cover parsing and pure screen transformations. Do not substitute mocks for proof of PTY lifecycle behavior. Never describe a configured CI matrix as a passing matrix until it has actually run.

## MVP promise

A developer can run a trusted interactive CLI, drive its keyboard flow, assert the rendered screen and expected exit status, compare a reviewed text snapshot, and receive a useful failure artifact and nonzero runner exit status. The test completes within its budgets and cleans up the processes it launched on supported platforms.

Out of scope: cloud accounts, billing, PR bots, autonomous agents, game mechanics, browser/desktop game testing, styled visual regression, GIF recording, parallel scheduling, and multiple SDKs.

## Sprint 0 — baseline and decisions (current)

- Connect this folder to the new GitHub repository.
- Select the implementation language and record the tradeoffs.
- Preserve the existing interactive menu and six-step spec as the baseline.
- Verify the baseline build, unit tests, and menu snapshot locally.

Acceptance: `go run ./cmd/playtestr test examples/menu.json` passes against the built demo. Windows was previously exercised through ConPTY. Linux/macOS execution and remote CI are still unverified. Current code is a prototype, not the complete MVP.

## Sprint 1 — correct process outcomes (next)

User-visible result: a CLI that exits unexpectedly cannot be mistaken for a passing test.

Add an explicit expected-exit step, preserve process status while draining output, and distinguish a process failure from a missing-text timeout. Keep the implementation focused on these outcomes.

Acceptance: fixtures for exit 0, exit nonzero, text followed by a crash, and waiting for an exit that never happens. Retain the existing menu test. Each failure must return a nonzero runner status with the failing step and reason. Settle how an intentionally nonzero expected exit interacts with assertions before implementation.

## Sprint 2 — bounded sessions and cleanup

User-visible result: a silent, hung, or output-flooding target ends predictably and leaves no launched target tree behind.

Add startup/run/output limits and cancellation handling. Separate session lifetime from assertion orchestration where needed. Implement platform-specific cleanup and report failure to confirm cleanup. Make working-directory and environment inheritance explicit.

Acceptance: natural exit, forced shutdown, no output, output flood, interruption, and a child-process fixture. Use bounded repeated sessions to check for lingering processes and handles. Publish platform limitations uncovered by these checks.

## Sprint 3 — useful screen regressions

User-visible result: an intentional UI regression produces a readable expected/actual text diff.

Add text diffs and focused terminal compatibility fixtures. Cover redraws, escape sequences split across reads, Unicode, alternate screen behavior, then a resize action in its own small increment. Make snapshot readiness explicit; output quietness alone is insufficient. Introduce configurable volatile text only if the fixtures require it.

Acceptance: clean baseline passes, changed menu fails with the correct diff, explicit update changes only the selected baseline, and unsupported terminal behavior is documented. Evaluate the emulator against these fixtures before expanding its use.

## Sprint 4 — MVP packaging and external trial

User-visible result: another developer can install a release binary and test an actual CLI from its README instructions.

Version the spec and machine-readable report, include target/viewport/step metadata and failure screens, exercise the GitHub Actions matrix, and trial an existing external TUI in addition to our fixtures. Choose the oldest Go version actually supported by the code and pinned dependencies before publishing installation instructions. Choose the project license before the first release.

Acceptance: recorded Linux/macOS/Windows CI results for advertised platforms, a deliberately failing CI example with downloadable evidence, and a successful user walkthrough. Unsupported platforms stay explicitly unsupported rather than being inferred from cross-compilation.

## After the MVP

Replay files and reproduction, exact-failure minimization, styled snapshots, recordings, reusable CI integration, optional exploration, and hosted reports. Prioritize these using feedback from real CLI authors.
