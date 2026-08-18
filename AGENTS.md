# Playtestr repository instructions

## Purpose

Playtestr is a standalone black-box playtesting toolkit for terminal games. It launches a target in a pseudo-terminal, observes the VT screen, sends bounded input, evaluates executable oracles, and produces replayable evidence.

## Working rules

- Keep Playtestr independent from Gamr. Gamr-specific behavior belongs in an adapter package, not in core.
- Preserve the terminal contract: PTY input, VT output, viewport size, timing, process lifecycle, and replay metadata are public behavior.
- Prefer deterministic, replayable algorithms in core. LLMs and network providers must be optional integrations.
- Every finding needs evidence: a replay, seed, target metadata, observation, or executable oracle result.
- Never let a target inherit secrets or unrestricted host access by default. Treat arbitrary game commands as untrusted.
- Do not claim total coverage from black-box screen exploration. Report observed state/action novelty separately from internal code or mechanic coverage.

## Commands

```sh
npm ci
npm run typecheck
npm test
npm run build
node dist/cli.js run --manifest fixtures/turn-counter.json --artifacts artifacts/example
```

## Architecture boundaries

- `src/types.ts`: public contracts and report schema.
- `src/terminal.ts`: PTY and VT lifecycle only.
- `src/runner.ts`: episode orchestration and budgets.
- `src/agents.ts`: input policies; policies must remain bounded and side-effect free outside the target.
- `src/oracles.ts`: executable failure checks.
- `src/observations.ts`, `src/corpus.ts`, `src/minimize.ts`: exploration evidence and replay reduction.
- `fixtures/`: deterministic targets used by tests.
- `docs/`: design, operations, and roadmap material.

## Change discipline

For changes to the replay or report schema, update the versioned types, fixtures, tests, and migration notes together. For changes to PTY cleanup, test both a target that exits normally and a target that must be force-stopped.
