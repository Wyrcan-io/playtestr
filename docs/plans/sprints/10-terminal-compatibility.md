# Sprint 10: fix a terminal compatibility gap that blocks a real test

Status: proposed and evidence-gated. This plan is not a promise of full Unicode or terminal-emulator compatibility. Read the current [terminal compatibility contract](../../terminal-compatibility.md) before selecting the implementation scope.

## User problem and outcome

A real application's screen looks correct in the maintainer's terminal, but Playtestr places a character in the wrong cell, wraps a line incorrectly, or does not handle a control sequence the application needs. The resulting snapshot failure describes the emulator's limitation instead of a product regression.

The outcome is one precisely scoped compatibility improvement, backed by a reproducible application flow and a focused terminal corpus. Existing supported screens remain correct, changed snapshot behavior has an explicit migration path, and unimplemented behavior remains documented.

The known one-rune-per-cell limitation makes wide-character layout a likely candidate. It is not a commitment to implement grapheme segmentation, every emoji sequence, every terminal protocol, mouse input, or image rendering in one sprint.

## Entry gate and scope selection

Require a real adopter reproduction that fails with the current runner, the exact target/version, terminal dimensions, input sequence, and independently observed expected screen. Reduce the problem to a small fixture while retaining the application case as the acceptance test.

Choose one family of behavior after triage:

1. Cell width and cursor layout for a bounded set of wide characters, if that is the blocker.
2. One missing VT sequence family with a demonstrated application dependency, if that is more valuable.
3. One specific terminal-query response needed for startup or resize, if that is the actual cause.

These are alternatives, not three required workstreams. Write the chosen family and explicit exclusions into checkpoint 10.1. If there is no blocking case, postpone this sprint; collecting broader compatibility claims without user need is not completion.

Review ordering before starting. If this gap prevented a useful R3 trial or an earlier sprint's core workflow, move this work earlier rather than waiting for the number 10. Conversely, do not use the known limitation alone to justify replacing the whole terminal engine.

## Success measures

The previously blocked application flow passes on the exact native platforms claimed, a deliberate application regression still fails, and the focused fixture's expected cells/cursor behavior agree with the documented contract. Existing menu, resize, redraw, Unicode-read-boundary, alternate-screen, exit, timeout, and cleanup regressions continue to pass.

Record before/after CPU, memory, and throughput on fixed normal-output and flood workloads. Establish baselines before choosing an implementation. A provisional review trigger is a greater-than-20% regression over repeated comparable measurements, not an automatic universal pass/fail threshold; investigate variance and set a justified bound for the selected workload at checkpoint 10.2. Product output/time limits cannot be relaxed merely to make a new engine pass.

Compatibility statements name the tested application, version, host, dimensions, and sequence/character subset. Passing a framework example does not certify all applications built with that framework.

## Independent expected behavior

Create a small corpus with literal input bytes or deterministic fixture writes, initial dimensions, operations, expected rendered cells/text, cursor state where relevant, and the source of the expectation. Document the terminal standard or exact reference terminal/version used when implementation requires external protocol facts.

Do not generate goldens from the implementation being tested and then treat matching them as proof. Use manually reasoned cases checked against the relevant primary specification and an independently observed native terminal. Where terminals differ, define Playtestr's selected profile and disclose the difference instead of choosing whichever output makes a test pass.

For the likely wide-cell slice, candidate cases include:

- An ASCII prefix followed by one selected width-two character and a suffix.
- Cursor positioning and overwriting either cell of a wide glyph, with an explicit continuation-cell rule.
- Erasing a line or region intersecting a wide glyph without leaving stale cells.
- Wrapping at the last and second-last columns under the selected profile.
- Shrinking and expanding a viewport containing a wide glyph.
- A split UTF-8 read for the selected glyph, preserving the existing buffering guarantee.
- Alternate-screen entry/exit containing the selected text.

Freeze which of these are necessary for the real application. Combining marks, variation selectors, regional indicators, ZWJ emoji, bidirectional display, and ambiguous-width characters remain explicitly unsupported or retain documented behavior unless one is the selected blocker. Do not label the result simply "Unicode support."

If the chosen family is a control sequence or query instead, replace this candidate list with that family's exact valid, incomplete, malformed, reset, resize, and interleaving cases before implementing. Query responses must use the existing bounded input path and must not create unbounded response loops.

## Implementation decision and architecture

Keep the terminal dependency behind the internal session boundary. Evaluate three concrete options: a small upstream-compatible patch, a focused adapter where semantics can be correct, or replacing the emulator. Time-box an initial investigation to a few working days, with runnable prototypes and a decision record. Stop or split the sprint if a whole-engine migration is the only viable solution and cannot fit the acceptance boundary safely.

Compare correctness against the selected corpus, parser/resize APIs, concurrency ownership, dependency maintenance/license, bounded memory, and measured workload behavior. Do not choose a library by popularity or add a second runtime. If external documentation or packages are evaluated during implementation, verify current primary sources then.

Avoid repairing wide characters by postprocessing final strings alone: layout errors affect cursor movement, wrapping, erasing, and later writes. The cell model must represent the selected behavior at the terminal boundary if that is the chosen gap. Ensure continuation cells cannot become independent visible characters or leak stale contents.

Keep one synchronized owner of parser/screen state, or preserve the existing explicit locking model. A renderer upgrade must not introduce a background goroutine without a bounded shutdown path. Raw output accounting remains based on received bytes, independent of how many terminal cells are produced.

## Snapshot and version contract

Classify the change before implementation: a correction within documented behavior or a newly supported behavior that changes the contract. Record representative before/after output and the impact on existing baselines. Never run a repository-wide snapshot update to conceal emulator changes.

For new width/profile behavior, propose an opt-in terminal profile under the then-current new spec version, for example `terminal_profile: "text-wide-v1"`. This is a design placeholder, not an implemented field. Coordinate with Sprint 9's version decision; preserve v1's documented behavior and reject unsupported profile names. If an implementation cannot preserve the old profile, explicitly design and announce a breaking migration rather than silently changing every existing test.

Each profile has a deterministic documented width policy, including handling of ambiguous characters. Do not depend on the developer's font or unspecified locale for snapshot widths. Text snapshots stay text snapshots; no color/style comparison is introduced here.

Add profile information to reproduction prerequisites using an appropriately versioned format. A rerun with a different profile cannot be called identical context. Ensure diagnostic screen exports and HTML reports render text legibly without asserting that a browser font proves terminal cell correctness. If needed, show cell/cursor metadata in an optional technical view for this debugging task.

Migration instructions identify affected specs, run the old and new profiles against the chosen application, review differences, update only deliberately selected baselines after positive readiness, and rerun without update. Existing transactional snapshot protections remain mandatory.

## Implementation checkpoints

### 10.1 — Confirm the real blocker and select one family

Record the application reproduction and independently observed expectation. Choose the exact character/sequence subset, relevant native hosts, and exclusions. Decide whether this is a documented-contract correction or an opt-in extension.

Acceptance: a focused regression fails against the current runner for the intended reason, and the target's own regression is distinguishable from the emulator defect.

### 10.2 — Compare bounded implementation options

Prototype only enough of each plausible option to run the reduced corpus. Measure current performance and candidate overhead, inspect lifecycle integration and licensing, and write a decision with rejected alternatives and maintenance costs.

Acceptance: one approach can satisfy the selected behavior without weakening resource limits or hiding unsupported cases. If no approach qualifies, report the blocker and split/replan instead of undertaking an unbounded replacement.

### 10.3 — Implement terminal semantics with focused coverage

Implement the selected profile/behavior and malformed/incomplete input handling behind the internal terminal boundary. Use unit tests for pure cell transformations and real PTYs for byte fragmentation, input interaction, and process behavior.

Acceptance: the independent corpus passes; out-of-scope inputs do not panic, allocate without bound, or acquire accidental compatibility claims. Run the race detector for shared terminal changes.

### 10.4 — Integrate resize, snapshots, and evidence

Exercise selected behavior across erase, wrapping, redraw, resize, and alternate-screen transitions as relevant. Update strict schemas, version validation, report/reproduction prerequisites, and migration examples together.

Acceptance: assertion, snapshot, failure artifact, and diagnostic frame reflect the same captured terminal state. A mismatched profile is visible during reproduction inspection.

### 10.5 — Run native compatibility and regression checks

Run existing real-PTY regression suites and the selected application on each claimed platform. Inspect failed cases rather than disabling snapshots or raising product timeouts. Repeat normal/flood performance measurements with the same builds and environment settings used for the baseline.

Acceptance: exact run evidence supports the advertised scope; unsupported hosts remain labeled. Any newly failing previous supported case is fixed or explicitly prevents promotion.

### 10.6 — Complete a reviewed adopter migration

Have the maintainer enable the new profile where applicable, inspect the deliberate baseline change, and rerun the actual workflow. Introduce a controlled target regression and show that the test still rejects it. Record any unsupported neighboring characters or protocol behavior they encountered.

Acceptance: the original adoption blocker is removed, regression detection remains useful, and the public compatibility table reflects tested scope rather than aspirational coverage.

## Acceptance matrix

| Scenario | Required result |
| --- | --- |
| Reduced real-app blocker | Correct independently specified screen/cursor behavior. |
| Deliberately broken target | Meaningful assertion/snapshot failure remains. |
| Fragmented UTF-8/escape input | Same result as equivalent complete writes within the selected contract. |
| Relevant wrap/erase/resize boundary | No stale/duplicated cells; deterministic documented output. |
| Alternate-screen transition | Correct restoration for the supported profile. |
| Unsupported profile | Validation failure before target launch. |
| Old spec/profile | Existing documented behavior preserved or an explicitly approved migration required. |
| Different reproduction profile | Context mismatch is visible; no claim of exact reproduction. |
| Malformed/flood input | Bounded resource use, timeout/cancellation, and cleanup retained. |
| Native application trial | Evidence names actual host/version; no framework-wide inference. |

## Definition of done and next decision

- [ ] Checkpoints 10.1–10.6 complete for one selected compatibility family.
- [ ] Independent corpus and real adopter workflow both demonstrate the fix.
- [ ] Previous supported behavior, resource bounds, and lifecycle checks remain intact.
- [ ] Profile/version/schema changes and reviewed baseline migration are documented together.
- [ ] Compatibility table names exact supported and unsupported behavior with evidence.

At this boundary, review adoption and maintenance rather than automatically inventing Sprint 11. Ask which real task is still costly: slow suites, authoring long interactions, sharing failure evidence, or another compatibility gap. Parallelism, recording, minimization, and services each need their own concrete evidence and acceptance boundary. The success of Sprints 5–10 is a dependable tool people keep using, not the number of features delivered.
