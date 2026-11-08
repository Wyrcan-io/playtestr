# Taskell pinned-source screen

## Identity

- Repository: `smallhadroncollider/taskell`
- Selected commit: `a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`
- Acquisition archive: SHA-256 `23804ef331022030aeb97da2c34b07828dfe68144ba71b5b431e4f22310853e9`
- Extracted source: 197 entries, 2,639,742 bytes; full per-file SHA-256 manifest is in the ignored `active/taskell/acquisition.json`.
- License: BSD-3-Clause (the pinned `LICENSE` includes the standard redistribution and attribution conditions).
- Proposed native cells: Linux and macOS, as declared during screening. No Windows cell is claimed.

## Review before build

`package.yaml` declares Taskell 1.11.4, Haskell library dependencies and the `taskell` executable. `Setup.hs` is the two-line `Distribution.Simple` default build entry point. `stack.yaml` selects `nightly-2021-07-14`, enables `allow-newer`, and adds `tz-0.1.3.5`; `stack.yaml.lock` pins that extra package and the snapshot digest. The full transitive package set still needs to be resolved and reviewed before a build is authorized.

The `.travis.yml` downloads a Stack binary from Stackage, installs dependencies, then runs `stack test`. It will not be executed as a repository hook. `.bin/build` is a release script: it stashes changes, runs `git push --all` and `git push --tags`, deletes/creates release paths, uses Docker, opens a browser, uploads to Hackage, changes Homebrew formulae, and launches the program. It is expressly excluded. `.bin/analytics` runs `brew info`; it is excluded. `.envrc` only adds `.bin` to `PATH` and will not be sourced. The selected build path is a reviewed, explicit Stack build/test invocation in campaign-owned directories on hosted native runners.

Taskell is a deterministic local Markdown Kanban application when invoked with an explicit board path. The README documents `taskell <filename>.md`, prompt-to-create behavior, Markdown storage and keyboard movement; config supports an explicit XDG path. Campaign fixtures will use synthetic boards, isolated HOME/XDG variables, and no Trello/GitHub tokens or network-backed imports. Candidate cases should assert rendered task/column state and saved Markdown bytes after controlled UI actions.

## Current disposition

Source-only acquisition succeeded and no target build or execution has occurred. This is a pre-build screen, not a dependency approval or project admission. Next gates: inspect the pinned dependency resolution and build hooks; produce reviewed Linux/macOS build/runtime setup; conduct real first use and freeze the scenario/fault model before ordinary executions.

The prior Skim cleanup receipt predates a later local target tree, so it does not describe the current tree. Its exact ownership marker, acquisition record, and pinned source were restored from the retained archive and verified against all 819 provenance entries. A fresh Windows PID/birth inspection found no process using the owned path. The current tree has 35 non-source files; its two local case-report event triplets were copied byte-identically and hash-verified in `skim/local-residual-case-evidence-v1`. No target files have been deleted. The narrow evidence-reader change accepts a UTF-8 BOM in the process proof but does not bypass removal checks. Taskell source acquisition is project-path-exclusive; cleanup of the stale Skim target remains a prerequisite to Taskell build/execution.
