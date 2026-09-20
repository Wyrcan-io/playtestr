# Competitive assessment — 15 September 2026

> Historical assessment. Current-state descriptions and recommendations are superseded by the [19 September survey](competitive-user-survey-2026-09-19.md) and [delivery roadmap](../plans/README.md). Preserve the dated observations below as history, not current feature status.

## Verified conclusion

Playtestr can already serve supported keyboard-driven regression flows. We have
not established that it is more reliable, easier to use, or commercially
stronger than its alternatives. Its documented feature surface is narrower.

The opportunity is a focused product: a short reviewed test, a dependable CI
result, and a failure a developer understands immediately. Completing six more
sprints is neither necessary nor sufficient to win that workflow.

## Evidence and corrections to the first assessment

We inspected the local CLI, terminal adapter, README, compatibility contract,
release/trial records, and sprint plans. The CLI currently accepts explicit spec
paths and supports snapshot updates and a JSON report; directory discovery and
a local HTML report are proposals. The adapter uses vt10x with buffering for
split UTF-8 input. The documented wide-cell and grapheme limits remain relevant.

Public GitHub metadata was refreshed on 15 September. Playtestr showed one star,
zero forks, and zero open issues. The cohort record reports no qualifying
independent runs. That establishes an evidence gap; it does not establish that
nobody uses the binary or that demand is absent. The stable release was only
three days old. Stars are attention, not customers or technical quality.

The earlier response made several claims too strongly:

- Competitor README capabilities are documented capabilities, not our executed
  compatibility or reliability findings. No comparative runtime benchmark was
  performed in this review.
- Microsoft's broad current documentation explicitly describes a beta rewrite.
  The GitHub latest stable release field returned 0.0.4; its beta surface must
  not be attributed to that stable release.
- More terminal features do not prove better cleanup or fewer flakes. We have
  not audited competitors' complete lifecycle implementations.
- VHS's much larger star count does not prove market share. It is primarily an
  adjacent recording product.
- A “4/5 correctness” score has no calibrated meaning here. Numeric rankings
  from the first assessment have been removed.
- We have no evidence of Microsoft staffing or budget for this particular
  repository, competitor revenue, total market size, or likely Playtestr income.
- The previous local test claim was broader than the captured command output:
  the transcript did not show a final runner-package result and explicit exit
  codes for both checks. This planning review relies on recorded release/CI
  evidence and does not assert a newly completed full local test run.

The earlier read-only check observed successful Website and Terminal tests runs
at commit 0ec1e2d and an HTTP 200 homepage with the stable download. This was a
deployment smoke, not a complete live-site usability audit:
[Website run](https://github.com/Wyrcan-io/playtestr/actions/runs/34718370933),
[Terminal tests run](https://github.com/Wyrcan-io/playtestr/actions/runs/34718370801).
Existing native and application claims remain scoped by
[platform support](../platform-support.md) and the trial records.

## Closest alternatives and what to learn

These observations describe project-owned documentation checked on 15 September
2026. Branch documentation can lead releases; pin a tag and check its matching
documentation before a hands-on comparison.

| Alternative | Documented approach | Implication for Playtestr |
| --- | --- | --- |
| [Microsoft tui-test](https://github.com/microsoft/tui-test) | Beta rewrite: CLI sessions and Rust/Python/JavaScript APIs, locators, styles, mouse, multiple backends, screenshots and recording. | Real PTYs, cross-platform binaries, and screen assertions are shared capabilities. A small reviewed test-and-report workflow must earn preference. |
| [Atago](https://github.com/nao1215/atago) | Declarative CLI testing with rendered PTY checks, fixtures, suites, JUnit, CI setup, and generated initial specs; also covers service peers. | Closest broad declarative alternative. Learn its runnable onboarding and useful CI output. Native binaries and declarative files alone do not differentiate us. |
| [Termless](https://github.com/beorn/termless) | Terminal application testing with Vitest, cell/state inspection, emulator backends, screenshots, and playback. | Strong fit when users need detailed terminal or cross-emulator behavior. Its TUI testing role is as important as its conformance work. |
| [Termlens](https://github.com/vyncint/termlens) | Rust E2E library with screen predicates, bounded waits, snapshots, masking, and richer terminal semantics. | Reliability and evidence already matter to competitors. A standalone language-neutral runner is a different workflow, not proof of superiority. |
| [VHS](https://github.com/charmbracelet/vhs) | Scripted recordings, screen waits, text/golden output, and CI integration. | Learn the immediately understandable demonstration. Do not claim it has no testing or assertion-related support. |
| [Textual testing](https://textual.textualize.io/guide/testing/), [Ratatui testing](https://ratatui.rs/recipes/testing/snapshots/), [Ink testing library](https://github.com/vadimdemedes/ink-testing-library) | Framework-specific test helpers and snapshots. | Existing framework tests are a serious substitute. Position real-process E2E as a small additional layer, not a replacement for fast unit/widget tests. |

Termlens also explains its separation of readiness predicates, settled screens,
and output silence in its [design document](https://github.com/vyncint/termlens/blob/main/docs/DESIGN.md).
This supports studying synchronization semantics rather than assuming our
positive-readiness policy is unique.

Dated GitHub attention snapshot: tui-test 263 stars, Atago 20, Termless 36,
Termlens 20, VHS 20,904. Latest stable-release metadata returned Atago v0.22.0,
Termless v0.8.4, Termlens v0.11.0, and VHS v0.12.0. These numbers establish
neither adoption in production nor comparative quality.

## Focus and honest limits

Target maintainers who need to protect a few important keyboard interactions
through the actual executable: selection, navigation, modal close, resize, and
expected exit. Start with repeatable synthetic data and supported screen text.

Current strengths are bounded execution, explicit readiness, transactional
baselines, structured outcomes, a standalone runner, and documented native
release evidence. The product promise can combine these into a simple workflow.
Competitors possess overlapping strengths; this is a positioning hypothesis.

Current gaps include suite ergonomics, installation effort, failure presentation,
limited keys, unsupported style assertions, and incomplete complex Unicode
layout. A flow requiring those absent semantics may be better served elsewhere
today. A shorter feature list never excuses an incorrect screen or false pass.

Screen assertions alone cannot prove filesystem or service mutations. The
Lazygit trial already found a screen pass while the Git index was unchanged.
Keep independent postconditions in explicit target-specific harnesses. Do not
turn that lesson into a general database/HTTP assertion engine.

## Recommended delivery order

See the [product focus](../plans/product-focus.md) and
[roadmap](../plans/README.md) for the current contract.

1. **Sprint 5: useful suites.** Directory selection, list, serial execution,
   a concise summary, and safe evidence destinations. JUnit, custom globs, and
   filtering require an actual acceptance workflow; the ordinary demo needs
   only a directory argument.
2. **Sprint 7: readable failure evidence.** Recommended next candidate after
   Sprint 5: one polished offline HTML report from the existing evidence. Show
   the failing step, screen, diff, and cleanup. It does not depend on Sprint 6,
   a new diagnostics sidecar, continuous recordings, or target execution.
3. **Sprint 6: failure handoff, if necessary.** Build a bounded one-spec
   manifest only when ordinary evidence and explicit rerun instructions cannot
   resolve missing local context.
4. **Sprint 8: one easier installation route.** A setup action or one requested
   package channel, chosen from measured friction. It can move earlier if it
   prevents a willing user from starting.
5. **Sprints 9/10: unblock a real flow.** Controlled fixture state or one
   terminal behavior family. Either moves ahead of convenience work when it
   prevents correct testing.

Identifiers stay stable for links; they are not an execution dependency chain.
Technical work can use a documented reproducible project case while recruitment
continues. Independent trial completion is a separate adoption gate and may
never be filled by operator repetitions. Stop at each delivered boundary.

The previous instruction to bundle installation into Sprint 5 is superseded.
A separate small installation milestone is useful when warranted; it does not
belong in every suite implementation by default.

## A demo that earns the next click

Plan a 45–60 second explanation: show the short test beside an actual terminal
interaction; introduce one meaningful UI defect; show the captured failure and
focused diff; fix the target and rerun successfully. Annotated playback must be
identified as recorded. When the report ships, show the same report users get.

The initial missing visual goal is not another homepage redesign. The existing
R5 example can carry the story. Improve the path from watching to running the
same example: disclose prerequisites, use an exact runner release, provide
reviewed specs/baselines, and separate installation time from execution time.

Proposed usability gates, not measured achievements: a newcomer explains the
bug after one viewing; with documented prerequisites ready, they complete
pass/failure/recovery within ten minutes; they can change one assertion and
explain its result. Record actual times, assistance, failures, and decisions to
continue. A failed gate should identify a specific usability repair.

## How to establish a competitive advantage

Use three matched tasks: a selector/modal regression, a resize/redraw regression,
and a small CI suite containing an intentional mismatch. Choose one applicable
competitor per task first, normally Atago for the declarative workflow and
Termlens or tui-test where its API/session model is the relevant alternative.

Pin target and tool releases, OS/architecture, dimensions, fixtures, and defect.
Keep missing features, installation failures, and invalid comparisons visible.
Give alternatives their documented idiomatic setup. Do not compare our tuned
recipe against a deliberately weak competitor script.

Measure fresh installation effort, first useful test, authoring/maintenance,
time to identify the seeded failure, repeated-run failures, and cleanup on
hang/cancel/flood. Count all attempts; a small sample cannot prove zero flakes.
Test our known limitations as well as strengths. Publish procedures and
sanitized results only after actual execution.

A credible win is a maintainer choosing Playtestr for these workflows after
comparison, with no regression in correctness or lifecycle behavior. No such
head-to-head result is claimed here.

## Monetization remains an experiment

Keep the standalone regression workflow useful without an account. Sponsorship,
scoped onboarding, and compatibility/support engagements are plausible early
experiments. We have no paying-customer or willingness-to-pay evidence.

A later evidence service might sell history, sharing, retention, and support;
[Cypress Cloud](https://docs.cypress.io/cloud/account-management/billing-and-usage)
and [Buildkite](https://www.buildkite.com/pricing/) demonstrate adjacent models,
not demand for a terminal-specific subscription.

Five unrelated repositories with repeated CI use and two requests for shared
history are proposed discovery triggers, not proof a service should be built.
Require a paid pilot and measured operating/support costs before committing.
The earlier dollar ranges were untested interview hypotheses, not recommended
prices or revenue forecasts. No cloud, billing, or account work belongs in the
current sprint plans.
