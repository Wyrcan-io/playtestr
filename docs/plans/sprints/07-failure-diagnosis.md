# Sprint 7: diagnose a failure from local evidence

Status: proposed. Commands, timeline data, and report views below are not implemented capabilities. This sprint builds on [Sprint 6](06-failure-reproduction.md); it does not replace the existing console output or report v1.

## User problem and outcome

A maintainer downloads a failed CI run and sees a timeout, final screen, and JSON. They still need to answer: which interaction failed, what assertion was pending, whether the target exited, whether the viewport changed, and whether cleanup succeeded. A final screen alone can hide the preceding transition.

The outcome is an offline report that answers those questions from captured evidence. The user can open it without a server, account, or the target application installed. Missing observations remain missing; the report must not invent why an application behaved a certain way.

## Entry evidence and success measure

Collect two diagnosis tasks from trials: preferably one assertion timeout and one snapshot mismatch or unexpected exit. Keep the actual report and reviewed, synthetic-data artifacts, plus the maintainer's steps to understand them. Establish how long it takes to locate the first failure and the relevant evidence with current tools.

Success requires another developer to identify the failing interaction, expected behavior, observed behavior, and cleanup result for both tasks using the report. Record time, assistance, and unresolved questions. With this small sample, report task results rather than claiming a general productivity percentage.

If final screens already answer both tasks, first improve their presentation. Add checkpoint capture only for the demonstrated missing transition; a continuous terminal recording is not a prerequisite.

## Scope

Required: a self-contained static HTML report generated locally; summary and per-spec failure detail; safe links or embedded copies of bounded evidence; an explicit timeline contract; optional checkpoint screens when the selected tasks require them; accessible text and keyboard navigation.

Excluded: live dashboards, remote asset loading, GIF/video export, raw ANSI playback, automatic root-cause diagnosis, automatic minimization, styled snapshots, and a target execution button. Opening a report never runs its original command.

The existing JSON report remains an automation interface. HTML is a view of captured outcomes, not a second outcome evaluator.

## Proposed workflow

```text
playtestr test --report artifacts/results.json --diagnostics artifacts/diagnostics.json tests/terminal
playtestr report --input artifacts/results.json --diagnostics artifacts/diagnostics.json --output artifacts/report.html
```

These are proposed commands. Rendering a report from existing report v1 without diagnostics must work; unavailable history is visibly labeled. The renderer accepts only supported format versions and never fetches references from the network.

The generated page starts with result counts, cancellation/incomplete-run state, and failures. A selected failure shows its spec identity, step, assertion kind, expected snapshot name where applicable, failure category, screen/diff, viewport, relevant event ordering, and separate cleanup outcome. Passing specs remain accessible without dominating the first view.

## Evidence contract

Use a separately versioned diagnostics sidecar with its own schema. Do not add unrecognized fields to report v1. Associate it with the report through a documented local identity mechanism, including spec identity and step indexes, and reject a mismatched pairing rather than displaying another run's history.

Record only observable lifecycle events: step started/completed, input submission completed or failed, assertion satisfied or failed, resize acknowledged, process exit observed, cancellation observed, cleanup started/completed, and evidence write failure. An input write completing does not prove the application handled it. A resize call completing does not prove a redraw completed. Quiet time is not readiness.

Use monotonic elapsed durations for ordering within a run. Wall-clock timestamps, if present, are descriptive and not the basis of ordering. Mark simultaneous/uncertain observation order honestly; never claim the exact instant the target made an internal decision.

Checkpoint screens are opt-in and event-based: for example after an assertion provides positive readiness and at the first failure. Capture a bounded, synchronized screen with its dimensions and step phase. Reuse the same captured failure screen for text evidence and HTML rather than sampling the terminal again and showing contradictory states.

### Resource budgets

Before implementation, confirm provisional limits against the two trial tasks:

- At most 10,000 timeline events per spec and 64 checkpoint screens per spec.
- At most 256 KiB per checkpoint, 8 MiB diagnostics data per spec, and 32 MiB for a generated HTML file.
- Existing spec, session output, snapshot, and report limits remain authoritative.
- Stream or budget suite aggregation so many passing specs do not allocate all possible checkpoint limits at once.

Exhausting an optional capture budget records omitted-event/frame counts and preserves core execution. Failure to write an explicitly requested artifact follows the established artifact-failure policy and cannot silently produce a passing result with missing promised evidence. The separate render command fails clearly when it cannot produce a valid bounded document; it never modifies the recorded test outcome.

## Privacy and safe rendering

Screens and diffs can contain application data. Enable richer capture explicitly, document the extra persistence, and use synthetic test data in public examples. Do not copy environment values, raw input text, arbitrary command arguments, or unrelated filesystem contents into diagnostics. Capture action kinds and indexes instead.

Automatic masking cannot promise to remove all sensitive terminal output. Keep ordinary privacy obligations explicit: a target must not print secrets into evidence intended for sharing; inspect artifacts before upload; any redaction is a visible transformation and cannot be used as proof of the original assertion. Existing failure screens are also sensitive, so the guidance applies to them.

Treat all report text, filenames, and terminal output as untrusted HTML input. Escape them as text; never interpret ANSI/OSC sequences as browser links or execute embedded HTML, JavaScript, or URLs. Use a self-contained page with no analytics, web fonts, CDN libraries, or external requests. Prefer static HTML and CSS; any necessary script must operate only on already embedded, escaped data.

Resolve artifact references within an explicit evidence root, reject traversal and escaping symlinks, and reject unsupported URI schemes. Do not read the user's arbitrary absolute paths merely because a downloaded report requests them. Show an unavailable-artifact entry when evidence was not provided.

Use readable contrast, visible focus, semantic headings, and textual outcome labels rather than color alone. Respect the existing site's restrained visual direction without making the report depend on the public website.

## Implementation checkpoints

### 7.1 — Validate the diagnosis tasks and freeze the view contract

Sketch the report using the two real tasks and current report v1. Inventory which questions existing evidence can answer. Approve the minimal event/frame set, limits, privacy behavior, and standalone command semantics before instrumenting the runner.

Acceptance: every proposed panel points to an existing or explicitly planned observation. Remove speculative panels and inferred root causes.

### 7.2 — Render existing outcomes safely

Implement the standalone renderer in Go behind the artifact boundary. Show suites, failures, captured screens, diffs, and cleanup using existing evidence. Resolve roots safely; handle missing artifacts and unsupported versions without running a target.

Acceptance: a report v1 from an intentional mismatch renders offline; a malformed report fails; hostile screen text appears literally. Open the result in a browser as well as checking generated markup.

### 7.3 — Capture the minimal diagnostic events

Instrument the runner/session boundary without changing assertion decisions. Preserve synchronization and avoid blocking terminal reads on HTML or filesystem writes. Define how queued observations are bounded and drained on cancellation.

Acceptance: real-PTY success, timeout, early exit, and cancellation produce correctly attributed events with bounded shutdown. Run the race detector because shared lifecycle observations change.

### 7.4 — Add bounded checkpoint evidence

Implement only the checkpoints justified in 7.1. Reuse immutable screen captures, annotate viewport and phase, and enforce per-spec and suite budgets. State when frames/events were omitted.

Acceptance: a delayed redraw followed by a satisfied assertion has evidence at the right phase; a silent timeout shows no invented readiness; an output flood cannot expand diagnostic memory indefinitely.

### 7.5 — Exercise corrupted and adversarial artifacts

Test wrong-run sidecars, missing screens, path escape, symlinks, oversized references, XML/HTML-like terminal text, control sequences, Unicode, very long lines, and write failures. Verify the page has no external requests and remains usable without JavaScript where practical.

Acceptance: report problems are visible and separate from test outcomes; the renderer does not execute, fetch, or read outside its allowed evidence root.

### 7.6 — Repeat the maintainer diagnosis tasks

Give the generated artifacts to a developer without explaining the seeded failure. Record their explanation and comparison with the expected diagnosis. Include a case with incomplete evidence so uncertainty is tested as deliberately as success.

Acceptance: both tasks can be explained from the artifacts, and missing observations are not mistaken for confirmed target behavior. Update examples and troubleshooting documentation based on actual confusion.

## Acceptance matrix

| Case | Required observation |
| --- | --- |
| Snapshot mismatch | Correct step, expected/actual diff, and matching failure screen. |
| Assertion timeout after input | Input submission and pending assertion visible; no claim the app consumed input. |
| Unexpected exit | Observed exit status and first failing step preserved. |
| Cancelled suite | Active failure and later not-run specs remain distinguishable. |
| Failure plus cleanup failure | Both visible without replacing the primary outcome. |
| Report without diagnostics | Useful static summary; history explicitly unavailable. |
| Wrong or truncated sidecar | Clear diagnostic error; no merged cross-run history. |
| Large/flooding target | Bounded capture; omissions disclosed; cleanup still completes. |
| Hostile HTML/OSC/path | Literal text or rejected reference; no execution/network/path escape. |
| Sensitive synthetic canary | Disallowed metadata fields are absent; screen persistence follows the documented opt-in boundary. |

## Definition of done and handoff

- [ ] Checkpoints 7.1–7.6 complete and both real diagnosis tasks recorded.
- [ ] Standalone rendering cannot launch a target or alter snapshots/outcomes.
- [ ] Timeline schema, capture limits, missing-data behavior, and privacy guidance published together.
- [ ] Unit/renderer checks and relevant real-PTY, race, and native platform checks pass.
- [ ] Existing console and JSON workflows remain usable without diagnostics enabled.

Handoff to [Sprint 8](08-ci-adoption-and-installation.md): a documented artifact set that an external repository can upload and inspect. Recordings and minimization remain separate proposals requiring evidence that these reports cannot solve a real task.
