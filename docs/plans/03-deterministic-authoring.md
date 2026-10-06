# 03 — Deterministic recording and authoring

Execution update 7 October 2026: source `record` implemented with existing strict v1/v2; actual controls, review/replay/export and maintenance are documented in [recording](../recording.md), with [generated examples](../../examples/recorded/README.md). Native/hosted acceptance is tracked in [the dated record](../validation/p0-p2-2026-10-07.md); prior published binaries are unchanged. [Journeys](02-customer-journeys.md) · [Quality](10-quality-and-release.md).

## Fundamental contract

Recording captures what a developer does; assertions encode what they expect. The author supplies the correctness criterion. Capture alone cannot discover all important behavior or validate that the captured behavior is correct.

The recorder produces ordinary readable, editable test files and candidate text snapshots. Replaying a test uses the same runner locally and in CI; it does not require an account, network connection, proprietary recording format or hosted session.

## Planned authoring stages

1. **Setup:** executable plus arguments, target cwd, fixture, dimensions, environment allowlist, budget and output cap. Show resolved paths before launch. Launch only explicitly trusted applications.
2. **Capture:** bounded ordered input events and target screen state through the existing terminal/session interface. Keep typed text in memory until explicit reviewed export. Do not capture the user's surrounding shell session.
3. **Checkpoint:** author marks text appearance/disappearance, exact expected exit, or a snapshot of a known-ready screen. A snapshot still requires meaningful readiness evidence.
4. **Review:** display generated steps, sensitive-data warning based on actual captured fields, candidate baselines, dynamic fields and unresolved waits. No silent acceptance.
5. **Replay validation:** fresh state, no recorded wall-clock sleeps by default; condition-based waits and bounded deadlines. Preserve the first failure.
6. **Export:** atomic write of approved files; no overwrite of existing reviewed baselines without selected confirmation. Failed/cancelled recordings do not leave partly accepted suites.

P1 first slice: keyboard/text capture plus explicit text/exit checkpoints for one wizard. Add full-screen recording, resize and edit controls only after that slice proves the flow. Recorder-control keystrokes must be configurable or out-of-band; test collisions and literal transmission to the target.

## Readiness design

Captured timing may inform a suggested timeout but cannot become the correctness oracle. Use expected content that identifies the new state after each relevant input. Existing quiet-screen settling remains supplementary, never positive proof of readiness.

A deterministic heuristic may propose stable text from observed screens; mark it as a suggestion. Require review, reject empty/stale/ambiguous anchors, and replay under delay variation. If no useful anchor exists, leave an explicit authoring problem rather than inventing a sleep that makes the sample pass.

Avoid broad matching that permits the wrong menu item or old success text. For disappearance checks, retain the requirement that the previous state was observed. Exit-only tools can assert exact code and final output when meaningful. Long-running TUIs need a checkpoint plus bounded teardown, not a fabricated natural exit.

## State and fixture handling

Reuse v2 workspace boundaries. A fixture should be small, synthetic, reviewed and copied fresh. Control selected home/temp paths, locale and environment deliberately. Do not copy real user home directories, tokens, SSH keys or production databases.

Separate target executable resolution, runtime dependencies and fixture cwd. Generated tests should be relocatable within the repository, including spaces and Unicode paths. Never infer a shell command from joined arguments.

State assertions need a defined lifecycle. Preferred launch approach: documented existing harness checks while the managed fixture still exists, or a narrowly specified postcondition hook only if current mechanisms cannot express the admitted cases. Define access, failure, timeout, output bounds and cleanup ordering before adding such a hook. A retained failed workspace is not the default passing-state assertion strategy.

For timestamps, random IDs or paths: deterministic fixture/clock/application options first. Optional normalization must be narrow, explicit and visible in review, with a control proving a meaningful nearby defect still fails. No automatic deletion of every changing line.

## Proposed event/export semantics

| Event | Export expectation | Failure behavior |
| --- | --- | --- |
| Printable typing/paste | Bounded text action, preserving intended characters | Unsupported encoding or oversized paste rejected clearly |
| Supported named key | Existing key action | Unsupported key logged as unresolved, not silently dropped |
| Resize | Existing dimensions and redraw/readiness contract | Invalid size rejected; no assumed target redraw |
| Checkpoint text | Explicit expect/expect-not | Ambiguous/empty checkpoint cannot be marked reviewed |
| Snapshot | Named candidate plus readiness proof | Unready/noisy screen produces actionable authoring state |
| Exit | Exact expected code | Unexpected exit classified separately from timeout |
| Recorder cancel | No approved export; bounded cleanup | Cleanup failure retained separately |

Do not add mouse, arbitrary escape sequences, style assertions or broad Unicode guarantees merely because capture can observe them. Use the campaign to identify necessary, bounded launch gaps. Unsupported interactions must be visible before presenting the generated test as runnable.

## Format and implementation decisions

Prefer exporting existing spec v1/v2 for representable behavior. Recorder draft metadata can use a separate versioned local format if necessary; do not insert unknown fields into strict public specs. New assertions need schema, parser, examples, report rendering and migration changes together. Assign exact format numbers only after auditing the current schemas.

Go owns the recorder and engine. Reuse PTY cleanup, output limits and synchronization; do not create a second terminal implementation. Input forwarding, recorder controls and target output need explicit goroutine shutdown. Cancellation must restore the operator's terminal mode even after errors.

## Acceptance

- Native Linux amd64, Windows amd64 and macOS arm64 paths run, subject to the actual selected support contract.
- Generated wizard, selector, full-screen, resize and stateful examples pass fresh replay and detect intended target defects.
- At least ten fresh replays per selected development example with delay variation, first failures retained; final campaign thresholds are in 08/10.
- Unsupported input, no readiness, duplicate snapshot names, dirty fixture, invalid path, interrupted export, target crash/hang/flood, Ctrl+C and descendant cleanup all have bounded accurate results.
- Recorder leaves no secret-bearing raw recording file by default; reviewed exports are inspectable before commit. A target can still print secrets, so no universal secret-redaction claim.
- Before/after target defects test actual behavior, not merely a deliberately wrong expected string.
- Round-trip generated spec can be edited manually and rerun without the recorder.
- Documentation states what must be chosen by a human and what remains uncovered.
