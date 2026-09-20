# Sprint delivery record and current roadmap

The root [roadmap](../roadmap.md) is authoritative for completed releases, current status and the execution sequence. The sections below preserve Sprints 0–9 engineering history; their dated platform statements are historical, not current aggregate support claims. Current evidence lives in [platform support](platform-support.md).

The next work is early Sprint 13 native-gap triage and five Sprint 11 pilots, followed by selected compatibility/authoring/handoff changes, integrated hardening, corpus depth, candidate freeze, frozen-byte qualification, demos and R6 publication/verification. Maintainer adoption begins only afterward. The root roadmap owns exact checkpoint order; [planning documents](plans/README.md) define execution details. All new campaign counts are targets, not completed results.

## Working agreement

Develop one observable behavior at a time. State the intended outcome, implement a small change, run relevant success and failure checks, then provide a manual demo command and result. Stop at the sprint boundary for user testing and feedback unless the user asks to continue. Keep unrelated enhancements in the backlog. A sprint is an acceptance milestone, not a fixed calendar estimate or a large batch of code.

Tests that exercise process behavior should use real PTYs and deterministic fixtures. Unit tests cover parsing and pure screen transformations. Do not substitute mocks for proof of PTY lifecycle behavior. Never describe a configured CI matrix as a passing matrix until it has actually run.

## MVP promise

A developer can run a trusted interactive CLI, drive its keyboard flow, assert the rendered screen and expected exit status, compare a reviewed text snapshot, and receive a useful failure artifact and nonzero runner exit status. The test completes within its budgets and cleans up the processes it launched on supported platforms.

Out of scope: cloud accounts, billing, PR bots, autonomous agents, game mechanics, browser/desktop game testing, styled visual regression, GIF recording, parallel scheduling, and multiple SDKs.

## Sprint 0 — baseline and decisions (implemented locally)

- Connect this folder to the new GitHub repository.
- Select the implementation language and record the tradeoffs.
- Preserve the existing interactive menu and six-step spec as the baseline.
- Verify the baseline build, unit tests, and menu snapshot locally.

Acceptance: `go run ./cmd/playtestr test examples/menu.json` passes against the built demo. Windows was previously exercised through ConPTY. Linux/macOS execution and remote CI are still unverified. Current code is a prototype, not the complete MVP.

## Sprint 1 — correct process outcomes (implemented locally)

User-visible result: a CLI that exits unexpectedly cannot be mistaken for a passing test.

An explicit expected-exit step preserves process status and distinguishes a process failure from a missing-text timeout. An intentionally nonzero exit passes only when that exact code is declared. A process already observed to exit without an exit assertion fails; finite commands should end their specs with an exit assertion.

Acceptance: fixtures for exit 0, exit nonzero, text followed by a crash, and waiting for an exit that never happens. Retain the existing menu test. Each failure must return a nonzero runner status with the failing step and reason. Settle how an intentionally nonzero expected exit interacts with assertions before implementation.

## Sprint 2 — bounded sessions and cleanup (implemented locally)

User-visible result: a silent, hung, or output-flooding target ends predictably and leaves no launched target tree behind.

The terminal session now owns PTY I/O, process outcome, VT state, bounded final-output draining, output accounting, and idempotent cleanup. Specs support per-step, total-run, optional visible-startup, and raw-output limits. Ctrl+C cancellation stops the active spec and prevents later specs from starting.

Windows cleanup uses a Job Object and Unix cleanup uses a dedicated process group. Windows attachment happens immediately after xpty starts the target because the dependency does not expose a suspended-start hook; a child created in that narrow interval can escape the job. Unix children that deliberately create a new session can escape the original group. These are documented trusted-target boundaries.

`cwd`, `env`, and `inherit_env` make target launch configuration explicit. Relative working directories resolve from the spec directory. Ambient inheritance is restricted to an operational platform allowlist plus names selected by the spec.

Acceptance evidence: real-PTY tests cover natural exit, forced shutdown, no output, output flood, cancellation, blocked input, parent/child cleanup after a parent hang and natural parent exit, idempotent stop, environment filtering, working-directory resolution, and five bounded repeated sessions. Windows has been exercised locally; remote Linux and macOS execution remains unverified.

## Sprint 3 — useful screen regressions (implemented locally)

User-visible result: an intentional UI regression produces a readable expected/actual text diff.

Snapshot mismatches now print a bounded unified text diff and save expected/actual diff evidence alongside the captured screen. Baseline reads, diff output, and artifacts are bounded. Snapshot updates are staged until the spec and cleanup succeed; a selector can update one named baseline while all other snapshots continue to compare.

Snapshot readiness is explicit: an `expect` must succeed after the latest input or resize, or an exit assertion must succeed, before a snapshot can run. The existing quiet period settles a completed redraw but is not treated as readiness evidence.

Focused fixtures cover delayed redraw settling, carriage-return redraws, cursor movement and erasing, escape sequences split across writes, UTF-8 characters split across reads, basic Unicode text, alternate-screen entry and restoration, and PTY plus emulator resize. Playtestr buffers incomplete UTF-8 at its emulator boundary because vt10x otherwise drops a split code point.

Acceptance evidence: clean baselines pass; changed, added, and removed lines produce a readable diff; mismatch artifacts use the same captured screen; missing and oversized baselines fail distinctly; cancellation and later assertion failure do not commit staged updates; explicit update changes only the selected baseline; targets observe both larger and smaller viewport sizes. The emulator evaluation and unsupported behavior are documented in `docs/terminal-compatibility.md`.

## Sprint 4 — MVP packaging and external trial (implemented locally)

User-visible result: another developer can install a release binary and test an actual CLI from its README instructions.

Version the spec and machine-readable report, include target/viewport/step metadata and failure screens, exercise the GitHub Actions matrix, and trial an existing external TUI in addition to our fixtures. Choose the oldest Go version actually supported by the code and pinned dependencies before publishing installation instructions. Choose the project license before the first release.

Acceptance: recorded Linux/macOS/Windows CI results for advertised platforms, a deliberately failing CI example with downloadable evidence, and a successful user walkthrough. Unsupported platforms stay explicitly unsupported rather than being inferred from cross-compilation.

Implemented: required spec version 1 and canonical JSON Schema; structured runner outcomes; atomic machine report version 1 and schema; bounded transactional snapshot updates; an external Charm Gum `v0.17.0` trial; Go 1.25 minimum-version verification; Apache 2.0 licensing; version injection; native ZIP/tar.gz packaging with SHA-256 files; and a release-candidate workflow for Linux amd64, macOS arm64, and Windows amd64. The Windows packaged-binary walkthrough, full test suite, vet, race detector, expected-failure evidence, external trial, and checksum verification pass locally.

Remote acceptance: commit `bcd1b6e` passed the complete native terminal-test matrix on Ubuntu amd64, macOS arm64, and Windows amd64. Each job ran the pinned external Gum test, proved that the deliberate regression failed, and uploaded its JSON report, screen, and diff. Historical packaging run `34048585717` built and exercised binaries before packaging on all three targets. Release run `34052977944` later verified checksums and archive members, extracted each archive, and exercised the exact packaged binaries before publishing `v0.1.0-rc.1`. The recorded evidence and scope are listed in [Platform support](platform-support.md).

## Sprint 5 — deterministic suites and CI evidence (implemented locally)

User-visible result: a developer can preview and run a directory of `.json` specs serially, receive a complete suite summary, and place failure evidence in a collision-safe directory unique to that invocation.

Explicit paths retain their order. Directory matches are recursively sorted and deduplicated without following directory symlinks. Selection, aggregate step metadata, and outputs are bounded and checked before launch. Ctrl+C retains status 130 while accounting for the active and remaining specs. Report v1 remains unchanged.

Local Windows evidence covers directory listing, real-PTY execution, ordinary failure continuation, expected nonzero exit, cancellation, duplicate basenames, stale evidence, alias rejection, filesystem failures, and resource caps. JUnit, globs, and filters were omitted because the available acceptance project did not demonstrate those needs. See [Test suites and CI evidence](suites.md) and the [engineering validation record](validation/sprint-5-engineering-2026-09-15.md). Independent participant-owned CI acceptance remains open and is not replaced by operator evidence.

## Sprint 7 — offline failure diagnosis (implemented locally)

User-visible result: `playtestr report` renders an existing report-v1 document
and admitted screen/diff evidence into one atomic, self-contained HTML file.
The failure-first view separates target exit, cleanup, and evidence-write
outcomes; labels missing or unavailable data; remains usable without JavaScript
or a server; and does not launch the target, read specs, update baselines, or
infer a cause.

The renderer strictly bounds JSON, per-file and aggregate evidence, result/step
counts, and generated output. It rejects traversal, absolute/remote/network
references, escaping links and Windows junctions, inconsistent/shared evidence,
and input/evidence output aliases. Browser checks cover narrow and desktop
layouts, keyboard entry, contrast, terminal/diff readability, no-script use,
accessibility names, literal hostile content, and zero external requests.

Local Windows engineering acceptance, the two diagnosis cases, and a real
same-spec pass/regression/recovery demo are recorded in [Sprint 7 engineering
validation](validation/sprint-7-engineering-2026-09-18.md). The command shipped
in the checksum-verified `v0.3.0-rc.1` prerelease and passed published-install
checks on every advertised host. Independent maintainer adoption and outside
feedback are deferred until A1, after the complete engineering batch and R6 by product decision.

## Sprint 8 — exact CI installation (implemented locally)

User-visible result: a setup-only GitHub Action installs one exact published
runner on an advertised host, verifies its checksum and archive layout, checks
the binary by absolute path, and only then makes that version available to the
next workflow step.

The action and runner use independent pins. Downloads, retries, time, archive
and checksum sizes, archive membership, staging, and failure cleanup are
bounded. Linux amd64, macOS arm64, and Windows amd64 are the only mapped release
assets. Direct archive installation remains the fallback; target setup, test
execution, baseline review, and artifact upload remain explicit workflow work.

Local Windows normal and failure coverage, the route evidence, and maintenance
contract are recorded in [Sprint 8 engineering validation](validation/sprint-8-engineering-2026-09-18.md).
The first immutable public action revision, native Linux/macOS action results,
a later real-release upgrade, and independent adoption remain open. Maintainer
adoption and outside feedback are deferred until A1, after the complete engineering batch and R6.

## Sprint 9 — repeatable workspaces (implemented locally)

User-visible result: a spec-v2 test receives a unique bounded copy of a reviewed
fixture, an explicit working directory, and optional managed home/temp paths.
The runner resolves the trusted executable before changing directories, stops
the process tree before deleting files, preserves evidence outside the owned
root, and can explicitly retain failed state for inspection.

Spec and report v1 remain unchanged. Workspace results use strict spec/report
v2 schemas and distinct setup/cleanup outcomes; mixed suites emit report v2.
Copy and deletion bounds, link/junction rejection, marker-verified cleanup,
snapshot rollback, stateful repetition, cancellation, timeout, flood, expected
nonzero exit, and descendant cleanup have local native coverage. See
[Repeatable workspaces](workspaces.md) and the [Sprint 9 engineering record](validation/sprint-9-engineering-2026-09-19.md).

The internal Lazygit R3-T09 persisted-draft observation selects the engineering
case but is not independent adoption. Maintainer adoption/outside feedback remains deferred to A1 after engineering and R6. Non-Windows native confirmation is required during Sprint 13 before release qualification.

## Current development plans

- [Sprint 10: selected terminal compatibility](plans/sprints/10-terminal-compatibility.md).
- [Sprint 11: real-project corpus](plans/sprints/11-real-project-corpus.md), with baseline and completion phases.
- [Sprint 12: authoring and one conditional extension](plans/sprints/12-authoring-and-focused-assertions.md).
- [Sprint 13: native CI and release hardening](plans/sprints/13-native-ci-and-release-hardening.md).
- [Sprint 14: reproducible demos and release kit](plans/sprints/14-demos-and-release-kit.md).
- [R6: release qualification](plans/release/06-qualified-release.md), followed by [A1 adoption](plans/release/07-maintainer-adoption.md).

Sprint 6 remains conditional; a documented rerun may solve the task without a new manifest. Historical sprint identifiers are retained for links. Optional ideas do not extend the pre-adoption batch automatically. See [product focus](plans/product-focus.md) for the feature budget and [current research](research/competitive-user-survey-2026-09-19.md) for the evidence behind priorities.
