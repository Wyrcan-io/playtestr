# Terminal autonomy execution plan

Status: implemented foundation; remote CI validation and native Windows Job Objects remain release gates.

Implementation checkpoint (2026-08-19): work packages B-H are present with automated tests. Package A is configured in `.github/workflows/ci.yml` and becomes complete only after the pushed matrix succeeds. Windows tree cleanup currently uses `taskkill /T /F`; native Job Objects remain a hardening milestone rather than a capability claim.

This document turns the next product milestones into testable work packages. It records the decisions behind the order, the contracts that may change, the failure modes that must be exercised, and the evidence required before a capability is claimed.

## 1. Objective

Deliver a trustworthy terminal-game testing foundation that can:

1. start, observe, resize, cancel, and terminate a target and its descendants;
2. distinguish target failures from runner failures and external truncation;
3. reproduce and classify findings across repeated runs;
4. minimize only while preserving the exact finding;
5. retain useful action prefixes across runs;
6. mutate and schedule those prefixes to discover additional observable states;
7. prove search improvement against equal-budget baselines.

This plan does not include semantic game adapters, LLM planning, graphical input, hosted untrusted execution, or claims of complete mechanic coverage.

## 2. Ordering rationale

The order is a correctness dependency, not a preference:

- Search cannot be trusted if an episode can leak a child process or ignore cancellation.
- Reproduction cannot be trusted if findings have no stable identity.
- Minimization cannot be trusted if it matches only a broad category such as `crash`.
- Persistent corpora cannot be trusted without a target compatibility key and schema validation.
- A smarter explorer cannot be claimed as better without equal-budget benchmarks.

Therefore work moves through the following gates. A later work package may be developed behind an internal API, but it is not user-visible until all earlier acceptance checks pass.

## 3. Global engineering rules

### 3.1 Evidence rules

- Every finding has a stable signature, evidence level, oracle kind, and action position.
- Every retained corpus entry has a replayable action prefix and target compatibility key.
- Every minimization result records its budget, stop reason, and independent final verification.
- Every benchmark pins target, viewport, seed, action vocabulary, and total action/episode budget.
- Reports never serialize environment values.

### 3.2 Safety rules

- `local-pty` remains trusted-target-only.
- Cancellation and limits are fail-closed: an interrupted operation must proceed to cleanup.
- Process cleanup addresses the process tree, not only the immediate PTY child.
- Artifact limits are checked before files are committed to the artifact directory.
- Invalid schemas and unsupported versions are rejected, never defaulted silently.

### 3.3 Determinism rules

- Seeded search and mutation produce the same candidate order.
- Wall-clock timestamps are evidence metadata, not search inputs.
- Corpus serialization has deterministic ordering.
- Benchmarks use fixed fixtures and seeds in CI.

## 4. Work package A: checkpoint and CI truth

### Purpose

Establish a known-good checkpoint and make remote platform results authoritative.

### Deliverables

- Keep the current hardening commit as the baseline.
- Add CI jobs for Node 22 on Windows, Linux, and macOS plus Node 24 on Linux.
- Run unit/integration tests and CLI smoke on every platform.
- Run the 100-episode lifecycle soak on Windows.
- Upload failure diagnostics only; do not upload target artifacts by default.
- Document any platform-specific backend capability in reports.

### Acceptance

- All matrix jobs pass from a clean `npm ci`.
- No test is skipped by operating system without a linked reason and replacement check.
- CI failure is not overridden by a local pass.

### Rollback

If the pinned PTY beta fails a platform, keep it pinned and isolate the platform failure. Do not silently return to a version with known cleanup crashes.

## 5. Work package B: execution backend and lifecycle control

### Decision

The runner depends on an `ExecutionBackend` interface rather than constructing `PtyTerminalSession` directly. The first backend remains `local-pty`. This creates a real boundary for a future isolated worker without pretending the local backend is one.

### Public contracts

```text
ExecutionBackend
  id
  capabilities
  start(manifest, seed, viewport, signal) -> TerminalSession

TerminalSession
  observe
  diagnostics
  send
  resize
  probeProcessAlive
  waitForExit
  stop(reason)
```

Capabilities include process-tree cleanup, resize, signals, raw terminal events, and isolation level. Reports record active capabilities.

### Cancellation

- `RunOptions.signal` accepts an `AbortSignal`.
- Cancellation is checked before launch, after launch, before each action, during action waits, and during exit grace.
- Cancellation produces `status=cancelled`, `outcome=truncated`, and `termination.kind=cancelled`.
- Cleanup always runs after cancellation.
- CLI handles Ctrl+C by aborting the active operation; a second Ctrl+C may force the CLI process after a clear warning.

### Process-tree policy

- Unix: launch/identify the PTY process group and signal the negative process-group id, with direct-pid fallback.
- Windows: graceful Ctrl+C first, then terminate the full tree using the platform tree-control mechanism; record which mechanism was active.
- Cleanup result records graceful exit, forced tree termination, elapsed cleanup time, and whether descendants remain detectable.
- The current guarded ConPTY input-pipe shim remains version-pinned and soak-tested.

### Failure modes

- target exits normally;
- target ignores Ctrl+C;
- target crashes;
- target creates a long-lived child;
- target exits while child remains;
- cancellation during startup;
- cancellation during action wait;
- timeout during terminal output;
- cleanup mechanism fails.

### Acceptance

- Child-process fixture leaves no parent or child process.
- Cancellation exits within its cleanup budget and leaves no target process.
- Cleanup failure is a runner finding, not a game crash.
- The library and CLI both exit naturally with no native handles.
- 100 repeated launches pass after every PTY dependency change.

## 6. Work package C: adversarial fixture matrix

### Fixtures

| Fixture | Behavior | Expected evidence |
| --- | --- | --- |
| Unicode | wide, combining, emoji, and non-Latin text/input | stable capture without corruption |
| Resize | reports viewport after resize | observation dimensions and rendered dimensions agree |
| Hang | renders once, then ignores input | time truncation, not crash |
| Signal | terminates itself abnormally | crash signature with signal/exit evidence |
| Child tree | parent and child both stay alive | forced tree cleanup, no remaining pids |
| Output flood | exceeds byte budget | one output-limit finding |
| Startup silence | never renders | startup-failure finding |
| Flaky | deterministic alternating outcome via test-owned counter | mixed reproduction classification |
| Hidden route | secret behind a non-round-robin sequence | explorer benchmark target |

### Resize contract

Resize is a first-class terminal operation. It is tested at the session layer before it becomes an autonomous edge action. Viewport dimensions are included in transition identity so resize discoveries do not collide with ordinary frames.

### Artifact quotas

Artifact output is assembled in memory, measured in UTF-8 bytes, and written only if the complete set fits the configured total quota. The first implementation writes to a temporary sibling directory and renames it only after every file succeeds. Partial artifact sets are removed on failure.

### Acceptance

- Every fixture has a manifest, a human-readable purpose, and at least one assertion.
- Fixture behavior is deterministic unless its purpose is controlled flakiness.
- Tests clean up files and processes they create.

## 7. Work package D: finding identity and reproduction

### Finding signature

A signature is a SHA-256 digest of a versioned canonical payload:

```text
signatureVersion
target id
oracle kind
relevant exit code or signal
stable structural observation fingerprint
oracle-specific discriminator
```

Action position, elapsed time, prose message, and absolute paths are excluded because minimization and platform timing may change them without changing the failure.

### Evidence level

- `observed`: occurred once.
- `reproduced`: matched the same signature at the requested quorum.
- `confirmed`: an executable crash/process/invariant oracle proves the condition.
- `reviewed`: reserved for later human review metadata.

Crash and hard resource-limit oracles may be `confirmed` on observation, but stability is reported separately.

### Reproduction result

```text
signature
attempts requested/completed
matches
quorum required/met
classification: stable | flaky | not-reproduced | cancelled | budget-exhausted
per-attempt observed signatures
elapsed time
```

`stable` requires every completed attempt to match. A mixture is `flaky`, even if quorum is met. `not-reproduced` means zero matches. This avoids hiding instability behind a passing quorum.

### Budgets

- maximum attempts;
- required matches;
- total elapsed time;
- per-episode budgets inherited from the replay/manifest;
- optional cancellation signal.

### Acceptance

- Stable crash fixture is stable at 3/3.
- Controlled flaky fixture is classified flaky.
- A different crash screen/exit discriminator does not satisfy the target signature.
- Reproduction stops on cancellation or when quorum becomes mathematically impossible.

## 8. Work package E: exact-signature minimization

### Decision

Keep generic delta debugging, but add a finding-aware orchestration layer. Generic `minimizeSequence` knows only a predicate; product minimization knows the target signature, quorum, and budgets.

### Algorithm

1. Validate replay schema and target compatibility.
2. Establish the exact original signature.
3. Reproduce the original at the configured quorum.
4. Run deterministic chunk deletion.
5. Optionally simplify timing values after structural deletion.
6. Reject a candidate that produces only the same broad kind with another signature.
7. Independently verify the final candidate.
8. Emit the minimized replay only if final quorum is met.

### Stop reasons

- completed;
- attempt budget;
- elapsed-time budget;
- cancelled;
- original not reproducible;
- final verification failed.

### Acceptance

- Crash replay reduces while preserving the exact signature.
- A candidate causing a different crash is rejected.
- Flaky minimization is labeled and never promoted to stable.
- Empty and one-action sequences terminate correctly.
- Final replay runs independently.

## 9. Work package F: persistent coverage corpus

### Corpus schema

```text
schemaVersion: 1
targetCompatibilityKey
entries[]:
  structural fingerprint
  shortest action prefix
  first discovery episode/action
  discovery seed
  parent fingerprint
  transition fingerprint
  mutation provenance
```

The compatibility key hashes launch identity, viewport, normalization policy, action vocabulary, and seed configuration. Environment values may influence the hash but are never serialized directly.

### Persistence

- Deterministic JSON ordering.
- Atomic temporary-file replacement.
- Strict version and compatibility validation.
- Explicit merge semantics: shortest prefix wins; equal-length ties use deterministic lexical ordering.
- Corrupt or incompatible corpora fail closed unless the caller explicitly starts fresh.

### Acceptance

- Save/load round trip preserves entries exactly.
- Incompatible target key is rejected.
- Repeated discoveries preserve the deterministic shortest prefix.
- No environment values appear in corpus JSON.

## 10. Work package G: mutation and restart scheduler

### Mutation operators

All operators are deterministic under seed and individually testable:

- append allowed action;
- insert action;
- delete action;
- replace action;
- repeat action or subsequence;
- splice prefixes from two corpus entries;
- timing jitter within configured bounds.

Mutation never creates invalid action sizes or timing values. Edge-only actions remain separated from ordinary exploration policy.

### Scheduler

- Each candidate starts from a fresh target process until checkpoint support exists.
- Newly discovered states enter a frontier.
- Frontier entries receive bounded energy based on novelty, prefix length, and prior attempts.
- Shorter prefixes are preferred for equal novelty.
- Candidate and episode budgets are explicit.
- Search state is serializable so interrupted runs can resume.

### Profiles

- `smoke`: short deterministic key coverage and lifecycle checks.
- `explore`: corpus-guided prefix search.
- `edge`: invalid input, timing, resize, restart, and lifecycle boundaries.

The existing action-diversity policy remains a baseline and is not called coverage-guided.

### Acceptance

- Every executed candidate is replayable.
- The same seed and empty corpus produce the same candidate sequence.
- Restarts do not leak processes or native handles.
- Corpus growth is bounded by unique compatible fingerprints.

## 11. Work package H: benchmark harness

### Baselines

- deterministic action round-robin;
- seeded random action selection;
- corpus-guided explorer.

### Fairness

- identical target version and manifest;
- identical allowed action set;
- identical total episode/action/time budget;
- fixed seed set;
- independent fresh target state per episode;
- volatile-screen policy held constant.

### Metrics

- unique stable states;
- unique true transitions;
- hidden-route completion;
- actions and episodes to first discovery;
- reproducibility of discovered prefixes;
- cleanup failures.

### Release criterion

The explorer must beat both baselines on the held-out hidden-route fixture across the fixed CI seed set under equal budgets. One favorable run is not sufficient evidence.

## 12. CLI and artifact surface

Planned commands:

```text
playtestr run
playtestr verify
playtestr minimize
playtestr explore
playtestr benchmark
```

All local execution commands require `--trust-target`. Machine-readable JSON output and human summaries derive from the same typed result. Exit codes are stable:

- `0`: requested operation completed and its policy passed;
- `1`: controlled finding, failed verification, invalid input, or runner failure;
- `130`: cancelled by Ctrl+C after cleanup (the conventional `128 + SIGINT` value).

## 13. Verification matrix

| Check | Unit | Integration | Soak/CI |
| --- | --- | --- | --- |
| Manifest/report/replay/corpus schemas | yes | fixture load | clean install |
| Cancellation | race helpers | live PTY | repeated Windows |
| Tree cleanup | controller | child fixture | 100 runs |
| Unicode/resize | normalization | PTY fixture | OS matrix |
| Signatures | canonical payload | repeated crash | OS matrix |
| Quorum/flakiness | fake executor | flaky fixture | fixed seeds |
| Minimization | predicate | exact crash signature | CLI smoke |
| Persistence | round trip | resumed search | package smoke |
| Mutation | each operator | hidden route | deterministic repeat |
| Benchmark | aggregation | all strategies | fixed CI seeds |

## 14. Definition of done

This execution plan is implemented when:

- all public contracts are exported and documented;
- all listed fixtures and acceptance tests pass;
- `npm run check`, CLI smoke, package dry-run, production audit, and 100-run soak pass;
- no local command claims isolation;
- no broad-kind minimization is presented as exact reproduction;
- benchmark output proves or rejects explorer uplift honestly;
- remaining limitations are listed in the release notes.

Remote CI status and a deliberate licensing decision remain required before publishing the package publicly.
