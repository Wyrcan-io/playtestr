# Playtestr architecture

## Boundaries

Playtestr core owns target contracts, execution backends, terminal observations, search, oracles, replay, and evidence. Gamr owns games and game-specific semantics. An adapter may depend on both; neither core repository depends on the other.

```text
gamr <---- @wyrcan/gamr-playtest ----> playtestr
  ^                                      ^
  |                                      |
games and runtime                 generic test engine
```

## Layers

```text
CLI / library API
      |
episode runner ---- budgets ---- lifecycle outcome
      |
search scheduler ---- policy ---- corpus
      |                            |
execution backend ---- terminal ---- observations
      |
oracles ---- signatures ---- verifier ---- minimizer
      |
versioned evidence artifacts
```

Dependencies point downward. Policies propose bounded actions; they do not launch commands or declare bugs. Oracles inspect canonical observations/events; they do not steer the game. Reports serialize evidence; they do not invent conclusions.

## Execution backends

`local-pty` launches a trusted local process with the caller's operating-system permissions. It filters ambient environment variables, enforces runner budgets, and attempts process cleanup, but it is not a security sandbox.

Windows currently pins `node-pty@1.2.0-beta.14` because it contains the upstream ConPTY helper fix. A guarded compatibility shim closes an input pipe that the public API leaves open. The 100-run natural-exit soak checks that no native handles remain; upgrading node-pty requires rerunning that gate and removing the shim when upstream exposes complete cleanup.

The future `isolated` backend runs untrusted targets in disposable workers with explicit filesystem, network, identity, process, CPU, memory, and artifact policies. Backend capabilities are reported so a result never implies controls that were not active.

## Episode lifecycle

```text
created -> starting -> running -> target-terminated
                    \-> runner-truncated
                    \-> infrastructure-failed
```

Target termination means the game reached an exit condition. Runner truncation means an external budget or policy stopped an otherwise live episode. Infrastructure failure means Playtestr itself could not execute the contract. These outcomes remain distinct in reports and metrics.

## State and transition model

An exact fingerprint includes normalized screen, terminal mode, viewport, and cursor. A structural fingerprint excludes intentionally volatile details configured by the target. A transition key is `(previous structural state, action, next structural state)`. Corpus entries retain the action prefix and compatibility metadata needed to replay the discovery.

Observable novelty is a search signal only. Mechanic coverage requires an adapter-declared mechanic/event or an explicit black-box oracle.

## Adapter model

Adapters use a reset/step/close environment contract with separate `terminated` and `truncated` values. They may provide legal actions, semantic observations, events, goals, invariants, checkpoints, and stable hashes. Adapter errors are infrastructure findings, never game findings.

## Schema policy

Every persisted manifest, replay, report, corpus, and finding format has an integer schema version. Readers reject unsupported versions with a controlled error. A schema change requires fixtures, tests, and migration notes; adding an optional field alone does not justify silently changing semantics.
