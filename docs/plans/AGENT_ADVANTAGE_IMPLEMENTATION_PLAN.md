# Agent Advantage implementation plan

Status: approved for implementation by the product owner  
Program: Playtestr terminal autonomy, evidence, and release readiness  
Decision date: 2026-08-19

## 1. Outcome

Build an autonomous terminal-game playtester that can discover mechanics, pursue goals, probe failures and recovery, find hidden routes, and minimize completion routes across unfamiliar games. Promotion is evidence-driven: the new agent system must outperform the strongest existing equal-action-budget baseline on a frozen validation suite without lifecycle regressions.

This program does not promise universal game understanding or flawless testing. “General” means the engine uses observable terminal state, declared input vocabulary, optional adapter evidence, and reusable learned experience rather than fixture-specific scripts. Claims in documentation and releases must remain bounded by measured results.

## 2. Product and repository decision

Playtestr remains a separate repository and product from Gamr.

- `playtestr`: generic testing engine, runner, world model, agents, evidence, benchmark, CLI, and later graphical backends.
- `gamr`: game platform and a consumer/integration target for Playtestr.
- Integration direction: Gamr depends on Playtestr’s public package/CLI contract. Playtestr must never import Gamr internals.
- Compatibility: Gamr’s bridge test is a required downstream check before a Playtestr release.

This separation is already correct and should not be reversed. It gives Playtestr an independent API, release cadence, benchmark corpus, issue tracker, and future customer base.

## 3. Design principles and reasoning

### Evidence before intelligence claims

The existing system is operationally mature but its agents use mostly static heuristics. Before changing them, freeze new games, seeds, budgets, and expected evidence, then record the old implementation’s result. This prevents benchmark leakage and gives a meaningful before/after comparison.

### Return, then explore

Each observed state keeps a reproducible shortest action prefix. Planning should return to a valuable known state and probe an unresolved action frontier from there. This follows the core hard-exploration insight in Go-Explore: archive useful states, return deterministically, then explore.

### Learn causal outcomes, not only coverage

Transition counts alone cannot answer whether an action is productive, blocked, risky, rewarding, or context-dependent. World Model V2 records state/action outcome statistics, reward evidence, frontier status, and prerequisite hypotheses. All hypotheses remain inspectable and confidence-scored.

### Adapt agent allocation under a fixed budget

No agent role should receive a permanently hard-coded share. A deterministic UCB-style scheduler balances agents that have produced useful evidence against under-sampled roles. Its state persists across campaign sessions.

### Verify important claims

Completion, hidden-route, and speedrun claims are re-run in fresh target processes. Route shortening uses delta-debugging-style removal and only accepts candidates that reproduce the same semantic outcome. A discovered screen is evidence; a verified route is a stronger product claim.

### Promote only through gates

Replay V2 and real Docker execution add trust and lifecycle risk. They are unlocked only after the autonomy benchmark passes. Hosted model providers and graphical playtesting stay behind later gates; the deterministic terminal core must remain useful without an LLM.

## 4. Scope

### Included in the Agent Advantage milestone

1. Frozen held-out terminal-game validation suite and pre-change baseline artifact.
2. Versioned World Model V2 with V1 migration.
3. Action-outcome, reward, frontier, and prerequisite evidence.
4. Multi-step frontier planning and semantic objective planning.
5. Deterministic adaptive agent scheduling with persisted campaign learning.
6. Cross-session route knowledge.
7. Completion and hidden-route verification and minimization.
8. Equal-budget advantage evaluation and machine-readable gate decision.
9. Unit, integration, migration, determinism, and downstream Gamr tests.

### Explicitly deferred unless the benchmark gate passes

- Replay V2 with execution-backend identity and stronger environment provenance.
- Real Docker lifecycle execution.
- Hosted model provider integration.
- Public `0.2` alpha release.
- Playwright/graphical browser execution.

## 5. Frozen validation design

The validation corpus is created before agent changes and lives under `fixtures/held-out/`. It contains deterministic games with no source-code access at runtime:

1. `relay-vault`: acquire and apply state-dependent prerequisites before opening a vault.
2. `echo-ritual`: discover a sparse multi-step hidden sequence.
3. `branching-quest`: pursue completion while retaining a separate secret branch.
4. `fault-recovery`: deliberately enter and recover from a failure state.
5. `route-forge`: find a completion route containing removable detours, then prove the shorter route.

The suite freezes:

- manifests and allowed actions;
- seeds;
- episodes and per-episode action budgets;
- expected semantic evidence;
- minimum acceptable intelligent-agent evidence;
- advantage policy thresholds.

The legacy system’s result is written as an immutable baseline artifact before algorithm work. Changes to a frozen fixture or gate require a new suite version, never an in-place relaxation.

## 6. Architecture

### 6.1 World Model V2

Persist these inspectable records:

- `WorldActionOutcome`: state, action, attempts, changed-state count, novel-state yield, failure/recovery/completion/hidden counts, cumulative and mean reward, and observed destination states.
- `WorldFrontier`: state/action pair, attempts, status (`untried`, `uncertain`, `productive`, `blocked`, `exhausted`), novelty yield, expected reward, and exploration priority.
- `PrerequisiteHypothesis`: action observed blocked in some states and productive in others, supporting states, evidence count, and confidence.
- existing states, transitions, mechanics, milestones, objectives, and routes.

Reward is an internal scheduling signal, never confused with a game’s own score:

- new state: 5
- new transition: 2
- new mechanic: 4
- new milestone: 8
- completion: 20
- hidden discovery: 20
- reproducible finding: 8
- recovery transition: 5

The exact components are returned in each `WorldModelDelta` so decisions are auditable.

Migration requirements:

- accept valid V1 snapshots and deterministically migrate them to V2;
- preserve every V1 state, transition, mechanic, objective, milestone, and route;
- derive initial outcome records from V1 transition counts;
- emit only V2 snapshots after load;
- reject malformed or cross-target data.

### 6.2 Planner

Create a pure deterministic planner with no process I/O. It ranks candidate plans:

1. shortest reproducible prefix to a nonterminal state;
2. one unresolved frontier action;
3. optional continuation selected from known productive transitions;
4. objective-matched actions from screen options/hints;
5. prerequisite probes where the same action is blocked in one state and productive in another.

Plan value combines expected evidence reward, novelty bonus, frontier uncertainty, objective relevance, reproducibility, and route-length cost. Tie-breaking is stable so equal seed and state produce identical results.

### 6.3 Adaptive scheduler

Maintain per-agent learning records:

- selections and actions;
- cumulative/mean evidence reward;
- state, transition, mechanic, milestone, completion, hidden, recovery, and finding yields;
- last selected episode.

Use a deterministic UCB score: empirical mean reward plus an exploration bonus, then combine it with proposal value. New roles are sampled before exploitation. Bootstrap is excluded from agent statistics. Campaigns persist these records, so later sessions reuse role-performance knowledge.

### 6.4 Route evidence

Represent verified routes separately from raw discovered prefixes. A route record includes kind, actions, discovery episode, verification attempts/matches, deterministic observation signature, minimized-from length, status, and timestamps.

Workflow:

1. select the shortest unverified completion/hidden prefix;
2. replay it in fresh target processes;
3. require a configured quorum of semantic matches;
4. remove chunks/actions using deterministic minimization;
5. re-verify the minimized route;
6. persist only observed evidence and never label a flaky route verified.

### 6.5 Advantage evaluator

Compare intelligent autonomy with coverage-guided, round-robin, and seeded-random strategies at the same action budget. Aggregate over scenarios and seeds.

The Agent Advantage gate passes only when all are true:

- every run confirms target cleanup and has no runner lifecycle regression;
- intelligent autonomy meets every scenario minimum evidence threshold;
- intelligent autonomy’s mean evidence score exceeds coverage-guided by at least `0.10`;
- intelligent autonomy wins against coverage-guided on at least `60%` of scenario/seed trials and loses on no more than `20%`;
- it exceeds both simple baselines by at least `0.15` mean evidence;
- repeated same-seed evaluation has the same decision and semantic determinism signature;
- all unit/integration tests and the Gamr bridge pass.

Ties are not dominance. A failed gate produces a diagnostic report and leaves downstream work locked.

## 7. Delivery sequence

### Phase A — freeze and baseline

- Add held-out fixtures and suite V1.
- Add schema validation tests.
- Build current code and record the legacy result, source commit, environment, and suite digest.
- Commit the freeze independently so later comparison has a stable boundary.

Exit: fixture freeze exists and legacy baseline is reproducible.

### Phase B — World Model V2

- Add V2 types, migration, outcome aggregation, reward components, frontiers, and prerequisites.
- Add migration round-trip and corruption tests.
- Update campaign compatibility.

Exit: old campaigns load without evidence loss; all snapshots emitted are V2.

### Phase C — planning and scheduling

- Add deterministic frontier planner.
- Upgrade agent proposals to consume plan evidence.
- Add UCB learning state, result telemetry, campaign persistence, and tests.

Exit: same seed/state is deterministic; productive agents receive more budget over time while every role remains explorable.

### Phase D — route verification

- Add fresh-process semantic verifier and minimizer.
- Persist route evidence in campaigns.
- Add false-positive, flaky, completion, hidden, and shortening tests.

Exit: verified/minimized route claims include replay evidence.

### Phase E — benchmark gate

- Add suite-level advantage aggregation and CLI/artifact output.
- Run the frozen suite twice.
- Run full checks, lifecycle soak, package test, and Gamr bridge.
- Record pass/fail with exact metrics.

Exit: downstream gate has an objective result.

### Phase F — conditionally unlocked work

Only if Phase E passes:

1. Replay V2 and V1 migration, including backend type/image/runtime identity and target artifact hash.
2. Actual Docker backend with create/start/input/timeout/kill/remove lifecycle and adversarial cleanup tests.
3. Provider-neutral optional hosted model interface with redaction, budget, timeout, and deterministic fallback.
4. Alpha packaging/readiness evidence.
5. Browser/graphical backend spike after terminal release stability.

## 8. Verification matrix

| Risk | Required proof |
|---|---|
| Snapshot breakage | V1 fixture migrates to V2 with no lost entities; V2 round-trip equality |
| Non-deterministic scheduling | identical semantic signatures for repeated same-seed runs |
| Benchmark gaming | frozen pre-change suite commit and legacy artifact |
| Budget unfairness | exact action-budget equality in every strategy result |
| False completion/secret | fresh-process quorum verification |
| Unsafe route minimization | outcome predicate must remain true after every accepted reduction |
| Cross-session corruption | campaign reload/resume test with learning and routes |
| Process leaks | per-run cleanup assertions plus lifecycle soak |
| Product coupling | Gamr adapter bridge passes against packed Playtestr artifact |
| Release overclaim | readiness report states gate result and known limits |

## 9. Non-goals and limits

- No claim that every possible terminal game is solvable.
- No source-code instrumentation requirement.
- No mandatory cloud model or network dependency.
- No arbitrary shell-command generation by agents.
- No Docker security claim before the actual backend and hostile-target tests exist.
- No graphical-game claim before a real graphical runner and benchmark exist.

## 10. Rollback and compatibility

- World V1 remains readable; V2 is the only writer.
- New campaign fields default safely when loading old campaign files.
- The legacy static agents remain constructible for A/B tests during this milestone.
- Advantage evaluation records algorithm IDs and source commit.
- If the gate fails, keep the infrastructure improvements, publish the diagnostic, and iterate on agents without enabling Replay V2/Docker.

## 11. Definition of done

The milestone is done when the code, tests, frozen evaluation, artifacts, documentation, and downstream bridge all agree on one honest status. A passing status means Playtestr has measured fixed-budget agent advantage on the declared terminal validation domain. A failing status is also a valid delivery when it identifies the gaps and correctly keeps later risky work locked.

## Research basis

- Ecoffet et al., [Go-Explore: a New Approach for Hard-Exploration Problems](https://arxiv.org/abs/1901.10995).
- Auer, Cesa-Bianchi, and Fischer, [Finite-time Analysis of the Multiarmed Bandit Problem](https://doi.org/10.1023/A:1013689704352).
- Zeller and Hildebrandt, [Simplifying and Isolating Failure-Inducing Input](https://www.st.cs.uni-saarland.de/papers/tse2002/).
- Schaul et al., [Prioritized Experience Replay](https://arxiv.org/abs/1511.05952).

These works inform the architecture; Playtestr uses deterministic graph/search statistics rather than presenting itself as a full reinforcement-learning system.
