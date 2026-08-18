# Playtestr implementation plan

Status: active implementation roadmap

Playtestr is a standalone product for autonomous black-box testing of terminal games. Gamr remains the game runtime and anthology. The repositories share concepts and optional adapters, but Playtestr core must not import Gamr.

## Product promise

Playtestr will find reproducible failures, unexplored interaction paths, and objective-specific gameplay evidence in terminal programs. It will not claim that a black-box agent has proven a game bug-free, discovered every secret, or measured fun without human calibration.

The product has four evidence levels:

1. **Observed** — a screen, process event, or action transition was recorded.
2. **Reproduced** — the same replay reaches the same observation or failure again.
3. **Confirmed** — an executable oracle or adapter invariant proves the finding.
4. **Human-reviewed** — a person judged the behavior, usability, balance, or fun.

Reports must distinguish these levels.

## Current baseline

Already implemented:

- separate `@wyrcan/playtestr` package and CLI;
- JSON target manifests;
- `node-pty` process sessions on Windows/Unix;
- `@xterm/headless` VT screen parsing;
- keyboard actions, timing, viewport resize, and replay records;
- baseline bounded exploration;
- crash, timeout, stall, and output findings;
- fixture target and PTY integration test;
- typecheck, Vitest, tsup build, CI skeleton, security/contributor guidance.

Current limitation: Windows `node-pty` can emit an `AttachConsole failed` diagnostic during ConPTY teardown even when the run succeeds. This is a release-blocking lifecycle issue to isolate and resolve, not suppress blindly.

## Non-goals for the first release

- training a general reinforcement-learning player;
- graphical game support;
- hosted execution of untrusted targets;
- an LLM dependency in core;
- claiming full game/mechanic coverage from screen novelty;
- migrating Gamr’s game-specific profiles wholesale.

## Architecture target

```text
manifest -> target launcher -> PTY session -> VT parser
                                      |
                         observation + stable fingerprint
                                      |
                 policy -> action -> runner budgets -> replay
                                      |
                     oracles + corpus + minimizer -> report
                                      |
                    optional adapter / optional LLM supervisor
```

### Package boundaries

```text
@wyrcan/gamr              built-in games and Gamr runtime
@wyrcan/playtestr         generic runner, agents, oracles, replay, CLI
@wyrcan/gamr-playtest     future optional adapter/profile package
```

### Source boundaries

- `src/types.ts` — public versioned contracts.
- `src/terminal.ts` — PTY process and VT lifecycle.
- `src/runner.ts` — episode orchestration, budgets, observation recording.
- `src/agents.ts` — bounded action policies.
- `src/oracles.ts` — executable failure checks.
- `src/observations.ts` — normalization and fingerprints.
- `src/corpus.ts` — interesting action-prefix storage.
- `src/minimize.ts` — replay reduction.
- `src/replay.ts` — serialization and replay compatibility.
- `fixtures/` — deterministic test targets.

## Milestone 0 — repository and contract hygiene

Goal: make the project safe to extend and easy for contributors or coding agents to understand.

Deliverables:

- root `AGENTS.md` and `.agents` guidance;
- architecture, security, contribution, and CI documentation;
- package scripts for typecheck, test, build, and fixture smoke;
- schema/version policy for observations, replays, reports, and findings;
- Node 22/24 CI on Linux, with Windows PTY validation added as soon as runner stability allows.

Acceptance:

- a new contributor can install, test, build, and run a fixture from the README;
- CI rejects type, test, or build regressions;
- arbitrary-target safety limitations are visible before execution.

## Milestone 1 — deterministic observation and corpus foundation

Goal: make exploration measurable instead of relying on raw text equality.

Deliverables:

- canonical screen normalization with explicit treatment of whitespace, cursor, viewport, and alternate buffer;
- exact and structural observation fingerprints;
- dynamic-region policy so clocks/animations do not create infinite false novelty;
- `ActionCorpus` with action prefixes, first-seen fingerprints, depth, and provenance;
- runner report metrics: unique states, novel transitions, and corpus size;
- tests proving equivalent frames hash together and meaningful changes do not.

Acceptance:

- the same seeded run produces stable structural fingerprints;
- a changing clock does not cause unbounded structural novelty;
- the fixture report exposes useful novelty metrics;
- corpus entries can be serialized without losing action timing.

## Milestone 2 — replay minimization and finding quality

Goal: turn a long failing run into a small issue-ready reproduction.

Deliverables:

- async delta-debugging over action sequences;
- retry policy to distinguish flaky failures from reproducible failures;
- minimization budgets and cancellation;
- report fields for original and minimized action counts;
- CLI command to minimize a report/replay against its manifest;
- fixture targets for crash, hang, invalid input, and lifecycle failure.

Acceptance:

- a known failure reduces to the shortest or near-shortest reproducing prefix;
- minimization never reports success without rerunning the oracle;
- flaky outcomes are reported as flaky, not confirmed;
- minimized replays are independently runnable.

## Milestone 3 — lifecycle and platform hardening

Goal: make external execution trustworthy across platforms.

Deliverables:

- complete process-tree cleanup on normal exit, timeout, crash, and Ctrl-C;
- bounded stdout/PTY output and explicit overflow findings;
- stderr capture where the platform supports it without corrupting the game screen;
- startup readiness and graceful-exit detection;
- resize tests, signal tests, repeated-launch tests, and raw PTY cleanup tests;
- Windows ConPTY diagnostic investigation and Linux/macOS PTY matrix validation.

Acceptance:

- 100 repeated fixture launches leave no target process behind;
- force-stopped targets do not poison the next run;
- output floods, hangs, and non-zero exits have distinct reports;
- the CLI exits with a stable status and no uncaught helper-process diagnostics.

## Milestone 4 — generic exploration and edge profiles

Goal: find more than the baseline key loop without game-specific code.

Deliverables:

- novelty-guided action selection;
- action-prefix mutation: repeat, delete, splice, replace, and timing jitter;
- edge profile for invalid keys, rapid input, holds, escape, backspace, resize, restart, pause, and quit;
- checkpoint/restart scheduling;
- per-profile budgets and deterministic random seeds;
- corpus retention and replay deduplication.

Acceptance:

- the explorer reaches more structural states than baseline on benchmark fixtures;
- every discovered crash or stall has a corpus prefix and replay;
- edge profiles do not escape target or artifact boundaries;
- time spent on one dynamic screen cannot starve the rest of the run.

## Milestone 5 — optional adapter protocol

Goal: give cooperative games much deeper coverage without making black-box mode dependent on instrumentation.

Adapter capabilities:

- reset(seed, options);
- semantic state snapshot and stable state hash;
- legal action vocabulary;
- event stream;
- goal predicates;
- invariant checks;
- checkpoint/restore;
- fast headless step path where available.

Acceptance:

- a game can run in black-box mode without an adapter;
- an adapter can improve coverage and oracle quality without changing replay semantics;
- Gamr adapters live outside Playtestr core and can evolve independently.

## Milestone 6 — objective agents

Goal: support speedrunning, hidden-feature, and player-style testing.

Profiles:

- `smoke`: startup, input, quit, restart, and basic interaction;
- `explore`: maximize stable observation/event novelty;
- `edge`: stress timing, invalid input, resize, and lifecycle boundaries;
- `complete`: reach declared goals across seeds;
- `speedrun`: minimize actions/time while preserving goal evidence;
- `secrets`: investigate optional routes and unusual transitions;
- `persona`: novice, cautious, curious, reckless, completionist, optimizer.

Acceptance:

- speedrun metrics are not mixed with exploration coverage;
- secret discoveries include evidence and reproduction status;
- persona results are distributions, not a claim of one human simulator;
- each profile has a budget, stop condition, and benchmark evaluation.

## Milestone 7 — semantic supervision

Goal: use an LLM where language interpretation helps, without giving it control of safety or truth.

The LLM may summarize screens, infer possible controls, propose goals, rank candidate actions, classify findings, and write reports. The runner must validate action schemas, enforce budgets, and rely on executable oracles for confirmation.

Requirements:

- provider interface with local/offline fallback;
- strict structured output;
- context compression and cost budgets;
- model decisions stored separately from canonical replay;
- hypothesis/evidence/confirmation labels;
- redaction of secrets and target data before external calls.

Acceptance:

- deterministic agents complete runs when the model is unavailable;
- model hallucinations cannot issue arbitrary shell commands;
- model-generated findings link to frames, actions, and reproduction attempts;
- usefulness is measured against benchmark fixtures and human review.

## Milestone 8 — CI and hosted product

Goal: make Playtestr useful in a development workflow.

Deliverables:

- `playtestr check` for CI-friendly pass/fail policies;
- artifact upload and retention guidance;
- baseline report comparison;
- GitHub Actions integration;
- package release process and changelog;
- hosted jobs only after disposable sandboxing, resource limits, network policy, and secret isolation are implemented.

## Benchmark suite

Maintain small deterministic fixtures before relying on real games:

1. menu/navigation game;
2. text-entry and Unicode game;
3. turn-based state machine;
4. real-time timer game;
5. hidden-route game;
6. crash-on-sequence game;
7. hang/no-progress game;
8. output-flood game;
9. resize/lifecycle game;
10. one Gamr adapter integration.

Each fixture should declare the bug or objective it represents and provide a human-readable expected result.

## Success metrics

- reproducible findings per CPU-hour;
- time to first finding;
- reproduction rate;
- false-positive rate;
- unique stable states and transitions;
- corpus growth and minimization ratio;
- seeded goal completion rate;
- best speedrun time/actions;
- cleanup failures per 100 launches;
- cost and latency per autonomous run.

Never use one percentage called “coverage” for all of these.

## Migration from Gamr

Keep Gamr’s existing `src/playtest` profiles in Gamr. Extract only generic contracts and utilities. Add a separate adapter package when the protocol is stable. Migrate one Gamr game first, compare in-process and PTY reports, then migrate the rest incrementally. This preserves Gamr’s catalog regression value while allowing Playtestr to test unrelated terminal programs.

## Immediate build order

1. Land repository hygiene and CI.
2. Implement stable observation fingerprints and corpus metrics.
3. Implement replay minimization and the `minimize` CLI command.
4. Add crash/hang/output-flood fixtures and lifecycle cleanup tests.
5. Resolve the Windows ConPTY teardown diagnostic.
6. Add edge profiles and novelty-guided search.
7. Define the adapter protocol.
8. Add objective agents, then optional semantic supervision.
