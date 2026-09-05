# Learning from gametestr

Source reviewed: https://github.com/Wyrcan-io/gametestr (local reference checkout, September 5, 2026). This was a source review; the TypeScript test suite and benchmark claims were not independently rerun.

The existing project already implements a general terminal-testing foundation beneath its game exploration features. The Go prototype is currently smaller and lacks several lifecycle and evidence features present there. Keep the TypeScript implementation as a behavioral reference during development.

## Reuse map

| Existing code | Application to Go TUI testing |
| --- | --- |
| `src/terminal.ts`, `src/backend.ts`, `src/process-tree.ts` | Separate terminal sessions from test orchestration; expose screen, cursor, dimensions, process status, output counts, resize, and cleanup results. |
| `src/manifest.ts` | Versioned target configuration, manifest-relative working directories, explicit environment configuration, startup and episode budgets. |
| `src/oracles.ts`, `src/findings.ts` | Distinguish a crash from an assertion timeout or output-budget violation; attach evidence to each result. |
| `src/observations.ts` | Configurable normalization for timestamps and other changing fields; preserve raw screens alongside normalized comparisons. |
| `src/replay.ts`, `src/artifacts.ts` | Versioned actions and terminal metadata, target identity, bounded artifacts, and atomic report writes. |
| `src/reproduce.ts`, `src/finding-minimize.ts`, `src/minimize.ts` | Replay a failure in a fresh process, then shorten the action sequence while preserving the same failure signature. |
| `src/professional-report.ts` | Human-readable reports derived from canonical evidence. |
| `fixtures/` | Regression scenarios for no output, hangs, crashes, output floods, Unicode, resizing, and child-process cleanup. |

## Product boundary

Keep gametestr focused on autonomous game exploration, mechanic evidence, hidden routes, and completion goals. Give playtestr a deterministic TUI workflow: launch, wait for a prompt, type or press a key, assert the visible state, compare a snapshot, and collect failure evidence.

The shared conceptual contract is a terminal session plus actions, observations, lifecycle results, and replay metadata. Since these projects currently use different languages, share documented behavior and fixture expectations first. Extracting a common runtime now would introduce an additional integration layer before the Go implementation has parity.

The existing repository still calls itself Playtestr in its README, package name, executable, and repository metadata. Clarify product naming before publishing either package. No remote files were changed during this review.

## Recommended implementation order

1. Separate the Go terminal session from the runner. Add process-exit assertions, startup/run/output budgets, and verified cleanup. Cover natural exit and forced shutdown with integration fixtures.
2. Define versioned specs and reports. Add explicit working-directory/environment behavior and replay evidence before the format gains users.
3. Add resize actions, configurable volatile-text normalization, and useful snapshot diffs. Preserve attributes in a separate styled-screen representation.
4. Add fresh-process reproduction and failure-preserving minimization.
5. Build demos around an interactive setup wizard, a full-screen menu with resize behavior, and a deliberately broken CLI with a replayable failure. Expand CI reporting afterward.

The game-specific agent roles, world model, and persistent campaigns can remain in gametestr. Optional bounded exploration for TUIs can follow once deterministic regression testing is reliable.
