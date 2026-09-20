# Decisions, unresolved questions and scope control

Updated 19 September 2026. The [root roadmap](../../roadmap.md) fixes order; this register makes choices and revisit triggers visible. A proposed feature is not approved merely because it has a row.

## Decisions made for this batch

| ID | Decision | Reason and consequence |
| --- | --- | --- |
| D01 | Complete finite engineering batch and R6 before A1 recruitment | Explicit user preference; compensate with public research, operator pilots and a fixed stop at Sprint 14 |
| D02 | Verify existing S8/S9 native behavior early at 13-A0 | Platform/lifecycle risk should surface before new features amplify it |
| D03 | Five pilots before implementing full corpus | Broad 120-case inventory is useful; building every case before reducing blockers wastes work |
| D04 | Freeze executable/version before 3,000 repeats | Expensive results must apply to final candidate bytes; avoid a circular “finish campaign before freeze” gate |
| D05 | State checks have an explicit lifecycle contract | Successful workspace deletion prevents naive post-run inspection; use proven external resource/adapter/owned-cwd approaches |
| D06 | Existing report-v2 HTML is verification work | Source and S9 evidence already contain implementation; avoid speculative duplicate work |
| D07 | At most one compatibility family plus one conditional input/assertion family | A finite feature budget keeps breadth in tests rather than API surface |
| D08 | Manifest/reproduce commands conditional on failed manual handoff | Existing spec/report/fixture/version instructions may solve the task; no new replay system by default |
| D09 | Runner remains serial; corpus CI may shard independent jobs | Large validation volume does not justify a user-facing parallel scheduler |
| D10 | Native application claims are version/workflow/host-specific | Language diversity, framework examples and WSL do not prove all-platform compatibility |
| D11 | No version per sprint; no forced v1.0 | Releases express qualified coherent behavior and contract policy, not number of tasks completed |
| D12 | Documentation-only audit does not rerun PTY test suite | Check links, provenance, feasibility and consistency; later implementation must execute relevant tests |
| D13 | Defer Sprint 10 without a qualifying pilot blocker | All five admitted pilots complete their intended current flows; BT-06 redraw passes and no reduced application case demonstrates wrong terminal cells/protocol behavior. Reopen only with the evidence in the Sprint 10 decision record. |

## Decisions to make at explicit checkpoints

| ID | Question | Owner / deadline | Evidence needed / default |
| --- | --- | --- | --- |
| Q01 | Which terminal family blocks the most valuable pilot? | **Closed 2026-09-21: none qualifies; Sprint 10 deferred** | [Decision record](../validation/sprint-10-decision-2026-09-21.md); reopen only with a reduced failing real case and independent expectation |
| Q02 | Extra input or focused region? | Maintainer, 12-A exit | Two distinct admitted flows, failed recipe workaround, migration cost; neither justified → defer 12-B |
| Q03 | Does CI handoff need new software? | Maintainer, S6 decision | Try complete ordinary instructions on clean local context; default documentation |
| Q04 | Which candidate projects cannot meet host/task depth? | Corpus owner, 11-A1 | Exact pinned target attempts; replacement preserves interaction risk and counts |
| Q05 | What next version and compatible migration? | Release owner, R6-F | Actual public contract delta, old spec/report reader behavior, tag inventory; no number reserved here |
| Q06 | How to retain reproducible evidence affordably? | Corpus owner, before 11-B | Measured bytes/time, available CI retention, sanitized durable compact ledger; bounded failures/artifacts |
| Q07 | Is a comparison task fairly supported by all chosen tools? | Benchmark owner, 13-C pilot | Matching docs/pins and real PTY task; unsupported cells visible, not forced or scored as slow failures |
| Q08 | Can genuine installer upgrade be shown in this batch? | Release owner, R6-V | Same published immutable action SHA installs existing v0.3.0-rc.1 then new R6 release; otherwise future longitudinal check stays open without invented releases |
| Q09 | How do strict formats interact with patch-addition wording? | Release owner, before R6-F | SUPPORT.md permits optional patch additions, while readers reject unknown fields; explicitly distinguish new-reader/old-document compatibility from old-reader/new-document compatibility and freeze minimum-version/migration policy |

Do not silently pick a new format version during implementation. Document alternatives and cost at the relevant checkpoint; the maintainer reviews the concrete contract before it is presented as stable. Routine implementation choices within accepted scope do not need repeated permission requests.

## Backlog admission table

| Idea | Current disposition | Revisit trigger / smallest possible response |
| --- | --- | --- |
| JUnit | Deferred | A named CI consumer cannot ingest current evidence; one bounded exporter, no CI orchestration |
| Parallel runner | Deferred | Measured user suites exceed accepted duration after profiling; resource separation proven |
| Broad mouse input | Deferred | Two important keyboard-inaccessible adopter flows; selected protocol only |
| Styled snapshots | Deferred | Text cannot detect a real visual regression users need; reviewed representation and compatibility policy |
| Recorder/code generator | Deferred | A1 shows manual authoring causes repeated abandonment despite recipes; start with small template assistance |
| New SDK/language DSL | Deferred | Repeated retained users cannot express necessary deterministic flow in current contract |
| Failure minimization | Deferred | Stable reproducible failure identity and repeated manual shrinking burden |
| More installer channels | Deferred | Measured requested channel plus maintenance owner; archives/action remain useful |
| AI/MCP sessions | Outside batch | Separate product decision supported by actual user job; no autonomous game exploration |
| Hosted evidence/history | Deferred to A2 | Independent repeat use, repeated collaborative need and one paid pilot |
| Billing/accounts/PR bots | Deferred | Paid value and privacy/operating economics established; never a local-run prerequisite |

Every new accepted item needs task, evidence, minimum solution, regression proof, cost, owner and a displaced priority or later slot. A competitor release alone is not a trigger. Do not append pre-adoption sprints for these ideas.

## Main risks and early warning signals

| Risk | Early signal | Mitigation / stop condition |
| --- | --- | --- |
| Demand assumptions outlive engineering | New optional sprint added before A1 | Fixed batch; escalate scope change, then proceed to user validation |
| Test count inflation | Same flow renamed for hosts/viewports | Stable IDs, distinct-task review, separate repeat counters |
| Oracle validates the wrong state | Screen green but Git/file state differs | Independent exact state checks and failing-oracle controls |
| Adapter invalidates real-process coverage | Signals/input differ from direct launch | Native parity checks or use owned-cwd harness alternative |
| Dynamic data causes noisy snapshots | Baselines change without target defect | Control data, choose meaningful assertions, isolate limited region only if justified |
| Scope masking | Bad cell removed to get all-green report | Keep denominator and issue; previously promised correctness blocks promotion |
| CI cost/maintenance growth | Campaign exceeds measured estimate or artifacts explode | Pilot cost model, shard fixed work, preserve compact ledger, never weaken assertions to save time |
| Late freeze invalidates effort | Rebuilding runner/version after long campaign | R6-F precedes repeat campaign; hashes enforce evidence reuse |
| Overstated competitor win | Different target/host or tuned versus naive recipes | Matched protocol, unsupported states and losses published |
| Platform claim creep | Windows/WSL result described as three-host coverage | Native per-cell ledger; same release hashes as advertised |
| Release promises exceed staffing | SLA/support promises before an owner exists | Explicit maintenance boundary; commercial promises require costed paid pilot |

## Decision record form

Record ID/date, task/evidence, alternatives considered, selected smallest scope, exclusions, affected format/version, maintenance cost, acceptance proof, owner, and revisit trigger. Link it from the checkpoint and root roadmap. An unresolved question stays unresolved until evidence or an explicit scoped decision closes it.
