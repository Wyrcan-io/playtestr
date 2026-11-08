# Taskell scenario catalog draft v1

Status: **not frozen; no scenario-series credit**. The exact pinned source and
public first-use flow are reviewed. Before freezing, exercise every route on
the native target, retain settled screens and same-execution saved bytes, and
correct any unsupported or unstable interaction. Host cells are Ubuntu 24.04
x86-64 and macOS 15 Intel x86-64 only. The app is a single-process local
Markdown board; no web imports, credentials, or service behavior are in scope.

Cross-host one-shot evidence exists for N01 (existing-task smoke), N02
(create task), N03 (duplicate task), and N04 (rename), recorded in
`build-attempt-v25.json`. N04's first Mac setup attempt hit HTTP 504 while
fetching Stack; the Mac-only retry passed. N05-N08 are source-grounded authored
candidates, not yet executed. N02 requires Escape after Enter because Taskell
keeps a blank row in INSERT mode. No case has repeated-series credit and the
catalog remains unfrozen.
Target evidence: Taskell README, `Taskell.IO.Keyboard.defaultBindings`,
`Taskell.Events.Actions.Normal`, `Taskell.Events.Actions.Insert`,
`Taskell.Events.Actions.Search`, and `Taskell.IO.Markdown.Serializer` at the
source pin in `source-screen-v1.md`. In this source, Escape from task insert
calls `finishTask`; it commits the field rather than cancelling it. The
project must not claim a cancel-without-change route unless a separate actual
key behavior proves one.

Every eventual spec will launch the exact board file in a fresh fixture with
temporary home/temp, fixed locale/timezone where dates matter, 80x24 unless the
scenario explicitly covers resize, positive initial and post-action screen
observations, exact expected exit, same-execution exact Markdown bytes, and
confirmed process-group/workspace cleanup. IDs, inputs, host applicability,
expected state, oracle source, and byte hashes will be frozen before the final
series.

## Normal user workflows (candidate set: 8)

| ID | User task and starting data | Interaction under evaluation | Required outcome and independent oracle |
| --- | --- | --- | --- |
| N01 | Complete one existing To Do item on a two-column board. | Select the item, Space, then `q`. | The item appears in Done and is absent from To Do; capture the exact saved board after exit. This is the already observed first-use candidate; its six-step Linux run passed, but the case is not yet part of a repetition series. |
| N02 | Add a distinct task to a nonempty To Do list. | `a`, enter a unique title, Enter, verify INSERT mode, Escape to finish the blank row and return to normal mode, then `q`. | New title is visible before exit and serialized once in To Do in the expected order. Cross-host one-shot passed 12/12 with exact bytes and cleanup. |
| N03 | Duplicate an existing task for a second work item. | Select one uniquely named task with `j`, `+`, then `q`. | Two exact task rows serialize in the same list; neighboring rows stay in their original order. Cross-host one-shot passed 7/7 with exact bytes and cleanup. |
| N04 | Rename a task while preserving the other board items. | On the second uniquely labeled row, `e`, send Backspace once per old-title character, enter a new title, Enter, Escape, then `q`. | New title is rendered and saved once; the old title is absent and unrelated bytes retain their reviewed values. Linux and Intel Mac passed 22/22 once with exact bytes and cleanup. |
| N05 | Reorder a task within a list. | On a two-item fixture select the first item and press `J` once. | Exact row order changes once, with both items still present and no cross-list movement. |
| N06 | Move work from an active list to its next workflow column. | On a three-column fixture select the unique task and press `L`. | Task moves to the expected adjacent column and screen selection/column transition is visible; exact Markdown confirms one copy. |
| N07 | Find a non-default task and complete it. | Enter `/` search, type a unique term, Enter, Space, `q`. | The matching item is the one completed; exact saved bytes show unrelated tasks untouched. |
| N08 | Add a project-specific board column and use it. | `N`, enter a unique column name and press Enter; Taskell enters task insertion for the new list, where a unique task is entered, committed, and exited before `q`. | New column and task are visible and serialize in reviewed order without rewriting prior columns. |

## Edge and adversarial workflows (candidate set: 12)

| ID | Risk and fixture | Interaction under evaluation | Required outcome and independent oracle |
| --- | --- | --- | --- |
| E01 | Empty list and blank task input. | Open an empty but valid board; invoke `a`, submit an empty field, then quit. | No blank task is persisted; board remains usable. Confirm from rendered screen and exact file bytes. |
| E02 | Search with no matches. | Search a deliberately absent string, observe the empty result, Escape to clear. | Positive no-result state, then prior tasks return; exact board bytes are unchanged. |
| E03 | Ambiguous identical task labels in different columns. | Navigate by column and move only the fixture-selected copy. | Screen context identifies the selected column; byte oracle proves only that occurrence moved. Pair with N06's move risk. |
| E04 | Escape while editing, where user may expect cancellation. | Edit a task title, change text, press Escape. | Measure the pinned implementation's actual behavior. Current source predicts Escape commits through `finishTask`; freeze only that observed behavior and explicitly record that safe cancellation is unsupported if confirmed. |
| E05 | Small viewport plus resize/redraw. | Start at a supported compact viewport, resize, wait for redraw, navigate and act once. | Settled screen and exact saved bytes identify the same intended task after resize. Pair resize with a real state transition. |
| E06 | Long title/content and off-screen selection. | Use a bounded long task and enough rows to require navigation; complete the off-screen uniquely labeled row. | Wrapped/clipped rendering remains distinguishable; correct task alone changes in saved bytes. |
| E07 | Unicode text and spaced/Unicode board path. | Create a unique Unicode task in a fixture reached through a path containing spaces and Unicode. | Rendered text and UTF-8 file bytes match; process and fixture paths stay inside the managed workspace. |
| E08 | Rapid supported navigation. | Send a bounded burst of `j`/`k` movement, then one state-changing key. | Final selection is established by a fresh positive screen checkpoint; saved bytes show only the intended action. |
| E09 | Debounced persistence boundary. | Make one state change and quit immediately after its positive screen update. | Exact same-execution saved-state check after process exit proves the debounced write was flushed; cleanup must be confirmed. |
| E10 | Missing board path. | Launch with an absent explicit board path and observe the documented create prompt; quit without confirming creation. | Prompt is positive evidence; no file is created unless confirmation is observed. Verify absent state and clean exit/cleanup. |
| E11 | Malformed Markdown input and recovery. | Launch a bounded malformed owned fixture; capture the actual diagnosis/exit, then run the corrected fixture in a fresh workspace. | First run must not look successful or silently overwrite source data; separate recovery run proves normal use. Preserve both outcomes. |
| E12 | Read-only board write path. | Run as the hosted unprivileged user with an owned board that is genuinely read-only; request a state change. | Target must not be reported as a successful saved change; retain exact error/exit/screen, confirm original bytes and cleanup. Verify OS permissions before launch. |

## Predeclared risk pairs

| Pair | Combined risks | Bound |
| --- | --- | --- |
| P01 | E03 ambiguous labels + N06 column movement | Two named tasks, two destinations; one selected occurrence changes. |
| P02 | E05 resize/redraw + N05 reorder | One resize and one reorder; no repeated resize Cartesian product. |
| P03 | E07 Unicode/spaced path + N02 task creation | One exact Unicode title and one explicit managed fixture path. |
| P04 | E06 wrapping/off-screen + N01 completion | One bounded board size and one preselected off-screen item. |
| P05 | E01 empty input + E04 Escape in editor | One blank create attempt; no additional editor-state matrix. |
| P06 | E09 debounced quit + N06 move | One immediate quit after observed move; same-run state is the oracle. |

## Source fault candidates (not executed)

1. Change the genuine completion reducer so the UI can continue but the selected
   item is not moved to Done. N01/N07 must reject the wrong exact file bytes.
2. Change the genuine quit reducer to ignore `q`. The unchanged exact-exit route
   must reject the hang/timeout and retain the useful screen and cleanup result.
3. Change the genuine Markdown serializer to omit or duplicate one saved task
   while preserving the successful terminal transition. The state checkpoint
   must reject it in that same invocation.

Before any fault run, record the exact minimal source diff and pristine source
hash, pin the native toolchain, rebuild normally, bind the executed binary hash,
and prove baseline / mutated / restored behavior. Restore and hash-check source
even on failure. These are only candidate mutations; do not count any until
the real patch is independently reviewed and all required phases pass on both
claimed hosts.

## Freeze gate

This candidate set becomes a frozen declaration only after each exact action,
settled screen anchor, expected Markdown byte string, timeout, and platform
variant has been run and inspected. Drop or replace unsupported edges only
with a source-backed reason; record inapplicable service/child-process behavior
instead of simulating it. Then generate one unique case identity per materially
different task and run all declared cases in both native cells at the required
repetition count. No repetition or fault calibration is represented by this
draft.
