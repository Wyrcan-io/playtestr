# Playtestr architecture

```text
target manifest
      |
launcher + process/PTY lifecycle
      |
VT driver -> terminal observation -> stable fingerprint
      |
agent policy -> action -> replay corpus
      |
oracles -> finding -> minimizer -> evidence artifact
```

## Core layers

The target layer knows how to start a program and apply seed configuration. The terminal layer knows how to send bytes and parse VT output. The runner applies budgets and records an episode. Agents propose actions but do not decide whether a bug is real. Oracles produce executable findings. The corpus stores interesting action prefixes, and the minimizer reduces a reproducing sequence.

## Product boundary

Gamr owns games, built-in game profiles, and deep adapters for its own mechanics. Playtestr owns generic terminal execution, exploration, replay, evidence, and optional adapter contracts. The core package must not import Gamr.

## Evidence model

Every episode has:

- target command and arguments;
- viewport and seed;
- ordered actions with hold/wait timing;
- observations and stable fingerprints;
- findings and their action positions;
- the final screen;
- tool and schema versions.

Screen novelty is a search signal. It is not a claim that every hidden mechanic was tested.
