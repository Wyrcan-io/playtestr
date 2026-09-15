# Product focus — a smaller way to become the better choice

## Product job

Playtestr helps a maintainer prevent a regression in a trusted interactive CLI
or TUI by running a small, reviewable keyboard flow in CI and returning bounded,
credible failure evidence.

The product is not a terminal emulator laboratory, a general automation daemon,
a recording studio, a framework SDK, or a hosted test platform. It is a
deterministic regression runner.

## What “better” means

Playtestr does not need to have more commands than every alternative. It is
better for its intended job only when an independent maintainer can:

1. Write or review a small terminal regression test without learning an SDK or
   assembling an `expect` script.
2. Run it in CI without a false pass from a hang, exit, stale artifact, or
   missing test selection.
3. See the first useful failure and rerun the relevant test locally with the
   right context.
4. Keep using it after the first assisted setup.

A feature belongs in the core when it improves one of those outcomes for a
concrete user task and does so without weakening bounds, determinism,
privacy, or the simple standalone-binary workflow. Product design may use a
documented hypothesis before recruitment completes; independent validation
must remain labeled pending. Attractive presentation and easy onboarding are
functional product requirements, even when an expert can work around their absence.

## Core contract to protect

- Declarative, language-neutral test files.
- Real PTY input and rendered-screen text assertions.
- Explicit readiness and exact process outcomes.
- Per-step/run/output budgets, cancellation, and best-available tree cleanup.
- Reviewed, transactional text snapshots.
- Small, versioned, privacy-conscious reports and artifacts.
- Native support claims only where the exact path has run.

## Deliberately not core

- Persistent interactive sessions, terminal-as-a-service daemons, or agent
  control protocols.
- Multiple programming-language SDKs.
- Video/GIF capture, visual/styled baselines, or a general terminal recorder.
- Full emulator conformance matrices or support for every terminal protocol.
- Parallel scheduling, retries, auto-healing, or flake masking.
- HTTP/database/browser/service testing, cloud accounts, hosted dashboards,
  PR bots, billing, or telemetry.
- Package-manager breadth. One distribution channel is justified only after
  measured demand and an owner for updates.

These are not bad features. They are other products or later, evidence-backed
extensions. Competing with Microsoft `tui-test`, Termless, VHS, and Atago on
their broadest surfaces would make Playtestr less coherent and less maintainable.

## Roadmap rule

The next proposed implementation milestone is Sprint 5.
Stop after its acceptance project and review retention before starting another
implementation sprint.

Subsequent items are candidates, not promises:

| Observed recurring obstacle | Smallest candidate response |
| --- | --- |
| A maintainer cannot run a directory of tests or find the failed screen | Sprint 5 suite discovery, summary, and safe artifact layout. |
| A CI failure cannot be understood locally because its required context is unclear | One-spec, local-only reproduction manifest. |
| Existing screen/diff/report evidence leaves a proven diagnosis question unanswered | One bounded inspector view; no dashboard or recording by default. |
| Reused files or config make a stateful flow nondeterministic | One reviewed fixture-workspace slice. |
| A demonstrated target needs one missing key, query, width rule, or VT family | One bounded compatibility slice. |

If a proposed feature has no concrete task or testable product hypothesis,
record it in the backlog. Correctness fixes do not wait for multiple users.
Prefer a small failure report after Sprint 5; it can make existing evidence
easier to understand without requiring richer capture or reproduction tooling.

## Competitive discipline

The closest tools are broad and active. Microsoft `tui-test` is a beta rewrite
with persistent sessions, APIs, locators, mouse control, styles, screenshots,
and recordings. Atago combines CLI, service, fixture, and TUI testing. Termless
supports both TUI tests and emulator comparisons. VHS is presentation-oriented.
These documented approaches confirm active work in the category; they do not
establish market size or independently verified product quality. See the
[dated sources and limitations](../research/competitive-assessment-2026-09.md).

Playtestr should win by being the simplest tool a team trusts for a durable CI
regression test. Any “better than” claim must name that workflow and be backed
by adopter preference, not feature parity.

## Make the proof memorable

The product should look compelling because the evidence is clear, not because
it imitates a terminal recorder or a SaaS dashboard.

The public “jump in” loop is:

```text
write a short flow → run it → introduce one visible regression
→ see the captured screen and focused diff → fix it → rerun green
```

The website already presents this loop using recorded states from real fixtures.
Keep that standard for every public demo:

- Use a real target, real spec, real baseline, and captured runner evidence.
- Show one interaction and one meaningful regression, not a feature montage.
- Let the contrast between pass, intentional failure, and recovery carry the
  visual story; never invent output, testimonials, performance counters, or
  coverage claims.
- Make CLI output crisp: stable spec names, a short per-spec result, a final
  summary, direct artifact paths, and readable diffs. This is functional
  design, not decoration.
- Keep the runner text-first and scriptable. A browser demo may be polished,
  but it must never pretend to be a live terminal or add a runtime service.

Sprint 5's human suite summary is therefore part of the product experience. It
must make a maintainer want to inspect a failure because the relevant test and
evidence are obvious, not because it uses animation or visual effects.

## Demo acceptance

Use one 45–60 second story as a design target, with optional pauses and a static
fallback. Reuse the existing R5 presentation and choose a regression whose
changed terminal text explains why the feature matters.

1. Show a short reviewed spec alongside one keyboard interaction.
2. Run the correct target and show success.
3. Introduce one visible target defect, such as the wrong item selected or a
   missing confirmation. Keep the reviewed expected baseline unchanged.
4. Show the real nonzero result, failing step, captured screen, and focused diff.
5. Restore the target and rerun green; retain the failure evidence for inspection.
6. Link directly to the same versioned example and its explicit prerequisites.

A deliberately different expected baseline can explain diff mechanics, but
label that as a snapshot-mismatch demonstration; it alone does not prove a
target regression was detected.

When Sprint 7 ships, use its actual exported report in this story. Color
highlights in a diff show text changes and do not imply styled terminal
assertions. Any annotation or accelerated playback must be labeled as
presentation. Do not render proposed commands as shipped functionality.

Proposed user checks: after one viewing, a newcomer explains what bug was
caught; with prerequisites ready, they run pass/failure/recovery within ten
minutes and change one assertion themselves. Record actual time, installation
time separately, assistance, and willingness to use it on their own app.
These are usability targets, not achieved metrics.

Visual polish should appear in hierarchy, readable aligned text, a focused
diff, responsive layout, and an obvious next action. Keep detailed metadata
available without requiring it for the first successful test. Reuse the
existing site style and avoid another branding project.

## Decision gate

Continue beyond a sprint only when the evidence names:

- the maintainer and recurring task, with permission-aware records;
- the target/version/host and a reproducible before/after outcome;
- why existing Playtestr behavior is insufficient;
- why the smallest proposed response is safer than a documented workaround;
- the success and failure acceptance cases; and
- a maintainer who will evaluate the result again.

Otherwise, improve docs, recruit another trial, or leave the area alone.
