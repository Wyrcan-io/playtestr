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

Linux on run `42455300421` passed all 250 upstream tests, built Taskell and Playtestr, and passed the six-step authored synthetic-board smoke with exact exit 0, saved-state bytes, process-tree termination and workspace cleanup. The same job reached recorder review using valid quoted text controls, captured a fresh candidate and state, then cancelled with exit 130 as the workflow specified. It did not replay or export; the candidate is not yet a frozen contract. Receipt `build-attempt-v17.json` records the limited result. The run's macOS Intel job remains in upstream tests at the latest status check. Dependency resolution on macOS arm64 remains a separate preflight, not a build claim. No Taskell scenario, native cell, fault calibration, or admission is yet established.

The prior Skim cleanup receipt predated a later local target tree. Its exact ownership marker, acquisition record, and pinned source were restored from the retained archive and verified against all 819 provenance entries. Two local case-report event triplets were copied byte-identically and hash-verified in `skim/local-residual-case-evidence-v1`. A fresh native Windows PID inspection and an immediate pre-delete target revalidation passed; the exact 854-file / 213,911,372-byte tree was removed via the checked PowerShell path. Preparation and removal evidence is in `skim/local-residual-cleanup-v1-{prepared,removed}.json`. Fresh campaign storage observation passes with Taskell as the sole active target. The narrow evidence-reader change accepts a UTF-8 BOM in a process proof and retains all other identity and inventory checks.

The Linux job on `42456298245` passed the same pinned 250-test suite and native
build, repeated the authored smoke, then completed the public recorder route:
review, fresh replay (6/6), JSON export, and ordinary `playtestr test` (1/1,
6/6 steps). Both reports show exact exit 0, saved Markdown bytes, process-group
termination, and workspace cleanup. The exported spec, both reports, recorder
console and control inputs, fixture, runner and host identity receipts are
retained in `first-use-attempts/42456298245-linux-first-use.tar.gz` with a
member hash manifest. Receipt `build-attempt-v18.json` binds the provider
artifact and target/runner binary hashes. MacOS Intel on that run remains in
the upstream test phase; Linux alone does not establish a native cell or
admission.

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

Run `42451800719` later completed both hosts: each passed 250 tests, built
Taskell and Playtestr, and configured Go 1.25.0, then rejected the same
repo-prefixed fixture path before launching Taskell. Both artifact digests are
in `build-attempt-v12.json`. Run `42452701639` contains the corrected
spec-relative fixture.

Ubuntu on run `42452701639` passed the 250 upstream tests, built both
executables, launched Taskell and passed the initial screen checks. It then
failed the authored state checkpoint before sending `q`: the post-space
`Review sample` assertion matched the unchanged initial text immediately
(0 ms), and the same-execution state read was premature. The actual report and
screen are retained in `first-use-attempts/first-use-attempts-v1.tar.gz` under
`42452701639-linux/`; Playtestr
confirmed process-group termination and workspace cleanup. This is an
authoring/timing failure, not evidence of a Taskell defect. The case now sends
`q`, requires exact exit 0, then checks saved bytes after exit. MacOS for that
run was still compiling at this update; the corrected case is next.

The Linux leg of run `42453888286` then passed the authored smoke: all six
steps, exact exit 0, saved-state bytes, process-tree cleanup and workspace
cleanup. Its report and binary identities are retained under
`first-use-attempts/first-use-attempts-v1.tar.gz` under `42453888286-linux/`.
The following no-JSON recorder step
failed before target launch because that separate workflow step omitted the
Taskell binary directory from `PATH`; `build-attempt-v14.json` records this
split result. Pinned `PATH` export is now included for the next native run.
MacOS on `42453888286` was still in upstream tests when recorded.

MacOS Intel on run `42452701639` later reproduced the same premature state
checkpoint failure. Its actual report and screen are in
`first-use-attempts/first-use-attempts-v1.tar.gz` under `42452701639-macos/`,
with toolchain and binary identities
in `build-attempt-v15.json`. Both old-host cases are preserved; the first
post-exit authored smoke result is Linux-only at this point.

Both native jobs on run `42456298245` have now completed successfully. Ubuntu
24.04 and macOS 15 Intel each passed all 250 pinned upstream tests, built
Taskell 1.11.4 and Playtestr, passed the six-step authored smoke, and completed
recorder review, fresh replay, export and ordinary test (6/6; 1/1 case).
Same-run reports record exact exit 0, saved state, process-group termination
and workspace cleanup. Linux and macOS first-use packets are retained in
`first-use-attempts/42456298245-linux-first-use.tar.gz` and
`first-use-attempts/42456298245-macos-first-use.tar.gz`; receipts are
`build-attempt-v18.json` and `build-attempt-v19.json`. This establishes a
successful two-host first-use observation only. It is not the frozen scenario
catalog, complete native cells, fault calibration, or admission.

## Candidate interaction readback (2026-11-08)

Run `42467040351` passed the existing-board smoke and candidate create/duplicate
specs on Ubuntu 24.04 and Intel macOS. The creation case confirms the source
read: Enter stores the task and creates a blank insert row; Escape runs
`finishTask`, removes that row, and returns to normal mode; `q` then exits with
code 0. Exact expected Markdown bytes, reports, process cleanup and workspace
cleanup matched on both hosts. The duplicate case likewise preserves the
neighbors and serializes the extra row exactly once on both hosts. These are
single observations, not native-series or admission evidence; see
`build-attempt-v24.json`.

For candidate N04, `startEdit` initializes the field from the current task
text with its cursor at the end (`textToField`), and the field handler maps
Backspace to deletion immediately before the cursor. Therefore the prepared
rename case sends nine Backspace keys to clear the fixture title `Rename me`
before entering the replacement. This is source-grounded but still requires
settled-screen and exact-state validation on both hosts.

## N05 reorder source grounding

The pinned `templates/bindings.ini` binds `moveDown` to `J`. `Taskell.Events.Actions.Normal.events` maps `MoveDown` to `down`, `Taskell.Events.State.down` calls `moveVertical 1`, and `Taskell.Data.List.move` performs the bounded task-sequence shift. Candidate fixture `fixtures/reorder/board.md` starts with two unique adjacent rows; the N05 same-run state oracle requires their exact order to swap once. N05 has not yet run on a native host.

## N06-N08 source grounding (candidates not yet run)

N06 uses the pinned `L` binding for `MoveRightBottom`, which the normal event map sends through `moveRightBottom` to `moveHorizontal 1 Lists.Bottom`; the oracle expects one item appended to the next list. N07 uses `/` search and the default Space completion action; completion calls `moveToLastBottom` and the oracle checks the unique searched task moves to Done. N08 uses `N` (`ListNew`); the pinned Insert handler commits the new list on Enter and immediately opens task insertion, so the candidate types a task directly, commits it, escapes the blank row and checks exact Markdown. These are source-backed candidate routes, not native observations.
