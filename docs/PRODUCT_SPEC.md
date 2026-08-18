# Playtestr product specification

## Problem

Terminal-game developers can write unit tests for known mechanics, but they lack a reusable autonomous player that exercises the real terminal interface, searches unfamiliar interaction sequences, detects objective failures, and returns a reproducible case.

## Product

Playtestr is an evidence-first autonomous testing system for terminal games. It drives the same PTY/VT interface a player uses, retains interesting action prefixes, checks executable oracles, and emits replayable reports. Cooperative games can later expose semantic mechanics through an adapter. Models are optional planning assistants, not the source of truth.

## Initial users

- a game author running trusted code locally before a commit;
- a maintainer running deterministic regression exploration in CI;
- a framework author adding a semantic adapter for deeper mechanic checks.

Running third-party binaries is a later isolated-service use case, not an initial local-runner feature.

## Core jobs

1. Tell me whether the game launches, responds, exits correctly, and survives common interaction.
2. Explore more observable states and transitions than my scripted smoke tests.
3. Give me a replay that reproduces a crash, hang, overflow, or declared invariant failure.
4. Show which declared mechanics and goals were exercised, skipped, or failed.
5. Search for completion, optional routes, and faster valid routes under controlled rules.

## Product principles

- Evidence before intelligence.
- Oracles before prose.
- Determinism before optimization.
- Explicit truncation instead of ambiguous completion.
- Trusted local execution and isolated untrusted execution are different products.
- Generic core, optional adapters, no Gamr dependency.
- Honest metrics instead of a universal coverage percentage.

## User-visible objects

- Target manifest: versioned launch, environment, terminal, normalization, and budget policy.
- Episode: one reset-to-termination/truncation interaction trace.
- Observation: screen, cursor, terminal mode, time, and process state.
- Action: bounded terminal input plus timing and provenance.
- Corpus entry: interesting replayable prefix with target compatibility metadata.
- Finding: oracle result with a stable signature and evidence level.
- Replay: minimum information needed to recreate an episode.
- Report: versioned summary that references all canonical evidence.

## Success definition

The product succeeds when developers trust its findings enough to put it in CI and can reproduce them quickly. Autonomous breadth, human-like planning, speedrunning, and graphical support matter only after that trust exists.
