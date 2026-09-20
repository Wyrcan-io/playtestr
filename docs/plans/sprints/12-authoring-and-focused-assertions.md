# Sprint 12: make the first useful test easy to write

Status: planned; checkpoint B conditional. Owner: Playtestr maintainer. Entry: Sprint 11 baseline recipes and the [research evidence](../../research/competitive-user-survey-2026-09-19.md). No independent adopter is needed before engineering; human measurements wait for A1.

Follow the [execution contract](../execution-contract.md) and [root roadmap](../../../roadmap.md). Reuse existing multi-snapshot, `expect_not`, redraw-wait and v2 report behavior. This sprint improves a demonstrated journey rather than inventing commands to make a plan look complete.

User result: a developer adapts a short complete example, gets a useful diagnostic for a mistake, and can explain why the test proves the intended behavior.

## A: recipes and diagnostics first

Provide three versioned copyable recipes: a selector with exact output/exit, a stateful setup wizard with an external file check, and a full-screen modal/resize flow. Include target/runtime prerequisites, runner minimum version, native host evidence, a deliberate defect and recovery. Explain readiness after input, disappearance assertions, continuously repainting screens, multiple snapshots and selective baseline updates.

Audit existing JSON schema/editor integration and validation errors with ten realistic mistakes: wrong version, unknown field, invalid key, mixed actions, missing command, malformed duration, missing baseline, snapshot without readiness, incorrect workspace path, and empty selection. Improve field/step/path context without leaking typed values or environment secrets. Invalid specs must fail before target launch.

Prefer examples and current CLI improvements. An init/validate command is not assumed necessary: if proposed, show the specific task existing validation cannot do and review its contract separately. Do not add a recorder or generate baselines from an unreviewed target automatically.

Acceptance: each recipe runs pass/intentional failure/recovery from a clean environment; no undocumented prerequisite; error examples identify the next action. Record operator setup and edit times as biased engineering measurements, not independent usability results. Manual demo: adapt one assertion, demonstrate a validation error, then catch a real changed behavior.

Record the authoring journey as separate observations: prerequisite acquisition, first launch, first valid spec, meaningful readiness, first intentional failure, diagnosis, baseline review and rerun. Keep the concise example front and center; move boundedness and format details to reference docs. A short spec that never reaches a meaningful state is not a usability win.

For each of the ten invalid-input cases, define whether validation can occur before launch. Missing baseline existence may be evaluated during execution under the current contract; do not claim universal prelaunch rejection if implementation does not guarantee it. Any proposed shift in validation timing must preserve errors, resource bounds and snapshot-update semantics, with a regression test. Invalid spec syntax/semantics must always reject before target launch.

## B: one extension only when demonstrated

At A's exit choose **one** of the following, or defer both:

| Candidate | Entry evidence | Minimal scope |
| --- | --- | --- |
| Additional keys or paste | Two corpus workflows blocked by the same input family | A finite named key set OR explicit bracketed-paste behavior with tested modes; no arbitrary protocol scripting |
| Focused text assertion/snapshot | Two workflows have unavoidable irrelevant dynamic text after fixture/state control | One bounded region mechanism with clear coordinate and resize semantics; no general regex-rewrite/masking language |

The first checkpoint freezes versioning, schema, bounds, interaction with readiness, report metadata, old-spec behavior and migration. Do not silently widen strict v1/v2 formats. Unknown actions and out-of-bounds regions fail before launch where determinable. Rectangles after resize must have an explicit validated meaning.

Decision record: two named workflow IDs, current failing commands, rejected workarounds, minimal syntax/semantics, compatibility decision, before/after authoring steps, and maintenance burden. Existing formats are strict; an optional field still changes a published contract. Use an explicit new opt-in format or a documented compatible policy decision, never silently let older readers misinterpret data.

Text-only assertions cannot prove a selected item when selection changes only color/style. Use exact accepted output or an independent state result for that task; a region alone does not solve the problem. Do not quietly introduce styled snapshots under an authoring change.

For input: real-PTY tests cover successful delivery, unsupported mode/key, exit during input, blocked input, timeout, cancellation and cleanup on each claimed host. For focused assertions: seed bugs inside and outside the region, show what is intentionally unobserved, test empty/overlarge/out-of-bounds regions and full-screen evidence, and preserve the ability to diagnose excluded text. A region must never be advertised as full-screen coverage.

Acceptance: both entry workflows become shorter or feasible while their known-bad controls still fail. Existing spec/snapshot behavior remains intact; run appropriate unit/integration checks, race tests for lifecycle changes, manual recipe, and documentation/schema parity. If fixing target fixtures removes the need, record deferral as the successful scope decision.

## Exit

- [ ] Three complete recipes and ten diagnostic cases verified.
- [ ] Authoring friction observations recorded, including remaining limits.
- [ ] B has a justified minimal implementation or explicit deferral.
- [ ] Contract changes have schemas, examples, migration and native evidence.
- [ ] A1 receives the onboarding tasks and proposed timing targets.
