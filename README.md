# Playtestr

Evidence-first autonomous black-box playtesting for terminal games.

The first slice runs an arbitrary terminal program in a pseudo-terminal, parses its VT output, drives bounded keyboard exploration, detects crashes/timeouts/stalls, tracks stable state novelty, and emits replayable JSON evidence.

## Quick start

```sh
npm ci
npm run build
node dist/cli.js run --manifest fixtures/turn-counter.json --profile explore --artifacts artifacts/example --trust-target
node dist/cli.js run --manifest fixtures/crash-sequence.json --profile explore --max-actions 4 --artifacts artifacts/crash --trust-target
node dist/cli.js minimize --manifest fixtures/crash-sequence.json --replay artifacts/crash/replay.json --kind crash --trust-target
npm run soak
```

The manifest format is JSON in this first implementation. YAML support and richer game adapters are planned after the external runner is stable.

Profiles currently include:

- `baseline`: bounded common-key smoke exploration;
- `explore`: deterministic action-diversity exploration with stable state metrics. Coverage-guided corpus search is planned, not yet claimed.

Every run can emit `report.json`, `replay.json`, and `last-screen.txt`. Findings should be treated as evidence to reproduce, not as a claim of complete game coverage.

The current `local-pty` backend is not a sandbox. It runs trusted targets with your user permissions, so the CLI requires `--trust-target`. Ambient environment variables are denied except for a small operational allowlist and names explicitly selected by the manifest.

## Manifest

```json
{
  "schemaVersion": 1,
  "id": "my-game",
  "command": "node",
  "args": ["game.mjs"],
  "allowedKeys": ["Enter", "ArrowUp", "ArrowDown", "q"],
  "episodeTimeoutMs": 30000,
  "maxOutputBytes": 2000000,
  "observation": {
    "volatilePatterns": ["TIME \\d+"]
  }
}
```

Relative `cwd` values resolve from the manifest directory; when omitted, the manifest directory is used. `env` sets explicit values and `inheritEnv` opts into additional host variable names. Do not put secrets directly in a committed manifest.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the release-gated roadmap and permanent Gamr boundary. The concrete product definition is in [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md), the primary-source rationale is in [docs/RESEARCH.md](docs/RESEARCH.md), and the architecture is documented in [docs/architecture/overview.md](docs/architecture/overview.md).

## Repository boundary

Gamr retains its in-process catalog regression tests. Playtestr owns the generic target manifest, PTY driver, replay format, agents, oracles, and reports. A future Gamr adapter will let Gamr games expose seeds, semantic events, goals, and invariants without making Playtestr depend on Gamr.
