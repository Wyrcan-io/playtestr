# Sprint 12-B optional-extension decision

Date: 2026-09-21. Decision: **defer both candidates**. Evidence reviewed at
source checkpoint `b623241`. This is an evidence-gate decision, not an
implementation or a claim that every future application needs no additional
input or assertion mechanism.

## Entry-gate result

The gate requires two distinct admitted workflow IDs blocked by the same input
family, or two with unavoidable irrelevant dynamic text after fixture and state
control. There are no such pairs:

- The five admitted pilots all complete their intended interaction with current
  named keys and text input. The corpus checkpoint explicitly records no shared
  missing-input blocker.
- `GUM-01` and the selector recipe prove the selected value with exact accepted
  output, so a styled or focused selection assertion would add no proof.
- `LG-01` and `LG-08` use independent Git state checks where screen text alone
  is insufficient. Cropping a screen cannot replace those oracles.
- `CV-01` and the stateful recipe control the target and verify generated files.
  Dynamic-screen masking would weaken rather than improve the state proof.
- `BT-06` and the full-screen recipe pass with explicit redraw waits, positive
  post-resize assertions, a controlled marker process and its identity oracle.
  The absent-marker control still fails at the intended assertion.

The 201 planned risk-map gaps are missing focused coverage, not application
failures attributable to a missing public feature. Treating a coverage-plan row
as product demand would bypass the checkpoint.

## Alternatives and cost

| Candidate | Smallest contemplated contract | Why rejected now |
| --- | --- | --- |
| More keys or bracketed paste | New finite key names or an explicit paste action/mode | No two named workflows fail for the same input; requires PTY mode, blocked-write, exit, timeout, cancellation and host coverage without shortening a current recipe |
| Focused text assertion or snapshot | Explicit bounded rectangle with resize semantics and evidence metadata | No two workflows retain unavoidable noise after fixture control; regions intentionally hide text and cannot prove color-only selection or external state |

Either option would change a strict public spec and require minimum-reader,
old/new document, schema, migration, bounds, report, native and maintenance
decisions. With zero qualifying blocked workflows, that cost has no accepted
user result. Spec v1/v2, report v1/v2, schemas, examples and old-reader behavior
remain unchanged.

## Revisit trigger

Reopen only with two distinct admitted or adoption workflows, exact current
commands, the same reduced failure family, independent expected results, failed
fixture/state-control workarounds, and a demonstration that the smallest option
makes both feasible or materially shorter while their known-bad controls still
fail. A competitor feature, a hypothetical workflow, or a risk-map gap alone is
not sufficient.

Sprint 12 is therefore complete as **A delivered, B deferred**. The next
checkpoint is Sprint 6's ordinary-instructions handoff experiment.
