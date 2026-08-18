# Intelligent autonomy implementation plan

Status: implementation plan for Playtestr `0.2`; terminal-only, deterministic-core milestone.

Implementation checkpoint (2026-08-19): the deterministic semantic layer, shared world
model, six-agent orchestration, evaluation fixtures, CLI/API surface, and structural Gamr
adapter are implemented and locally verified. Remote cross-platform CI and fixed-budget
baseline comparison remain release evidence; licensing/tagging, stronger native isolation,
Docker execution, optional model providers, and graphical backends remain gated follow-up
work as described below.

## 1. Product outcome

Build a game-agnostic autonomous layer that can interpret terminal screens, retain a shared model of what it has observed, coordinate complementary testing strategies, and report measurable mechanic and objective discovery.

The milestone succeeds when Playtestr can test several unrelated terminal-game shapes and show, with replayable evidence, that coordinated semantic agents discover more expected mechanics and objectives than the existing action round-robin under a fixed budget.

This milestone does not claim human equivalence, complete mechanic coverage, or safe execution of untrusted programs.

## 2. Why this order

The implementation order is a correctness dependency:

1. Evaluation contracts come before agent sophistication so improvement cannot be defined after seeing results.
2. Semantic extraction comes before a world model because the model needs stable, serializable evidence rather than raw prose.
3. The world model comes before specialized agents because agents must share the same facts and transition history.
4. Specialized agents come before orchestration so the scheduler has genuinely different proposals to compare.
5. Diverse fixtures come before product claims so the design cannot overfit Gamr or one hidden-route toy.
6. The Gamr adapter follows the generic contract so Playtestr never imports Gamr.
7. Model providers, Docker, and graphical backends remain later gates; none are required for deterministic core behavior.

## 3. Architectural decisions

### 3.1 Deterministic core, optional model providers

- Core agents produce bounded proposals from screen semantics, action history, corpus prefixes, and the shared world model.
- The same seed and evidence produce the same proposal ordering.
- An eventual LLM may implement the same semantic-analyzer or proposal-provider interfaces.
- Provider output is advisory. Executable findings, terminal observations, replays, and target adapters remain authoritative.
- Core tests never require network access, credentials, or a hosted model.

### 3.2 Facts instead of hidden reasoning

The public report records concise decision facts:

- selected agent and objective;
- proposal score and machine-readable reasons;
- expected semantic tags;
- observed states, transitions, mechanics, and milestones;
- replay and budget consumed.

It does not depend on or expose private chain-of-thought.

### 3.3 Black-box truth boundary

Playtestr can measure:

- observed screen states and transitions;
- action and action-sequence novelty;
- inferred mechanic hypotheses with confidence and evidence references;
- adapter-declared milestones and completion signals;
- crashes, hangs, stalls, cleanup, and replay reproduction.

It cannot infer internal code coverage or prove that no hidden mechanic exists unless a target provides instrumentation.

### 3.4 Adapter boundary

Playtestr defines a structural `TargetAdapter` protocol. Adapters may contribute:

- additional action vocabulary;
- semantic tags and milestone detectors;
- completion, failure, hidden-feature, and recovery signals;
- initial objectives and mechanic labels.

Gamr implements this protocol in the Gamr repository. Playtestr core has no Gamr dependency, package import, or game-specific branch.

## 4. Public contracts

### 4.1 Semantic observation

Each terminal observation may be deterministically summarized as:

- normalized title and non-empty lines;
- prompt and menu-option candidates;
- inferred action hints;
- numeric counters and labels;
- semantic tags such as `help`, `menu`, `inventory`, `resource`, `completion`, `failure`, `error`, `secret`, `timing`, and `text-entry`;
- stable semantic signature.

Raw observations remain available. Semantics supplement rather than replace VT fingerprints.

### 4.2 World model V1

The world model contains:

- target identifier and schema version;
- state nodes keyed by structural fingerprint;
- shortest known replay prefix for each state;
- visit count, semantic tags, terminal flags, and milestone evidence;
- directed transitions keyed by source, action shape, and destination;
- mechanic hypotheses with confidence, evidence count, and supporting states/actions;
- objective records and statuses;
- dead-end and recovery evidence;
- completion and hidden-feature prefixes.

Serialization is deterministic. Environment values and private provider material are forbidden.

### 4.3 Agent protocol

An autonomous agent has:

- stable identifier and role;
- deterministic `propose(context)` operation;
- zero or more bounded action-sequence proposals;
- objective, score, machine-readable reasons, and expected tags per proposal.

The protocol does not grant filesystem, process, or network access to agents.

### 4.4 Orchestrator result

An autonomy run reports:

- total episodes/actions/time and stop reason;
- world-model snapshot;
- per-agent proposal, selection, action, state, mechanic, milestone, completion, and finding contribution;
- selected episode records with replay references;
- evaluation metrics when a scenario is supplied.

## 5. Specialized deterministic agents

### 5.1 Mechanic mapper

Purpose: identify the effect of each available or inferred action from short, reproducible prefixes.

Priorities:

- untried actions at shallow states;
- help and instruction screens;
- action-result pairs that produce new tags or counters;
- short prefixes over long speculative sequences.

### 5.2 Edge-case attacker

Purpose: stress input handling and state boundaries.

Candidate families:

- repeated keys;
- rapid zero-wait actions;
- long waits and bounded holds;
- Escape, Backspace, Tab, invalid-looking actions when allowed;
- repeated confirm/cancel and boundary navigation.

All timing and sequence sizes remain bounded by orchestrator policy.

### 5.3 Secret hunter

Purpose: discover hidden routes, uncommon commands, help-only actions, and surprising sequences.

Priorities:

- low-frequency actions;
- repeated and spliced novel prefixes;
- states tagged as suspicious, locked, hidden, bonus, or incomplete;
- branches not selected by the mechanic mapper.

### 5.4 Speedrunner

Purpose: reach known completion states with fewer actions.

It activates after completion evidence exists, replays the shortest completion prefix, removes detours, and proposes shorter graph paths. Exact completion evidence must survive any claimed improvement.

### 5.5 Completionist

Purpose: maximize declared milestones and semantic mechanic diversity.

It prioritizes unmet adapter milestones, unseen tags, unvisited action-state pairs, and prefixes adjacent to frontier states.

### 5.6 Recovery tester

Purpose: measure whether a confused player can escape help, menus, invalid input, dead ends, and failure screens.

It proposes bounded recovery sequences and records whether the target returns to a previously productive state.

## 6. Multi-agent scheduling

### 6.1 Proposal scoring

The scheduler combines:

- agent base priority;
- predicted novelty;
- unmet milestone value;
- mechanic/tag novelty;
- replay length penalty;
- duplicate and recently selected penalties;
- per-agent fairness credit;
- risk budget for edge-case timing.

Tie-breaking is deterministic by score, agent identifier, objective, and action-sequence key.

### 6.2 Shared learning

After every episode:

1. ingest all observations and transitions into the world model;
2. apply adapter semantics and milestones;
3. update mechanic confidence only from observable evidence;
4. make new shortest prefixes visible to every agent;
5. credit the selected agent for newly observed evidence;
6. regenerate proposals from the updated model.

Every episode starts a fresh target process. Shared knowledge is explicit data, not leaked process state.

### 6.3 Budgets and termination

Required limits:

- episode count;
- actions per episode;
- total actions;
- elapsed time per episode and overall;
- proposal count and sequence length;
- artifact and world-model size;
- cancellation signal.

Stop reasons distinguish completion, budget exhaustion, queue exhaustion, cancellation, and runner failure.

## 7. Evaluation design

### 7.1 Scenario contract

An evaluation scenario declares only externally observable expectations:

- mechanic identifiers and detectors;
- milestone identifiers and detectors;
- optional completion, hidden-feature, failure, and recovery detectors;
- fixed manifest, seed set, viewport, action vocabulary, episode count, and action budget.

### 7.2 Metrics

- expected mechanic recall;
- required milestone recall;
- unique semantic tags;
- unique VT states and transitions;
- completion and hidden-feature success;
- episodes/actions to first objective;
- crashes and exact finding signatures;
- cleanup failures;
- per-agent unique contribution;
- deterministic repeat agreement.

Precision is not claimed for undeclared mechanics. Inferred hypotheses are reported separately from scenario recall.

### 7.3 Diverse fixture matrix

The suite must include:

1. menu/resource game: help, inventory, resource acquisition, purchase, completion, and an invalid action;
2. text-command game: prompt recognition, multi-character commands, inventory, navigation, and completion;
3. timing game: wait-sensitive transition, premature action, recovery, and completion;
4. hidden-route fixture: sequence-secret discovery;
5. one real Gamr game through the external adapter after the generic suite is green.

### 7.4 Baselines

Compare under identical episode and per-episode action budgets:

- round-robin;
- seeded random;
- coverage-guided corpus explorer;
- coordinated semantic agents.

Release evidence must use a fixed seed set, not one favorable random run.

## 8. Gamr adapter implementation

Gamr will export a Playtestr adapter entry that:

- creates a trusted local manifest for a selected Gamr CLI game;
- enables reduced motion and color-stable output;
- maps existing Gamr playtest milestones to the structural adapter detector shape;
- supplies category and generic action vocabulary;
- exposes no Playtestr runtime dependency;
- keeps all Gamr game IDs and milestone knowledge outside Playtestr core.

Acceptance requires typecheck/build in both repositories and one adapter contract test in Gamr.

## 9. Release and platform gates

### Gate A: local deterministic core

- all semantic/world/agent/evaluation unit tests pass;
- diverse fixtures pass integration tests;
- deterministic reruns agree;
- no cleanup regression in the lifecycle soak.

### Gate B: remote platform truth

- Node 22 passes on Windows, Linux, and macOS;
- Node 24 passes on Linux;
- Windows lifecycle soak passes remotely;
- platform differences are documented, not skipped silently.

### Gate C: alpha tag

Only after A and B:

- choose and record a license;
- remove `private` only if publication is intended;
- bump to the next alpha version;
- produce release notes and signed/tagged checkpoint;
- perform package install smoke from the packed tarball.

## 10. Docker isolation roadmap

Docker is the next execution-backend milestone after terminal intelligence, not part of the local PTY safety claim.

Required design:

- explicit image/build context allowlist;
- no host network by default;
- read-only root filesystem where possible;
- non-root user;
- CPU, memory, process, output, artifact, and wall-clock limits;
- scoped temporary workspace;
- no ambient credentials or host mounts;
- process-tree/container deletion on cancellation;
- backend capability report and adversarial escape tests.

The CLI must use a separate acknowledgement for image builds or network-enabled targets.

## 11. Graphical backend roadmap

Graphical testing starts only after terminal evaluation demonstrates stable agent improvement.

The agent, world-model, objective, finding, replay, and evaluation contracts remain shared. A graphical backend adds:

- frame observations and region/object semantics;
- mouse, controller, and key-state actions;
- deterministic capture timing;
- window/process focus control;
- visual-difference normalization;
- video/screenshot artifact quotas;
- backend-specific sandbox and anti-cheat boundaries.

Initial targets should be deterministic local HTML/canvas games before arbitrary native games.

## 12. Definition of done for this implementation slice

- deterministic semantic extraction is public and tested;
- a serializable shared world model learns states, transitions, mechanics, milestones, completion, and hidden evidence;
- all six specialized agents implement one common protocol;
- the orchestrator performs fresh-process multi-agent episodes with deterministic scheduling and bounded budgets;
- three additional unrelated fixture shapes and the existing hidden route have evaluation coverage;
- evaluation reports mechanic/milestone recall and agent contributions;
- Gamr exports a structural adapter without making Playtestr depend on Gamr;
- CLI/API documentation distinguishes deterministic autonomy from future LLM supervision;
- both repositories pass their local verification gates;
- unresolved remote CI, native Windows Job Objects, Docker isolation, licensing, and graphical work remain explicit release gates.
