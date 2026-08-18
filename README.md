# Playtestr

Standalone autonomous black-box playtesting for terminal games.

The first slice runs an arbitrary terminal program in a pseudo-terminal, parses its VT output, drives bounded keyboard exploration, detects crashes/timeouts/stalls, and emits a replayable JSON report.

## Quick start

```sh
npm install
npm run build
node dist/cli.js run --manifest fixtures/turn-counter.json --artifacts artifacts/example
```

The manifest format is JSON in this first implementation. YAML support and richer game adapters are planned after the external runner is stable.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the staged product roadmap and the Gamr migration boundary.

## Repository boundary

Gamr retains its in-process catalog regression tests. Playtestr owns the generic target manifest, PTY driver, replay format, agents, oracles, and reports. A future Gamr adapter will let Gamr games expose seeds, semantic events, goals, and invariants without making Playtestr depend on Gamr.
