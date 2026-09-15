# Sprint 5 — Run a small CI suite and find its failures

Status: engineering implementation complete locally on 15 September 2026; independent adopter acceptance remains open under [R3](../release/03-real-project-trials.md). See the [Sprint 5 engineering validation](../../validation/sprint-5-engineering-2026-09-15.md). Primary outcome: a maintainer runs an intended test directory serially with one command and can identify every failed spec and its evidence.

Scope refined after the [September 2026 competitive assessment](../../research/competitive-assessment-2026-09.md) and [product-focus rule](../product-focus.md). Active alternatives already provide broad automation and installation surfaces. This sprint deliberately owns one narrower job: deterministic suite selection and honest failure evidence. A setup action, package manager, recorder, retries, parallel workers, tags, config framework, and hosted upload are separate products or later evidence-backed responses.

## User problem and success measure

A project has a dozen menu/setup tests. Today it must enumerate every JSON file, and failure artifacts sit beside source specs. CI maintainers then assemble their own summary and file collection. Sprint 5 removes this repetitive plumbing while preserving sequential, deterministic execution.

Use one real adopter's multi-spec suite as the acceptance project. Measure its current command length/setup steps and the time needed to find a seeded failure. Success means one documented suite invocation selects the intended tests, the summary accounts for all selected tests, and a reviewer finds the failing spec and screen without scanning unrelated source directories.

The summary is also the sprint's demonstration surface: show stable spec paths,
plain pass/fail counts, the first failed step/category, and the exact evidence
location. Make it crisp enough for a maintainer to understand at a glance, but
do not add spinners, a runner TUI, animation, or a dashboard. The existing
website pass/failure/recovery demonstration remains the public visual showcase.

## Entry gate and scope budget

Require a documented project case with an awkward multi-spec command or scattered CI evidence. Capture its expected selection set before implementation. An operator reproduction can justify bounded engineering while independent trials continue; it does not count as adoption. The sprint delivers directory selection, serial execution, artifact organization, and a human summary. JUnit is a conditional interoperability addition when the acceptance project uses a CI test-results viewer. Custom globs and filtering also require a demonstrated selection task. Exclude test hooks, a config framework, workers, retries, tags, a runner dashboard, hosted upload, setup actions, and package-manager installers.

## Proposed user workflow

```text
playtestr test --list tests/terminal
playtestr test --artifacts-dir artifacts/playtestr --report artifacts/results.json tests/terminal
```

These flags are proposals to validate at checkpoint 1. Keep flags before positional arguments consistent with the current Go CLI parser. Explicit existing file commands remain valid. No new spec fields are required.

The final workflow may use existing documented release installation and the current JSON report. `--junit` is conditional on the acceptance project's evidence consumer; it is not a default promise. The planned suite behavior must not change how an explicit existing list of spec files runs.

## Contract decisions

| Area | Planned rule |
| --- | --- |
| Explicit paths | Preserve argument order for existing multi-file invocations. |
| Directories/globs | Expand each argument in place, sort matches by normalized relative path, and deduplicate by resolved file identity before launch. |
| Globs | Conditional on an actual selection task. If selected, define a small grammar including segment-level `**`, consistent across hosts. Existing shell-expanded explicit arguments work independently. |
| Directory traversal | Recursively select `.json` specs; exclude documented artifact/cache directories; do not follow directory symlinks by default. Reject unreadable roots. |
| Filter | Conditional on an actual selection task. If selected, match normalized spec paths with the documented glob grammar. |
| Empty selection | Usage/discovery error with nonzero status; never an empty green suite. |
| Execution | Serial, continuing after ordinary spec failure as today; cancellation stops launches and marks remaining selected specs `not_run`. |
| Update mode | Keep `--snapshot` restricted to one resolved spec. Reject ambiguous shared-baseline update targets before launching. |
| Reports | Keep report v1 output shape and order. Add JUnit only when checkpoint 5.1 records the acceptance project's actual CI consumer; it must derive from the same final results. |

Resolve all selections before launching. Bound the traversal and retained suite metadata: propose 10,000 visited entries, 1,000 selected specs, and 10,000 aggregate steps, plus the existing per-spec limits. Test these limits and adjust with actual suite evidence at checkpoint 1. Avoid collecting arbitrarily large result strings and only noticing the report limit at the very end.

## Evidence layout and collision rules

`--artifacts-dir` is opt-in; legacy adjacent artifacts remain the default for existing invocations. Create a unique subdirectory for each invocation under the selected root. Inside it, use safe spec identifiers derived from normalized relative paths and a collision-resistant suffix, not display names alone. Duplicate basenames from different folders must remain distinct.

Report references point to files actually written. Define paths relative to the report location where possible, including behavior when the report is on another Windows volume. If report v1 cannot support a change compatibly, preserve its existing paths and provide the new layout through a separately versioned manifest. Do not silently change the meaning of old path fields.

Reject output destinations that alias input specs or snapshot baselines. Keep stale files from earlier runs out of the current manifest. Directory creation or evidence-write failure must remain visible separately from the primary test failure. Do not delete arbitrary existing directories to get a clean run.

## Conditional JUnit contract

Implement this section if checkpoint 5.1 identifies an existing CI results consumer for JUnit. Emit one testcase per selected spec, with stable unique name/classname, duration in seconds, and a mapping consumers can rely on. Passed specs contain no failure. Product assertion/snapshot/unexpected-exit failures map to `failure`; invalid specs, launch, cleanup-only, or evidence infrastructure failures map to `error`. Cancelled and never-run specs map to skipped cases with explicit reasons, while the process still exits 130 on cancellation.

When a primary test failure and cleanup failure coexist, preserve both in bounded diagnostic text while counting one failed testcase. Do not add a second fake testcase for cleanup. Escape XML correctly, replace invalid XML code points, and omit environment data, command arguments, input, and embedded screen content. Validate with a parser and one actual CI consumer; there is no universal JUnit schema that proves every CI integration.

## Architecture and likely change surfaces

Create a small internal discovery component only when selection logic becomes larger than CLI parsing. Keep it separate from PTY execution. Adapt `cmd/playtestr` to orchestrate resolved paths and emit a human suite summary. Reuse `RunResult` and the current JSON writer; an approved JUnit writer cannot invent outcomes. Add an evidence destination option to the runner without giving artifact writers authority over pass/fail decisions.

Likely files: `cmd/playtestr/main.go`, `internal/runner/runner.go`, `internal/report`, a new internal discovery package, examples, README, and relevant schemas/docs if the contract actually changes. No broad package rewrite is part of this sprint.

## Checkpoints

### 5.1 — Freeze selection and output behavior

Write golden examples of input arguments and selected paths, including duplicate paths, zero matches, directory errors, case sensitivity, symlinks, and Windows separators. Set the resource caps and path alias policy. Decide whether the acceptance project's CI genuinely needs JUnit instead of the existing JSON report and artifacts. Review the proposed help text with the acceptance-project maintainer.

Acceptance: selection behavior is unambiguous, existing file-list commands retain their order and exit behavior, and any additional result format has one demonstrated consumer.

### 5.2 — Discover and list without launching

Implement directory resolution, bounded traversal, deduplication, and `--list`. Add custom glob/filter behavior only if selected in 5.1. Prove a list operation cannot launch a helper process. Reject a zero-match request with an actionable message.

Acceptance: the adopter's expected suite list matches exactly on each supported host, with deterministic order for repeated runs.

### 5.3 — Execute a selected suite and summarize it

Connect selection to the existing serial runner. Print total/passed/failed/cancelled/not-run counts and stable failing spec paths. Preserve exact CLI status 0/1/2/130 semantics and reject usage issues before launch.

Acceptance: a suite with passes, an expected nonzero target exit, an intentional failure, and cancellation is accounted for correctly. A failed first spec does not silently prevent later ordinary specs from running.

### 5.4 — Organize evidence safely

Implement unique per-run destinations and collision-safe spec paths. Reject spec/baseline output aliasing, preserve prior run directories, and capture filesystem errors accurately. Keep the old adjacent-artifact path covered for compatibility.

Acceptance: two failing `menu.json` files in different folders generate independent files; a subsequent pass does not point to either stale failure.

### 5.5 — Export JUnit only when the adopter needs it

If checkpoint 5.1 approved JUnit, implement exact summary mapping, atomic writes, and useful output-write errors. Run the generated XML through a parser and the chosen adopter CI test-results view. JSON and JUnit must describe the same requested suite and outcome. Otherwise, record that report v1 plus the human summary were sufficient and omit this checkpoint's code.

Acceptance: CI displays the right failing spec and can download its evidence; cancellation produces an honest partial suite.

### 5.6 — Complete the adopter walkthrough

Run the participant-owned CI workflow using the existing documented released-binary installation, seed one regression, inspect the selected report/evidence output, fix it, and rerun. Use read-only repository permissions where possible and upload only the explicit artifact root with finite retention. Update usage/examples and the deliberate-failure job if needed. Record the observed reduction in suite/diagnosis friction without inventing a percentage gain.

Acceptance: the maintainer can repeat the workflow using the documented command alone. Apply the [demo acceptance](../product-focus.md#demo-acceptance) to the same shipped suite workflow. If independent participation is unavailable, record engineering completion and keep this adoption check open.

## Validation matrix

| Scenario | Required result |
| --- | --- |
| Explicit old command | Same ordered specs, baseline behavior, and status as before. |
| Mixed files/directories, plus globs if selected | Documented expansion and deduplication, no missing tests. |
| No matches/unreadable directory | Nonzero selection failure, no launched target. |
| Traversal/symlink cycle | Bounded operation; no recursive loop or external directory traversal. |
| Two identical display names | Distinct artifact locations and, if JUnit is selected, distinct JUnit identities. |
| Snapshot update collision | Prelaunch rejection or explicitly documented safe policy; no racing writes. |
| Cancellation mid-suite | Active target cleaned; remaining specs not run; partial outputs saved. |
| Report/evidence path aliases source | Rejected; original bytes preserved. |
| XML metacharacters/control characters, if JUnit selected | Parseable XML with bounded, accurate diagnostics. |
| Large discovered suite | Limits fail predictably without exhausting memory. |

Run pure selection/writer tests and real-PTY suite tests. Run Go tests/vet and native CI on advertised hosts; run the race detector for orchestration/lifecycle changes. Validate only changed behavior beyond the standard suite, avoiding redundant repeated runs without a concern to investigate.

## Definition of done and handoff

- [x] Checkpoints 5.1–5.5 have local engineering evidence, including negative and cancellation paths; checkpoint 5.6's documented operator fallback is complete.
- [ ] One independent real project uses directory selection and CI results successfully; no qualifying participant was supplied, so this adoption gate remains open as required.
- [x] Existing explicit-file and report-v1 consumers keep working.
- [x] Artifact layout, limits, and commands are documented; JUnit was omitted because no actual results consumer was identified.
- [x] No parallelism, implicit retries, or baseline auto-approval slipped into scope.

Stop and review repeat use after this milestone. The recommended next candidate is Sprint 7's compact offline report, which reuses this evidence layout. Sprint 6 remains conditional on missing reproduction context. Record omitted optional work and separate completed engineering from any pending participant evaluation.
