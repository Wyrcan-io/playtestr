# Playtestr implementation plan

Playtestr is a separate repository from Gamr. Gamr keeps its in-process catalog regression profiles; Playtestr owns generic terminal targets and autonomous black-box testing.

## Current slice: external terminal MVP

- JSON target manifests with command, args, cwd, environment, viewport, seed, and budgets.
- Windows/Unix PTY process launch through `node-pty`.
- VT screen parsing through `@xterm/headless`.
- Keyboard action encoding, wait/hold timing, resize, and clean shutdown.
- Baseline bounded exploration policy.
- Crash, unexpected-exit, timeout, stall, and output-limit report types.
- Versioned action replays and report/screen artifacts.
- CLI entry point and a deterministic fixture game.

## Next implementation phases

1. Harden lifecycle behavior: process trees, stderr, output limits, signal handling, and cross-platform PTY CI.
2. Add novelty/state hashing, action-prefix corpus storage, sequence mutation, and delta-debugging.
3. Add edge-case profiles for invalid input, timing, resize, restart, pause, and quit.
4. Define the optional adapter contract for seeds, state snapshots, semantic events, goals, and invariants.
5. Add Gamr adapter profiles without importing Gamr into Playtestr core.
6. Add speedrun/search policies and hidden-feature evidence collection.
7. Add a pluggable LLM supervisor with strict structured actions, budgets, and evidence-backed findings.
8. Add CI artifacts, report comparison, and hosted job execution only after local replay is reliable.

## Migration rule

Do not move Gamr’s current `src/playtest/specs.ts` wholesale. Those profiles know the built-in game registry and are valuable end-to-end tests for Gamr. Extract only generic concepts into Playtestr; migrate game-specific knowledge later through an adapter package.
