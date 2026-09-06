# Sprint 5 — Run suites and find failures in CI

Status: proposed; no commands below are implemented by this plan. Depends on release/adopter evidence in [R3](../release/03-real-project-trials.md). Primary outcome: a maintainer runs a growing test directory with one command and can identify every failed spec and its evidence.

## User problem and success measure

A project has a dozen menu/setup tests. Today it must enumerate every JSON file, and failure artifacts sit beside source specs. CI maintainers then assemble their own summary and file collection. Sprint 5 removes this repetitive plumbing while preserving sequential, deterministic execution.

Use one real adopter's multi-spec suite as the acceptance project. Measure its current command length/setup steps and the time needed to find a seeded failure. Success means one documented suite invocation selects the intended tests, the summary accounts for all selected tests, and a reviewer finds the failing spec and screen without scanning unrelated source directories.

## Entry gate and scope budget

Require either two independent reports of suite/CI friction or one adopted repository with a demonstrably awkward multi-spec command. Capture its expected selection set before implementation. The sprint delivers selection, artifact organization, summary, and JUnit as one suite workflow. It does not introduce test hooks, a config framework, workers, retries, tags in the spec, a browser dashboard, or package-manager installers.

## Proposed user workflow

```text
playtestr test --list tests/terminal
playtestr test --filter '*settings*' --artifacts-dir artifacts/playtestr --report artifacts/results.json --junit artifacts/results.xml tests/terminal
playtestr test 'tests/terminal/**/*.json'
```

These flags are proposals to validate at checkpoint 1. Keep flags before positional arguments consistent with the current Go CLI parser. Explicit existing file commands remain valid. No new spec fields are required.

## Contract decisions

| Area | Planned rule |
| --- | --- |
| Explicit paths | Preserve argument order for existing multi-file invocations. |
| Directories/globs | Expand each argument in place, sort matches by normalized relative path, and deduplicate by resolved file identity before launch. |
| Globs | Define a small documented grammar, including segment-level `**`; match separators consistently on Windows and Unix. Shell-expanded arguments also work. |
| Directory traversal | Recursively select `.json` specs; exclude documented artifact/cache directories; do not follow directory symlinks by default. Reject unreadable roots. |
| Filter | Match a normalized spec path with a documented glob, avoiding a spec-schema change for tags. |
| Empty selection | Usage/discovery error with nonzero status; never an empty green suite. |
| Execution | Serial, continuing after ordinary spec failure as today; cancellation stops launches and marks remaining selected specs `not_run`. |
| Update mode | Keep `--snapshot` restricted to one resolved spec. Reject ambiguous shared-baseline update targets before launching. |
| Reports | Keep report v1 output shape and order. Add JUnit as a separate writer over the same final results. |

Resolve all selections before launching. Bound the traversal and retained suite metadata: propose 10,000 visited entries, 1,000 selected specs, and 10,000 aggregate steps, plus the existing per-spec limits. Test these limits and adjust with actual suite evidence at checkpoint 1. Avoid collecting arbitrarily large result strings and only noticing the report limit at the very end.

## Evidence layout and collision rules

`--artifacts-dir` is opt-in; legacy adjacent artifacts remain the default for existing invocations. Create a unique subdirectory for each invocation under the selected root. Inside it, use safe spec identifiers derived from normalized relative paths and a collision-resistant suffix, not display names alone. Duplicate basenames from different folders must remain distinct.

Report references point to files actually written. Define paths relative to the report location where possible, including behavior when the report is on another Windows volume. If report v1 cannot support a change compatibly, preserve its existing paths and provide the new layout through a separately versioned manifest. Do not silently change the meaning of old path fields.

Reject output destinations that alias input specs or snapshot baselines. Keep stale files from earlier runs out of the current manifest. Directory creation or evidence-write failure must remain visible separately from the primary test failure. Do not delete arbitrary existing directories to get a clean run.

## JUnit contract

Emit one testcase per selected spec, with stable unique name/classname, duration in seconds, and a mapping consumers can rely on. Passed specs contain no failure. Product assertion/snapshot/unexpected-exit failures map to `failure`; invalid specs, launch, cleanup-only, or evidence infrastructure failures map to `error`. Cancelled and never-run specs map to skipped cases with explicit reasons, while the process still exits 130 on cancellation.

When a primary test failure and cleanup failure coexist, preserve both in bounded diagnostic text while counting one failed testcase. Do not add a second fake testcase for cleanup. Escape XML correctly, replace invalid XML code points, and omit environment data, command arguments, input, and embedded screen content. Validate with a parser and one actual CI consumer; there is no universal JUnit schema that proves every CI integration.

## Architecture and likely change surfaces

Create a small internal discovery component only when selection logic becomes larger than CLI parsing. Keep it separate from PTY execution. Adapt `cmd/playtestr` to orchestrate resolved paths and emit a human suite summary. Reuse `RunResult` and the current JSON writer; the JUnit writer cannot invent outcomes. Add an evidence destination option to the runner without giving artifact writers authority over pass/fail decisions.

Likely files: `cmd/playtestr/main.go`, `internal/runner/runner.go`, `internal/report`, a new internal discovery package, examples, README, and relevant schemas/docs if the contract actually changes. No broad package rewrite is part of this sprint.

## Checkpoints

### 5.1 — Freeze selection and output behavior

Write golden examples of input arguments and selected paths, including duplicate paths, zero matches, directory errors, case sensitivity, symlinks, and Windows separators. Set the resource caps and path alias policy. Review the proposed help text with the acceptance-project maintainer.

Acceptance: selection behavior is unambiguous, and existing file-list commands retain their order and exit behavior.

### 5.2 — Discover and list without launching

Implement directory/glob resolution, bounded traversal, deduplication, filtering, and `--list`. Prove a list operation cannot launch a helper process. Reject a zero-match request with an actionable message.

Acceptance: the adopter's expected suite list matches exactly on each supported host, with deterministic order for repeated runs.

### 5.3 — Execute a selected suite and summarize it

Connect selection to the existing serial runner. Print total/passed/failed/cancelled/not-run counts and stable failing spec paths. Preserve exact CLI status 0/1/2/130 semantics and reject usage issues before launch.

Acceptance: a suite with passes, an expected nonzero target exit, an intentional failure, and cancellation is accounted for correctly. A failed first spec does not silently prevent later ordinary specs from running.

### 5.4 — Organize evidence safely

Implement unique per-run destinations and collision-safe spec paths. Reject spec/baseline output aliasing, preserve prior run directories, and capture filesystem errors accurately. Keep the old adjacent-artifact path covered for compatibility.

Acceptance: two failing `menu.json` files in different folders generate independent files; a subsequent pass does not point to either stale failure.

### 5.5 — Export machine results for CI

Implement JUnit, exact summary mapping, atomic writes, and useful output-write errors. Run the generated XML through a parser and the chosen adopter CI test-results view. JSON and JUnit must describe the same requested suite and outcome.

Acceptance: CI displays the right failing spec and can download its evidence; cancellation produces an honest partial suite.

### 5.6 — Complete the adopter walkthrough

Run the suite from the installed binary, seed one regression, inspect JSON/JUnit/artifacts, fix it, and rerun. Update usage/examples and the deliberate-failure job if needed. Record the observed reduction in setup/diagnosis friction without inventing a percentage gain.

Acceptance: the maintainer can repeat the workflow using the documented command alone.

## Validation matrix

| Scenario | Required result |
| --- | --- |
| Explicit old command | Same ordered specs, baseline behavior, and status as before. |
| Mixed files/directory/glob | Documented expansion and deduplication, no missing tests. |
| No matches/unreadable directory | Nonzero selection failure, no launched target. |
| Traversal/symlink cycle | Bounded operation; no recursive loop or external directory traversal. |
| Two identical display names | Distinct JUnit identities and artifact locations. |
| Snapshot update collision | Prelaunch rejection or explicitly documented safe policy; no racing writes. |
| Cancellation mid-suite | Active target cleaned; remaining specs not run; partial outputs saved. |
| Report/evidence path aliases source | Rejected; original bytes preserved. |
| XML metacharacters/control characters | Parseable XML with bounded, accurate diagnostics. |
| Large discovered suite | Limits fail predictably without exhausting memory. |

Run pure selection/writer tests and real-PTY suite tests. Run Go tests/vet and native CI on advertised hosts; run the race detector for orchestration/lifecycle changes. Validate only changed behavior beyond the standard suite, avoiding redundant repeated runs without a concern to investigate.

## Definition of done and handoff

- [ ] Checkpoints 5.1–5.6 evidenced, including negative/cancellation paths.
- [ ] One real project uses directory selection and CI results successfully.
- [ ] Existing explicit-file and report-v1 consumers keep working.
- [ ] Artifact layout, limits, JUnit mapping, and commands documented.
- [ ] No parallelism, implicit retries, or baseline auto-approval slipped into scope.

Handoff to Sprint 6: stable spec identity, per-run artifact root, ordered outcome model, and one actual CI failure that was difficult to reproduce locally. If JUnit proves irrelevant to the selected adopter, replace that checkpoint only after documenting the unmet user need and a smaller end-to-end scope.
