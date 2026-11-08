# Taskell pinned-source screen

## Identity

- Repository: `smallhadroncollider/taskell`
- Selected commit: `a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`
- Acquisition archive: SHA-256 `23804ef331022030aeb97da2c34b07828dfe68144ba71b5b431e4f22310853e9`
- Extracted source: 197 entries, 2,639,742 bytes; full per-file SHA-256 manifest is in the ignored `active/taskell/acquisition.json`.
- License: BSD-3-Clause (the pinned `LICENSE` includes the standard redistribution and attribution conditions).
- Proposed native cells: Linux and macOS, as declared during screening. No Windows cell is claimed.

## Review before build

`package.yaml` declares Taskell 1.11.4, Haskell library dependencies and the `taskell` executable. `Setup.hs` is the two-line `Distribution.Simple` default build entry point. `stack.yaml` selects `nightly-2021-07-14`, enables `allow-newer`, and adds `tz-0.1.3.5`; `stack.yaml.lock` pins that extra package and the snapshot digest. The exact Stackage snapshot was downloaded and verified at 555,978 bytes with SHA-256 `2005455f5d812ceb95560b708f006157533714bef631af52a3dd678d7dde32aa`; it declares 2,593 package records. The complete Taskell-specific transitive graph and package build metadata still need resolution and review before compilation.

The `.travis.yml` downloads a Stack binary from Stackage, installs dependencies, then runs `stack test`. It will not be executed as a repository hook. `.bin/build` is a release script: it stashes changes, runs `git push --all` and `git push --tags`, deletes/creates release paths, uses Docker, opens a browser, uploads to Hackage, changes Homebrew formulae, and launches the program. It is expressly excluded. `.bin/analytics` runs `brew info`; it is excluded. `.envrc` only adds `.bin` to `PATH` and will not be sourced. The selected build path is a reviewed, explicit Stack build/test invocation in campaign-owned directories on hosted native runners.

Taskell is a deterministic local Markdown Kanban application when invoked with an explicit board path. The README documents `taskell <filename>.md`, prompt-to-create behavior, Markdown storage and keyboard movement; config supports an explicit XDG path. Campaign fixtures will use synthetic boards, isolated HOME/XDG variables, and no Trello/GitHub tokens or network-backed imports. Candidate cases should assert rendered task/column state and saved Markdown bytes after controlled UI actions.

## Current disposition

Source-only acquisition succeeded and no target build or execution has occurred. This is a pre-build screen, not a dependency approval or project admission. Next gates: inspect the pinned dependency resolution and build hooks; produce reviewed Linux/macOS build/runtime setup; conduct real first use and freeze the scenario/fault model before ordinary executions.

The prior Skim cleanup receipt predated a later local target tree. Its exact ownership marker, acquisition record, and pinned source were restored from the retained archive and verified against all 819 provenance entries. Two local case-report event triplets were copied byte-identically and hash-verified in `skim/local-residual-case-evidence-v1`. A fresh native Windows PID inspection and an immediate pre-delete target revalidation passed; the exact 854-file / 213,911,372-byte tree was removed via the checked PowerShell path. Preparation and removal evidence is in `skim/local-residual-cleanup-v1-{prepared,removed}.json`. Fresh campaign storage observation passes with Taskell as the sole active target. The narrow evidence-reader change accepts a UTF-8 BOM in a process proof and retains all other identity and inventory checks.
