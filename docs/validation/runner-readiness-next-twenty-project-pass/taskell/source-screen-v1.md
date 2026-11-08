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

The `.travis.yml` downloads a Stack binary from Stackage, installs dependencies, then runs `stack test`. It will not be executed as a repository hook. `.bin/build` is a release script: it stashes changes, runs `git push --all` and `git push --tags`, deletes/creates release paths, uses Docker, opens a browser, uploads to Hackage, changes Homebrew formulae, and launches the program. It is expressly excluded. `.bin/analytics` runs `brew info`; it is excluded. `.envrc` only adds `.bin` to `PATH` and will not be sourced. A source-pinned dependency-resolution packet now exists for Linux x86-64 and macOS arm64: each resolved 158 packages with equal versions and edges, and the preserved packets include the exact lock and snapshot inputs. The graph contains BSD/MIT dependencies plus two Apache-2.0 packages, one ISC package, and 23 GHC-provided/base entries with no license field in Stack's output. Explicit native Stack build/test and executable identity runs are the next gate; resolution is not build evidence.

Taskell is a deterministic local Markdown Kanban application when invoked with an explicit board path. The README documents `taskell <filename>.md`, prompt-to-create behavior, Markdown storage and keyboard movement; config supports an explicit XDG path. Campaign fixtures will use synthetic boards, isolated HOME/XDG variables, and no Trello/GitHub tokens or network-backed imports. Candidate cases should assert rendered task/column state and saved Markdown bytes after controlled UI actions.

## Current disposition

## Post-screen progress (2026-11-08)

The pinned production/test dependency graph resolved successfully on Linux x86-64 and macOS arm64 and is retained in `dependency-resolution-v1/`. It contains 158 packages. The graph metadata reports 130 BSD-3-family, 27 MIT, two Apache-2.0, one ISC and 23 compiler/base packages without a license field; those 23 are GHC-provided entries and need accurate attribution review rather than a third-party license guess.

Linux x86-64 built Taskell with the pinned resolver compiler and passed all 250 upstream tests on run `42448622006`. A later run (`42448762334`) passed the same 250 tests and built on both Linux x86-64 and macOS Intel x86-64. The Mac build emitted Clang's case-only generated-header include warning and linker atom-alignment warnings from GHC's bundled libCffi; neither prevented the tests or build. Both lanes then invoked unsupported `--version`, which Taskell treated as a board filename and answered with its create-file prompt. These failed invocations are preserved in `build-attempt-v1.json` and `build-attempt-v3.json`; they are not successful full-screen workflows. A later authored smoke spec was rejected by Playtestr before target launch because it declared named key `Space`; spec v1 requires literal text for a space. The rejected attempt is preserved in `build-attempt-v2.json`, and the case and recorder controls now send literal space text.

Current native Stack build/test and Taskell UI attempts are still in progress on Ubuntu and macOS Intel. The corrected lane uses `-v`, runs the authored synthetic-board state smoke, then captures a no-handwritten-JSON recorder preview for operator inspection. Dependency resolution on macOS arm64 is not a build claim; the build lane's macOS evidence is specifically Intel. No target workflow or Taskell admission is yet established.

The prior Skim cleanup receipt predated a later local target tree. Its exact ownership marker, acquisition record, and pinned source were restored from the retained archive and verified against all 819 provenance entries. Two local case-report event triplets were copied byte-identically and hash-verified in `skim/local-residual-case-evidence-v1`. A fresh native Windows PID inspection and an immediate pre-delete target revalidation passed; the exact 854-file / 213,911,372-byte tree was removed via the checked PowerShell path. Preparation and removal evidence is in `skim/local-residual-cleanup-v1-{prepared,removed}.json`. Fresh campaign storage observation passes with Taskell as the sole active target. The narrow evidence-reader change accepts a UTF-8 BOM in a process proof and retains all other identity and inventory checks.

## Hosted follow-up (2026-11-08)

Run `42449961171` (source `9e1ebc3`) passed all 250 upstream tests and built
Taskell 1.11.4 plus Playtestr on Ubuntu 24.04. Its authored first-use spec was
rejected before target launch because single-character `q` was incorrectly
declared as a named key; the retained artifact is `build-attempt-v5.json`.
The run's Intel macOS test job was still active when that immutable receipt was
written. The smoke spec now sends `q` as text. Recorder controls likewise send
literal space and `q` as text. Corrected cross-host workflow run
`42450896413` is active at source `e3bdaa0`; no outcome is claimed until both
native jobs finish and their reports/artifacts are inspected.

Run `42449961171` later completed on both hosts. MacOS Intel also passed all
250 upstream tests and built Taskell 1.11.4, but stopped before building the
Playtestr runner because `go` was absent (`build-attempt-v6.json`). Its retained
artifact is 2,973,229 bytes with provider SHA-256
`1ed3f48d5d114fa00842167a73508c9e914d259b6ac0ef1c4e81567655ba8360`. The
workflow now installs the exact Go version from repository `go.mod` with pinned
`actions/setup-go`, then builds Playtestr and runs the authored smoke.

Run `42450896413` passed 250 tests and built Taskell and Playtestr on Ubuntu,
then failed before target launch because the authored fixture directory path
was invalid (`build-attempt-v7.json`; artifact digest and size are in that
receipt). The same run's macOS job was still building at receipt time. The
spec now points to the actual fixture directory and `board-basic.md`; workflow
push filters include first-use inputs so this correction runs natively.

Run `42451645308` verified pinned Go setup and built Playtestr on Ubuntu, then
failed before target launch with the same now-corrected fixture path
(`build-attempt-v8.json`; artifact digest is retained there). Its macOS lane
was still in upstream tests at receipt time. Run `42451800719` uses both the
corrected fixture and Go setup on source `2144fd69`; both native jobs are in
the pinned upstream test phase at the latest poll.

Run `42450896413` later completed. Its macOS Intel lane passed all 250 tests
and built Taskell 1.11.4, but lacked Go before Playtestr build; both host results
are in `build-attempt-v9.json`. Run `42451800719` remains the first one with
both prerequisite corrections.

On Linux, run `42451800719` passed the upstream suite and built both binaries,
then failed workspace setup because `workspace.fixture` is relative to the spec
directory, making the repository-prefixed path invalid. Receipt
`build-attempt-v10.json` retains the artifact digest. The fixture now uses the
spec-relative `fixtures` directory; the 250-test, build and host evidence from
the failed attempt remains separate.

Run `42451645308` later completed on both hosts: each passed 250 upstream
tests, built Taskell and Playtestr, and set up Go 1.25.0. Both then failed
before target launch on the same fixture-root path (`build-attempt-v11.json`).
Run `42452701639` uses the corrected `fixtures` path; its native outcomes are
still open.
