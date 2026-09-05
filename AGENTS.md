# Playtestr repository instructions

## Purpose

Playtestr is a deterministic end-to-end testing tool for interactive command-line applications and terminal user interfaces. Its product position is "Playwright-style testing for the terminal."

The MVP promise is that a developer can launch a trusted interactive CLI in a real pseudoterminal, drive it with keyboard input, assert the rendered terminal screen and exit status, compare reviewed snapshots, and receive clear failure evidence with a nonzero runner exit status.

Read `README.md` for current usage, `docs/sprints.md` for delivery order, and `docs/language-decision.md` for the Go decision. Treat those documents as product context, while this file defines repository-wide working rules.

## Product boundary

- Keep Playtestr focused on deterministic CLI and TUI regression testing.
- Keep autonomous game exploration, mechanics, hidden-route discovery, and game-specific agents in Gametestr.
- The target application may use any language or TUI framework. Do not make the core depend on a target framework.
- Use Go for the MVP runner, CLI, fixtures, and local reports. Do not add another core implementation language without a measured need and an architecture decision.
- Keep the local runner usable as a standalone binary. Cloud services, billing, PR bots, and hosted dashboards are post-MVP work.
- Do not expand a sprint with unrelated roadmap items. Put useful ideas in the backlog and finish the current acceptance boundary first.

## Development workflow

Work in small, demonstrable increments:

1. State one user-visible behavior and its acceptance cases.
2. Implement the smallest coherent change that provides it.
3. Test success, expected failure, timeout, and cleanup paths relevant to that behavior.
4. Run the manual example when the change affects user-visible execution.
5. Update documentation in the same change when public behavior changes.
6. Stop at the sprint boundary for user testing and feedback unless the user asks to continue.

Do not produce large speculative implementations. Prefer a narrow vertical slice that a user can run over partially built architecture for several future features.

## Architecture boundaries

Maintain clear boundaries as the prototype is separated into packages:

- Spec parsing and validation define the versioned public test contract.
- Terminal sessions own PTY creation, VT parsing, input, resize, process observation, and cleanup.
- The runner owns step ordering, time budgets, assertions, and outcomes.
- Artifact writers serialize evidence; they do not decide whether a test passed.
- CLI code parses arguments, invokes the runner, and maps results to output and exit codes.

Keep PTY and terminal-emulator libraries behind internal interfaces so they can be evaluated or replaced without changing test files. Avoid exposing dependency-specific types in public contracts.

The terminal contract includes viewport dimensions, rendered screen text, cursor behavior, alternate-screen state, input encoding, process status, output limits, timing, and cleanup. Changes to these behaviors require integration coverage.

## Go practices

- Format changed Go files with `gofmt`.
- Return errors with useful operation context and preserve wrapped causes with `%w` where callers may inspect them.
- Bound goroutines, reads, waits, output, and artifact sizes. Every goroutine that can outlive a step needs an explicit shutdown path.
- Synchronize shared terminal and process state. Run the race detector after concurrency or lifecycle changes.
- Prefer the standard library when it is adequate. Add production dependencies only for a concrete requirement, and document why the dependency is appropriate.
- Keep exported APIs small and document exported identifiers. Avoid exporting prototype details before the contract is stable.
- Validate untrusted spec values before using them as paths, dimensions, durations, environment names, or action values.
- Keep platform-specific behavior in platform-specific files when Unix and Windows implementations diverge.
- Preserve errors from cleanup separately from the test failure that triggered cleanup.

## Testing expectations

- Use table-driven unit tests for parsing, validation, normalization, and other pure logic.
- Use real PTYs and deterministic helper processes for lifecycle behavior. Mocks do not prove interactive terminal behavior.
- Cover natural exit, expected nonzero exit, unexpected exit, assertion timeout, forced shutdown, output flood, Unicode, redraws, resize, and child-process cleanup as those features are implemented.
- A regression test should fail before its fix and exercise externally observable behavior.
- Keep tests bounded. Increase test-only deadlines when instrumentation is slower; do not weaken product deadlines to accommodate tests.
- Do not claim Linux, macOS, Windows, framework, or terminal compatibility unless that exact path has run successfully.
- Do not treat a configured CI workflow as evidence that CI passed.

Run the checks appropriate to the change:

```powershell
go test ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
go build -o bin/demo.exe ./cmd/demo
go run ./cmd/playtestr test examples/menu.json examples/menu-exit.json
```

The race script uses the ignored project-local compiler under `.tools`. On environments without that compiler, record the missing prerequisite rather than reporting a successful race check.

## Evidence and failure behavior

- Assertions inspect the rendered terminal state, not raw ANSI byte streams.
- A passing step must have positive evidence. Quiet output alone does not prove readiness or completion.
- Process exits, assertion mismatches, timeouts, output-limit violations, and cleanup failures are distinct outcomes.
- Preserve the most useful final screen when a run fails.
- Expected nonzero exits pass only when the spec declares the exact code.
- Future replay and report formats must be versioned and deterministic. Reports must derive from captured evidence and must not invent coverage claims.

## Security and process handling

- The local PTY backend runs targets with the user's permissions. It is not a sandbox; describe it only as suitable for explicitly trusted targets.
- Do not persist environment values or secrets in snapshots, reports, logs, or replay files.
- Move toward explicit environment inheritance. The prototype's ambient environment inheritance is a known gap, not a stable contract.
- Confirm process termination where the platform permits it. Killing only the direct child is insufficient proof of process-tree cleanup.
- Never claim isolation merely because a target ran in a subprocess, PTY, or container.

## Documentation and release discipline

- Keep `README.md` focused on installation, the first successful test, authoring tests, and current limitations.
- Record durable design decisions in `docs/`; keep transient implementation notes out of public contracts.
- When changing a public spec or artifact format, update validation, examples, tests, and migration notes together.
- Keep examples small enough that users can understand the tested interaction at a glance.
- Do not publish releases, push commits, or claim remote CI results unless the user explicitly requests that action and the evidence exists.

## Code review rules

- Flag any path where a target can exit, hang, flood output, or leave descendants without producing a bounded and accurate result.
- Flag shared state accessed without synchronization and goroutines without a clear termination path.
- Flag tests that validate only mocks for PTY, VT, or process-lifecycle behavior.
- Flag public compatibility, coverage, isolation, or security claims that exceed the evidence collected.
- Flag changes that mix Gametestr's autonomous game behavior into Playtestr's deterministic MVP core.
