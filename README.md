# Playtestr

Evidence-first autonomous black-box playtesting for terminal games.

Playtestr runs an arbitrary terminal program in a pseudo-terminal, parses its VT output, drives bounded keyboard exploration, detects crashes/timeouts/stalls, tracks stable state novelty, and emits replayable evidence. Coverage-guided restart search, finding reproduction, exact-signature minimization, and equal-budget strategy benchmarks are available as first-class APIs and CLI workflows.

## Quick start

```sh
npm ci
npm run build
node dist/cli.js run --manifest fixtures/turn-counter.json --profile explore --artifacts artifacts/example --trust-target
node dist/cli.js run --manifest fixtures/crash-sequence.json --profile explore --max-actions 4 --artifacts artifacts/crash --trust-target
node dist/cli.js minimize --manifest fixtures/crash-sequence.json --replay artifacts/crash/replay.json --kind crash --trust-target
node dist/cli.js verify --manifest fixtures/crash-sequence.json --replay artifacts/crash/replay.json --signature <finding-signature> --trust-target
node dist/cli.js explore --manifest fixtures/hidden-route.json --episodes 10 --max-actions 3 --corpus artifacts/hidden-corpus.json --trust-target
node dist/cli.js benchmark --manifest fixtures/hidden-route.json --episodes 10 --max-actions 3 --seed 1 --artifacts artifacts/benchmark --trust-target
node dist/cli.js autonomy --manifest fixtures/resource-market.json --episodes 30 --max-actions 4 --artifacts artifacts/autonomy --trust-target
npm run soak
```

The manifest format is JSON in this first implementation. YAML support and richer game adapters are planned after the external runner is stable.

Single-run profiles include:

- `baseline`: bounded common-key smoke exploration;
- `explore`: deterministic action-diversity exploration with stable state metrics.

Use the separate `explore` command for persistent, coverage-guided prefix mutation and fresh-process restart scheduling. Use `benchmark` to compare it with round-robin and seeded-random policies under the same action budget.

## Intelligent autonomy

`autonomy` coordinates six deterministic roles over one shared world model:

- mechanic mapper;
- edge-case and timing attacker;
- secret hunter;
- speedrunner;
- completionist;
- recovery/confusion tester.

Each agent proposes bounded action sequences with an objective, score, machine-readable reasons, and expected semantic tags. The scheduler launches every selected proposal in a fresh process, then shares newly observed states, transitions, mechanics, milestones, completion paths, and hidden paths with all agents. The same target, seed, and evidence produce the same proposal order.

The deterministic semantic analyzer recognizes prompts, menu options, action hints, counters, and common terminal-game concepts. Target adapters can add authoritative milestone and mechanic evidence without making core depend on a particular game. Hosted model providers are a future optional integration; they will use the same interfaces and will not become executable oracles.

```ts
import { autonomousPlaytest, evaluateAutonomy } from '@wyrcan/playtestr';
import { createGamrPlaytestrTarget } from '@wyrcan/gamr/playtestr-adapter';

const { manifest, adapter } = createGamrPlaytestrTarget('blackout-grid', {
  cliPath: '/path/to/gamr/dist/cli.js',
});
const result = await autonomousPlaytest(manifest, { adapter, episodes: 30 });
const evaluation = evaluateAutonomy(result, {
  id: 'blackout-grid-progression',
  targetId: manifest.id,
  expectedMilestones: ['dispatch-briefing', 'operations-grid'],
});
```

Gamr supplies the adapter structurally; Playtestr has no Gamr package dependency.

Every run can atomically emit `report.json`, `replay.json`, and `last-screen.txt` under a manifest-controlled byte quota. Findings carry V1 signatures and evidence levels. `verify` establishes a reproduction quorum; `minimize` preserves that exact signature and independently verifies the result.

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
  "maxArtifactBytes": 10000000,
  "observation": {
    "volatilePatterns": ["TIME \\d+"]
  }
}
```

Relative `cwd` values resolve from the manifest directory; when omitted, the manifest directory is used. `env` sets explicit values and `inheritEnv` opts into additional host variable names. Do not put secrets directly in a committed manifest.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the release-gated roadmap and permanent Gamr boundary. The detailed autonomy execution plan is in [docs/plans/TERMINAL_AUTONOMY_EXECUTION_PLAN.md](docs/plans/TERMINAL_AUTONOMY_EXECUTION_PLAN.md). The concrete product definition is in [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md), the primary-source rationale is in [docs/RESEARCH.md](docs/RESEARCH.md), and the architecture is documented in [docs/architecture/overview.md](docs/architecture/overview.md).

The intelligent-agent contracts, evaluation suite, Gamr bridge, Docker gate, and graphical-backend roadmap are specified in [docs/plans/INTELLIGENT_AUTONOMY_PLAN.md](docs/plans/INTELLIGENT_AUTONOMY_PLAN.md).

## Current safety boundary

`local-pty` is a trusted-target backend, not a sandbox. On Unix it terminates the PTY process group; on Windows it currently uses the operating system's `taskkill /T /F` tree termination. A native Windows Job Object backend remains the stronger future isolation mechanism. Reports state backend capabilities and include cleanup confirmation so this boundary is visible rather than implied.

## Repository boundary

Gamr retains its in-process catalog regression tests. Playtestr owns the generic target manifest, PTY driver, replay format, agents, oracles, and reports. A future Gamr adapter will let Gamr games expose seeds, semantic events, goals, and invariants without making Playtestr depend on Gamr.
