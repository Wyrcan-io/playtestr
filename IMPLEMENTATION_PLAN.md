# Playtestr implementation plan

Status: pre-alpha. This plan is a release contract, not a feature wishlist.

## Decision

Gamr and Playtestr remain separate repositories and products.

- `gamr`: games, game runtime, catalog, and game-specific regression tests.
- `playtestr`: game-independent execution, exploration, oracles, replay, and evidence.
- Future `@wyrcan/gamr-playtest`: optional adapters that expose Gamr mechanics to Playtestr.

Playtestr core must never import Gamr. A terminal game must remain testable without an adapter.

## Product thesis

An autonomous bot is not a playtester unless it can say what it tested, why a result is suspicious, and how to reproduce it. Playtestr therefore develops in this order:

1. trustworthy execution and evidence;
2. reproducible failure detection;
3. coverage-guided black-box exploration;
4. semantic adapters and executable mechanic checks;
5. objective agents such as completion, secrets, and speedrunning;
6. optional LLM supervision;
7. isolated hosted execution and graphical games.

The first sellable wedge is a deterministic terminal-game test runner for local development and CI. The long-term product is an autonomous game-testing platform.

## Claims and non-claims

Playtestr may claim only what its evidence supports.

| Claim | Required evidence |
| --- | --- |
| The target launched | process event plus first observation |
| A failure occurred | executable oracle result plus report |
| A failure reproduces | matching finding signature over repeated replays |
| A state or transition was observed | stable fingerprint plus action prefix |
| A mechanic was checked | adapter event/invariant or explicit black-box oracle |
| A goal was completed | goal predicate plus replay |
| A route is faster | same goal predicate, comparable seed/rules, lower measured cost |
| A behavior resembles a player persona | distribution across runs, labeled as a simulation |

Playtestr must not claim complete coverage, absence of bugs, discovery of every secret, or human judgment of fun. Black-box screen novelty is not code or mechanic coverage.

## Runtime architecture

```text
target manifest
      |
execution backend ---- resource/process policy
      |
terminal driver ---- VT parser ---- observation normalizer
      |                                  |
episode runner <---- action policy ---- corpus/search scheduler
      |
oracles ---- finding signatures ---- replay verifier ---- minimizer
      |
versioned report and artifacts
```

Execution backends are a hard boundary:

- `local-pty`: trusted targets only; target has the invoking user's filesystem and network permissions.
- `isolated`: future disposable container/VM backend with network, filesystem, CPU, memory, process, output, and wall-clock limits.

Environment filtering reduces accidental secret leakage but is not a sandbox. Hosted or untrusted execution is forbidden until the isolated backend passes its security gates.

Episodes follow a `reset -> observe -> step -> close` contract. Target termination and runner truncation are separate outcomes. This prevents a game ending normally from being confused with a time or action budget ending the test.

## Evidence levels

1. `observed`: captured once.
2. `reproduced`: same finding signature reproduced under the configured retry policy.
3. `confirmed`: executable invariant, goal predicate, or crash/process oracle confirms it.
4. `reviewed`: a human evaluated subjective impact.

Reports preserve the evidence level and never silently promote one level to another.

## Current implementation status

Implemented in the present hardening slice:

- strict manifest schema version 1 with unknown-field rejection and manifest-relative working directories;
- environment allowlisting with explicit opt-in inheritance;
- explicit trusted-target acknowledgement in the local CLI;
- rendered-screen startup readiness, output overflow enforcement, and bounded actions;
- separate episode status, outcome, and termination reason;
- versioned reports, runtime metadata, true observed transition keys, and per-run corpus additions;
- configurable volatile-screen patterns;
- validated replay input and controlled CLI errors;
- crash, no-output, and output-flood fixtures;
- Windows ConPTY compatibility fix with a zero-handle 100-run soak;
- Linux, macOS, and Windows CI matrix configuration.

Gate A is not complete until the configured CI matrix passes remotely and child-process-tree, resize, Unicode, signal, artifact-quota, and cancellation fixtures are implemented. Gate B finding signatures and reproduction quorum are also intentionally not claimed yet.

## Release ladder

### Gate A - trustworthy local runner (`0.1.0-alpha`)

Scope: deterministic PTY execution of trusted local terminal programs.

Required:

- versioned and strictly validated manifests, reports, replays, and findings;
- minimal environment inheritance with explicit opt-in names;
- startup, action, episode, output, and process-exit diagnostics;
- distinct target termination and runner truncation reasons;
- complete process-tree cleanup on normal exit, timeout, Ctrl-C, and crash;
- bounded artifact writing and secret-safe reports;
- deterministic fixtures for success, crash, no output, hang, flood, Unicode, resize, and child processes;
- Linux, Windows, and macOS verification where PTY behavior differs;
- 100-run cleanup soak with zero leaked target processes.

Exit criteria:

- every limit produces a distinct tested finding or termination reason;
- repeated seeded fixture runs produce compatible evidence;
- the CLI exits without helper-process diagnostics or leaked processes;
- local execution requires an explicit trusted-target acknowledgement;
- documentation never describes local execution as isolated.

### Gate B - reproducible findings (`0.2.0-alpha`)

Scope: turn failures into issue-ready evidence.

Required:

- stable finding signatures based on oracle, target outcome, and relevant observation;
- replay validation and compatibility migrations;
- configurable reproduction quorum, for example 3 of 3 or 4 of 5;
- flaky classification rather than false confirmation;
- minimization with total time/run budgets, cancellation, and final independent verification;
- raw terminal event capture sufficient to diagnose parser disagreement.

Exit criteria:

- crash, timeout, stall, and output-flood fixtures reproduce at the declared quorum;
- minimization preserves the same finding signature, not merely the same broad kind;
- minimized replay runs independently from its source report.

### Gate C - coverage-guided black-box explorer (`0.3.0-alpha`)

Scope: systematically reach more observable behavior than a key loop.

Required:

- configurable volatile-screen masking for clocks and animation;
- real transition fingerprints (`previous state + action + next state`);
- persistent corpus with provenance, schema version, and target compatibility key;
- deterministic prefix mutation: insert, delete, replace, repeat, splice, and timing jitter;
- restart/checkpoint scheduler and per-prefix energy budget;
- benchmark comparison against random and action-round-robin baselines;
- separate `smoke`, `explore`, and `edge` profiles.

Exit criteria:

- explorer beats both baselines on held-out deterministic fixtures under equal budgets;
- dynamic screens cannot create unbounded false novelty;
- every retained state/transition has a replayable prefix;
- metrics distinguish per-run discoveries from the persistent corpus total.

### Gate D - adapter SDK and mechanic coverage (`0.4.0-alpha`)

Scope: deep testing for cooperative games without weakening black-box mode.

Adapter contract:

- `reset(seed, options)`;
- `observe()` with semantic state and events;
- `actions()` with currently legal actions;
- `step(action)` returning observation, reward/score, `terminated`, `truncated`, and diagnostics;
- goals, invariants, mechanic identifiers, checkpoints, and stable state hash;
- adapter and game version metadata.

Exit criteria:

- one standalone fixture and one Gamr game implement the contract;
- reports show declared mechanics exercised, goals attempted/completed, and invariants checked;
- adapter failure cannot be reported as a game failure;
- PTY replay semantics remain available for user-visible reproduction.

### Gate E - objective agents (`0.5.0-alpha`)

Scope: completion, secrets, speedrunning, and player-style stress.

Profiles have separate objectives and metrics:

- `complete`: maximize seeded goal completion rate;
- `speedrun`: minimize actions and wall/game time while preserving goal evidence;
- `secrets`: maximize optional goal/event discovery after main-path competence;
- `persona`: sample documented risk, patience, exploration, and skill distributions;
- `edge`: maximize boundary and invalid-interaction checks.

Exit criteria:

- each profile has a budget, stop condition, oracle set, and benchmark;
- speedrun comparisons pin game version, seed/rules, viewport, and timing mode;
- secret findings reproduce and identify the evidence source;
- persona output is statistical and never called a literal human simulation.

### Gate F - semantic supervisor (`0.6.0-alpha`)

Scope: optional model-assisted interpretation and planning.

The model may interpret screens, propose actions/goals, rank corpus entries, and summarize evidence. It may not execute shell commands, bypass action schemas, determine security policy, or confirm findings without an oracle.

Exit criteria:

- deterministic agents still work offline;
- every model action passes the same bounded action contract;
- prompts and responses are separated from canonical replay evidence;
- external-provider redaction, consent, cost, latency, and retention controls are tested;
- benchmark uplift exceeds variance and cost is reported.

### Gate G - isolated service and graphical targets

Hosted execution requires disposable workers, default-deny networking, read-only inputs, writable scratch space, resource quotas, full process-tree control, no ambient credentials, artifact quotas, and abuse monitoring. Graphical games then add frame capture, input devices, OCR/vision, accessibility trees where available, and engine adapters. Neither belongs in the local PTY core.

## Benchmark suite

Each fixture declares expected reachable states, transitions, findings, goals, and nondeterminism:

1. menu/navigation;
2. text entry, Unicode, and paste;
3. turn-based state machine;
4. real-time clock/animation;
5. hidden route;
6. crash-on-sequence;
7. no-output startup and hang;
8. output flood;
9. resize and alternate-screen lifecycle;
10. child-process cleanup;
11. flaky failure;
12. one Gamr adapter integration.

## Scorecard

No single number is called coverage. Track:

- reproducible findings per CPU-hour;
- time to first confirmed finding;
- reproduction and false-positive rates;
- unique stable states and true transitions per run;
- corpus additions and corpus reuse yield;
- minimization ratio and verification rate;
- declared mechanics exercised and invariants checked;
- goal completion distribution by seed;
- speedrun action/time distribution;
- cleanup failures per 100 launches;
- model cost/latency and measured benchmark uplift.

## Immediate work order

1. Enforce the Gate A manifest, environment, lifecycle, diagnostics, and schema contracts.
2. Add the missing adversarial fixtures and platform/soak tests.
3. Implement finding signatures, replay validation, reproduction quorum, and safe minimization.
4. Build true transition tracking, volatile masking, corpus persistence, and mutation search.
5. Publish the adapter protocol only after black-box evidence is stable.
6. Integrate one Gamr game, then benchmark objective agents.
7. Add an optional semantic supervisor only after deterministic benchmarks exist.

Features move forward only when the previous gate's automated acceptance tests pass. This is how Playtestr becomes dependable; adding a smarter agent does not waive a lower-level gate.
