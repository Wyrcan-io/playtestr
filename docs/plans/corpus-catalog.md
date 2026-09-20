# Proposed corpus: 120 workflow intents

Status: **design inventory, not implemented tests or compatibility evidence**. Each project has eight candidate user tasks below. IDs make omissions, duplication and scope changes reviewable. Sprint 11 admits exact versions and actual supported routes before implementation; a listed task may need replacement if that pinned application cannot perform it. Never modify the application just to make a proposed feature exist.

The [validation program](validation-program.md) owns acceptance, native breadth, counting and execution budgets. The [root roadmap](../../roadmap.md) owns order. A case is complete only with its actual spec, independently justified expectation, host scope, bounded setup and cleanup, attempt evidence and review. An interface framework or language name alone is not coverage.

## Five pilots first

Begin with `GUM-01` selector, `LG-01` Git mutation, `CV-01` wizard, `BT-06` resize/help and `LG-08` fresh workspace. Verify admission of the pinned UI paths before using these IDs. If a required key or host is unavailable, record the blocker and select a documented comparable pilot without erasing the original result.

For each pilot run manual known-good once, automated known-good three fresh times, one intended-negative and recovery. These are cheap development discovery runs, not final 100-repeat qualification. At least one pilot must prove an independent state check executes before successful workspace deletion. Record cold setup separately from target runtime and assertion waiting.

## Core selection and repository tools

| ID | User task | Expected observable result / independent check |
| --- | --- | --- |
| GUM-01 | Choose the second item | Exact emitted selection and expected exit |
| GUM-02 | Filter then choose one matching item | Exact selected record; original candidate data unchanged |
| GUM-03 | Confirm an explicit yes choice | Declared yes result/status, no unexpected file writes |
| GUM-04 | Reject a confirmation | Declared no result/status, not confused with runner cancellation |
| GUM-05 | Enter then correct text | Exact final emitted text, including intended edit |
| GUM-06 | Accept a documented default value | Default appears and exact default is returned |
| GUM-07 | Select multiple items where supported | Exact set/order under pinned semantics; no duplicates |
| GUM-08 | Cancel before committing selection | Documented target status, no accepted value |
| LG-01 | Stage one named file | Git cached diff contains only that path and exact intended change |
| LG-02 | Unstage one staged file | Cached diff removed; worktree edit remains |
| LG-03 | Commit the selected change | Exact commit message/tree; unrelated file still unstaged |
| LG-04 | Cancel commit editing | HEAD unchanged; no new commit or unintended staged mutation |
| LG-05 | Switch to a reviewed local branch | Symbolic HEAD is exact branch; fixture invariants preserved |
| LG-06 | Search/navigate a specific change | Correct visible file/hunk; Git state unchanged |
| LG-07 | Open and close help after resizing | Fresh help visible, then absent; primary view usable; no Git mutation |
| LG-08 | Reopen without stale draft/config | Fresh spec-v2 home/workspace, single intended input; original config/fixture unchanged |
| FZF-01 | Filter to and accept one exact record | Exact stdout record and target exit |
| FZF-02 | Move selection among multiple matches | Output is the explicitly selected matching record |
| FZF-03 | Clear query and select another record | No stale filter; exact new selection |
| FZF-04 | Cancel selection | Documented target exit and no successful output selection |
| FZF-05 | Search with no matches | Explicit empty-result behavior; bounded user exit |
| FZF-06 | Toggle multi-selection | Exact accepted set and order per pinned options |
| FZF-07 | Select a path containing spaces | Exact uncorrupted record, source file unchanged |
| FZF-08 | Resize then accept current match | Expected visible result survives redraw; exact stdout |

## Python projects

| ID | User task | Expected observable result / independent check |
| --- | --- | --- |
| POST-01 | Send deterministic local GET | Local server receives exact method/path; expected response shown |
| POST-02 | Edit query parameters | Parsed request query matches expected values exactly |
| POST-03 | Send body using chosen method | Server logs exact method/body hash, no external endpoint |
| POST-04 | Change one request header | Server receives intended synthetic header, no unrelated secret |
| POST-05 | Save a named request | Collection document fields/path match reviewed expectation |
| POST-06 | Reopen a saved request | Visible fields and subsequent local request match saved values |
| POST-07 | Handle a local connection failure | Useful failure state, bounded exit, no fabricated success |
| POST-08 | Cancel edits or dismiss help | Selected prior request/state remains as specified |
| LITE-01 | Query a known table | Exact ordered rows from disposable SQLite fixture |
| LITE-02 | Insert one record | External query observes exact new row and row count |
| LITE-03 | Reject invalid SQL then recover | Error followed by correct query result; database unchanged by invalid statement |
| LITE-04 | Complete a known table/column | Correct completion and executed query result |
| LITE-05 | Recall a prior query | Chosen history entry executes once with exact result |
| LITE-06 | Cancel an unfinished statement | No partial mutation; next valid query works |
| LITE-07 | Inspect empty query results | Explicit empty result and unchanged database |
| LITE-08 | Quit and reopen in clean state | Exact exit; fresh home/history policy; original fixture unchanged |
| MITM-01 | Open a recorded offline flow | Exact method/host/path visible from synthetic fixture |
| MITM-02 | Filter to one known flow | Intended request remains, other request absent where observable |
| MITM-03 | Clear filter and navigate | Full expected list returns; correct selected flow |
| MITM-04 | Inspect response details | Known status/body marker visible; no external network |
| MITM-05 | Inspect request headers | Synthetic expected header present and matched to correct flow |
| MITM-06 | Export a selected flow if supported | Export contains the selected record; input fixture unchanged |
| MITM-07 | Open help, resize, then dismiss | New geometry redraw and meaningful return-to-list condition |
| MITM-08 | Quit with and without changes | Documented exit; no input-fixture modification or leaked process |

## Rust projects

| ID | User task | Expected observable result / independent check |
| --- | --- | --- |
| BT-01 | Open and close help | Observed modal appears/disappears after explicit input |
| BT-02 | Filter process list to controlled helper | Exact unique helper identity, not a changing host PID golden |
| BT-03 | Change documented sort order | Stable controlled helper ordering under admitted metrics |
| BT-04 | Clear a process filter | Target's full-view marker/state restored, helper still observable |
| BT-05 | Enter and leave expanded widget | Distinct view markers and usable return path |
| BT-06 | Resize continuously repainting screen | Fresh redraw evidence and required controls at declared dimensions |
| BT-07 | Exercise empty-match filter | Explicit no-match behavior, then successful recovery |
| BT-08 | Quit during active refresh | Declared target exit; no managed descendants left |
| GUI-01 | Stage one file | Exact cached diff, unrelated file excluded |
| GUI-02 | Unstage one file | Worktree change retained, cached change removed |
| GUI-03 | Commit staged changes | Exact message/tree and one new commit |
| GUI-04 | Cancel commit input | HEAD/index match expected cancellation policy |
| GUI-05 | Inspect known history entry | Correct commit identity/detail and unchanged repository |
| GUI-06 | Navigate file diff | Correct file/hunk text, unchanged Git state |
| GUI-07 | Help/resize/close help | Correct observed state transitions and repository invariant |
| GUI-08 | Handle empty working tree | Explicit clean state, no accidental stage/commit |
| TV-01 | Filter and accept an exact line | Exact stdout selection |
| TV-02 | Move among matching candidates | Accepted item matches explicitly selected record |
| TV-03 | Clear search and select another | New query state with no stale match |
| TV-04 | Handle a no-match query | Documented empty-result behavior followed by bounded exit |
| TV-05 | Cancel selection | Correct non-success target outcome, input unchanged |
| TV-06 | Accept supported non-ASCII text | Exact output bytes; layout claim limited to tested characters |
| TV-07 | Inspect a controlled preview | Preview marker belongs to selected file; no file mutation |
| TV-08 | Resize filtered selection | Fresh redraw and exact accepted record |

## Node.js projects

| ID | User task | Expected observable result / independent check |
| --- | --- | --- |
| NPK-01 | Discover synthetic dependency trees | Expected known directories present; real home excluded |
| NPK-02 | Navigate to named tree | Exact selection marker; every fixture hash unchanged |
| NPK-03 | Filter a named tree if available | Correct visible match set, no writes |
| NPK-04 | Reorder by documented criterion | Controlled fixture ordering; no deletion |
| NPK-05 | Inspect an empty root | Explicit empty state, bounded exit |
| NPK-06 | Use reviewed dry-run action | Expected dry-run indication; all marker hashes unchanged |
| NPK-07 | Resize then return to selected tree | Correct identity after redraw; no file loss |
| NPK-08 | Cancel/quit scanning or selection | Exit/cleanup confirmed; synthetic trees intact |
| CV-01 | Scaffold minimal JavaScript project | Exact admitted file manifest and package fields |
| CV-02 | Select TypeScript variant | TypeScript-specific expected files/fields, no runtime installation |
| CV-03 | Select a second supported framework | Exact framework template marker and dependency fields |
| CV-04 | Correct invalid package name | Rejection then valid output path/package name |
| CV-05 | Refuse overwrite of nonempty directory | Sentinel contents unchanged; clear canceled/refused result |
| CV-06 | Cancel wizard before creation | No scaffold written; exact documented target exit |
| CV-07 | Use reviewed nested output directory | Files only under intended owned path; neighbor sentinel unchanged |
| CV-08 | Decline optional install/start steps | Scaffold produced with no package installation or dev-server child |
| IPM-01 | Create a dark theme | Exact package fields and stylesheet manifest |
| IPM-02 | Create a light theme | Correct variant metadata; no unrelated files |
| IPM-03 | Reject invalid theme type then correct | Rejection observed, one valid scaffold only |
| IPM-04 | Set a reviewed package name | Exact accepted package identifier and file paths |
| IPM-05 | Handle an existing destination | Refusal/confirmation policy preserves neighbor sentinel |
| IPM-06 | Cancel before write | Destination invariants and expected target status |
| IPM-07 | Edit a field before submission | Only final value stored; no duplicate stale input |
| IPM-08 | Repeat from fresh state | Same reviewed logical output; original fixture unchanged |

## Additional interaction diversity

| ID | User task | Expected observable result / independent check |
| --- | --- | --- |
| MICRO-01 | Edit and save a file | Exact saved bytes and unchanged neighbor sentinel |
| MICRO-02 | Undo an edit before saving | Exact original content restored |
| MICRO-03 | Find known text | Visible occurrence selection, file bytes unchanged |
| MICRO-04 | Replace selected text | Exact expected replacement and occurrence count |
| MICRO-05 | Cancel unsaved close | Editor remains usable; disk content unchanged |
| MICRO-06 | Discard unsaved changes | Exit with original disk bytes preserved |
| MICRO-07 | Switch among two owned buffers | Correct text per buffer; no cross-file write |
| MICRO-08 | Resize and save supported Unicode text | Exact saved bytes and independently checked supported layout |
| TIG-01 | Select a known commit | Exact commit identity and unchanged repository |
| TIG-02 | Inspect a known diff | Intended file/hunk visible; Git index/worktree unchanged |
| TIG-03 | Search a history entry | Correct matched commit |
| TIG-04 | Return from detail to list | Explicit observed view transition |
| TIG-05 | View a known branch history | Correct branch/commit sequence without branch mutation |
| TIG-06 | Open and dismiss help | Help observed then absent; main screen restored |
| TIG-07 | Resize with a selected commit | Selection/detail remains correct after redraw |
| TIG-08 | Quit from a nested view | Documented exit; no repository change or process leak |
| TASK-01 | Filter to one synthetic task | Exact task identity; external export unchanged |
| TASK-02 | Add a task through supported route | External export contains one exact new task |
| TASK-03 | Complete selected task | Only selected task changes status |
| TASK-04 | Cancel a destructive/complete action | Export unchanged; correct return view |
| TASK-05 | Edit a task description | Exact new description, no duplicated input |
| TASK-06 | Clear filter/show empty result | Correct visible set and unchanged task data |
| TASK-07 | Help and resize | Required controls visible after redraw; data invariant |
| TASK-08 | Quit/reopen with owned config/data | Expected state retention/reset policy and untouched source fixture |

## Admission and replacement rules

This catalog tests runner interaction diversity; it is not an attempt to test each target exhaustively. Use safe local data, disable first-run external calls where documented, and do not assert unstable CPU/time/download text as a whole-screen golden. Unsupported input is a recorded finding. Use ordinary documented keyboard routes, not hidden raw bytes to bypass the intended key contract.

New candidate fzf, micro, tig and taskwarrior-tui workflows need fresh admission. Existing evidence for the other eleven projects is a starting point, not proof of the eight new tasks or current bytes. The earlier Lazydocker/K9s campaign remains historical evidence; retain one optional isolated Docker/Kubernetes challenge lane only when infrastructure is available and bounded. It does not replace the deterministic offline release gate or imply production-infrastructure support.

If a target cannot supply eight meaningful distinct tasks, redistribute tasks to other admitted targets or replace it while retaining 15 independent projects and 120 distinct tasks. Record old ID, reason, replacement ID and risk coverage. Do not count repeated viewports/hosts/input strings as separate tasks unless the behavioral contract changes materially. At least two cases per project should exercise a user-visible rejection/cancellation/boundary, rather than only successful navigation.

## State-oracle implementation boundary

The runner deletes successful spec-v2 workspaces before returning. **A post-run oracle cannot inspect an already deleted successful workspace.** Choose and document one of these harness approaches before admission:

1. For external state (controlled HTTP service, disposable database outside the copied root), the harness owns that isolated resource and checks it after the target exits. Cleanup remains the harness's responsibility.
2. For files/Git inside a successful workspace, use a reviewed test-only launch adapter that starts the real target with inherited terminal handles, waits for it, checks exact state before returning, and exits with a distinct oracle-failure status. The spec must assert successful completion of the adapter. Preserve and record the real target exit separately. Prove the adapter does not swallow input/signals, change process-group behavior, or substitute fake target output. Test direct-launch and adapter parity on every admitted native host.
3. Where an adapter changes the behavior under test, use a harness-owned disposable directory with an ordinary v1 `cwd`, then inspect state and clean it externally. Label this as an application E2E case, not proof of spec-v2 automatic workspace cleanup. Separate dedicated v2 lifecycle tests still cover that feature.

Prefer the simplest proven approach per case. The adapter is test infrastructure, not a new Playtestr assertion language. Do not add “retain successful workspaces” to the product to simplify the harness. Never force a deliberate failure just to keep state and then call that a passing successful-workspace test.

For wrong-state controls, intentionally return the oracle-failure status while screen assertions succeed: the **combined harness must fail** and explain that the screen did not prove state. Include adapter timeout, signal forwarding, child cleanup, failed oracle, malformed result, partial result and missing result. Missing independent evidence cannot default to pass.
