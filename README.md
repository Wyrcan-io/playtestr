# Playtestr

Standalone autonomous black-box playtesting for terminal games.

The first slice runs an arbitrary terminal program in a pseudo-terminal, parses its VT output, drives bounded keyboard exploration, detects crashes/timeouts/stalls, tracks stable state novelty, and emits replayable JSON evidence.

## Quick start

```sh
npm install
npm run build
node dist/cli.js run --manifest fixtures/turn-counter.json --profile explore --artifacts artifacts/example
node dist/cli.js minimize --manifest fixtures/crash-sequence.json --replay artifacts/example/replay.json --kind crash
```

The manifest format is JSON in this first implementation. YAML support and richer game adapters are planned after the external runner is stable.

Profiles currently include:

- `baseline`: bounded common-key smoke exploration;
- `explore`: least-used action exploration with stable state metrics.

Every run can emit `report.json`, `replay.json`, and `last-screen.txt`. Findings should be treated as evidence to reproduce, not as a claim of complete game coverage.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the staged product roadmap and the Gamr migration boundary. Repository conventions live in [AGENTS.md](AGENTS.md), and the architecture is documented in [docs/architecture/overview.md](docs/architecture/overview.md).

## Repository boundary

Gamr retains its in-process catalog regression tests. Playtestr owns the generic target manifest, PTY driver, replay format, agents, oracles, and reports. A future Gamr adapter will let Gamr games expose seeds, semantic events, goals, and invariants without making Playtestr depend on Gamr.
