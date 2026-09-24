# Sprint 11: useful behavior across real applications

Status: **A0/A1 complete on 20 September 2026; B complete on 24 September 2026;
C planned after candidate freeze.** The checked admission artifacts, 15 project
records, 120 workflow specs, 300-cell focused map, controls, costs and exclusions
are in the [`corpus/` checkpoint](../../../corpus/README.md) and the
[B evidence](../../validation/sprint-11-b-corpus-depth-2026-09-24.md). Owner:
Playtestr maintainer.
Read the [root order](../../../roadmap.md), [validation program](../validation-program.md),
[120-intent catalog](../corpus-catalog.md), and [execution contract](../execution-contract.md).
This is internal engineering, with no recruitment dependency.

User result: a developer finds a reviewed recipe for a comparable application, runs it, and sees that the intended behavior and regression detection are actually checked.

## A0: five pilots, not a huge test framework

Completed at the admission boundary. The five records preserve their actual
Windows/WSL evidence, intended negatives, recovery and oracle ordering; WSL is
not promoted to native Linux. Cold acquisition timing remains the top campaign
measurement blocker and is not fabricated from old filesystem timestamps.

Start after or alongside independent parts of 13-A0. Admit the five catalog pilots for selection, Git mutation, prompt validation, resize/redraw and fresh-workspace state. Pin target/runtime versions and hashes, validate the real documented keyboard route, prepare local data, and verify expected behavior manually.

For each: three fresh known-good attempts, one intended-negative, and recovery. Record every attempt, setup time, execution time, postcondition and cleanup. These discovery repetitions are not the final qualification sample. Reduce blockers immediately; do not build all 120 workflows first.

Prove at least one independent state check before successful spec-v2 workspace deletion. Review the adapter/external-resource/owned-cwd choices in the catalog. Missing or failed oracle evidence fails the harness. Existing PowerShell trial infrastructure may be reused where it meets the boundary; a new portable helper, if necessary, stays test infrastructure in Go rather than becoming another product implementation.

Exit: five runnable pilot records, exact baseline expectations, native host availability, first cost estimate and ranked blockers. Stop to select the narrow compatibility/authoring repair before expanding code.

## A1: admission and coverage design

Completed as design/admission, not execution: 15 exact target identities and all
120 catalog intents are frozen. The 300-cell map identifies 99 reviewed existing
boundaries and 201 planned gaps. Unsupported/unrun hosts remain explicit. The
machine checks reject missing pins, host cells, workflow IDs and unresolved pilot
outcomes.

Review earlier campaigns without pooling different runner bytes or retries. Admit a 15-project roster with 120 distinct workflow IDs from the catalog; exact versions/hashes are required for admitted cases, while unadmitted candidates remain pending. Include licenses, install/build commands, dependency locks, clean state, external-resource ownership, time/output limits and disposal rules.

Map existing table-driven and PTY tests to the 300 focused risk cases. Existing meaningful cases count after review; function names alone do not establish case count. Mark gaps, unsupported hosts and unavailable prerequisites. Require at least five applications per advertised native host and three shared applications across all hosts by final qualification.

Exit: reviewed matrix and manifest, independently specified expected results, no fabricated green cells, targeted Sprint 10/12 entry evidence, a CI-local case for Sprint 6 evaluation, and a measured campaign estimate. A1 is the corpus checkpoint name here; maintainer adoption is separately named adoption A1 in the roadmap.

## B: complete depth and sensitivity

Completed 24 September 2026. All 15 exact pins have eight distinct implemented
workflows, an intended known-bad detection, and a passing recovery. The 300
focused cells reference exact reviewed test anchors and the 30 required
rejection/cancellation/boundary workflows are separately machine checked.
Application evidence is scoped to 13 native Windows targets plus two Linux
targets under WSL; it does not promote WSL to a native-host claim.

After selected repairs and integrated hardening, implement and run the full 120 admitted workflows and 300 focused risk cases. Keep target-specific state verification outside the core. At least two tasks per project exercise rejection, cancellation or a meaningful boundary. Avoid live-metric goldens and unnecessary snapshots where an exact selected output or state postcondition is clearer.

Each of the 15 projects needs a reviewed good/bad/recovered control. Target-source mutations or documented known-bad releases count as application-defect detection. Fixture variation can establish assertion sensitivity but must be labeled separately and cannot replace the required genuine defect control without an explicit revised acceptance decision. Budget target builds during admission; do not hide them in runner timing.

A negative succeeds as evidence only if the intended category/assertion or independent postcondition detects it. Unrelated launch failures, timeouts and crashes are not substitutes. Preserve the original baseline for good/bad/recovered runs. If the real screen passes while the independent result is wrong, the combined harness fails and retains both facts.

Exit: complete coverage map, explicit exclusions, intended defect controls and recovery, no unexplained false results or managed leaks. Support statements name application/version/host/workflow. If target selection cannot meet depth safely, revise the admission matrix visibly before claiming completion.

## C: qualify frozen bytes and maintenance

Entry is **R6-F candidate freeze**, after Sprint 13-D. Freeze embedded version/build flags and executable hash per host before the expensive sample. Reuse that executable from the extracted candidate archive. R6-Q consumes this evidence; do not run the same campaign twice because it has two milestone names.

Execute 10 selected workflows per native host × 100 fresh attempts = 3,000 executions, following the validation program's case composition and complete ledger. Run the full admitted application matrix against the same hashes. Do not double-count earlier discovery or competitor runs. Record cold starts, failure controls and recovery distinctly.

Add bounded PR/nightly/upgrade lanes with measured cost, pin ownership and fixture retirement procedure. Unexpected failures stop the affected qualification cell for diagnosis; retries never overwrite initial outcomes. New runner bytes require the invalidation policy, not a green result borrowed from another build.

Exit: complete frozen-byte ledger, native scope, supported/unsupported table, sanitized failure evidence, resource/cost summary and reproducible recipes. R6 public downloads still need hash comparison and post-publication smokes. Maintainer adoption remains later.

## Acceptance checkpoints

| Checkpoint | Required negative / cleanup proof | Artifact |
| --- | --- | --- |
| A0 | Wrong state despite screen success; oracle missing/error; fresh-state invariant | Five pilot records and oracle design |
| A1 | Unsupported host/task and missing pin reported as blocked, never passed | Admission manifest and coverage map |
| B | Intended defects, reject/cancel paths, original fixture unchanged, bounded target/harness cleanup | Specs/oracles, reviewed patches, result matrix |
| C | Repeated first-attempt outcomes, slow/cold cases, managed process absence, bounded artifact retention | Immutable candidate hash ledger and support table |

Manual demonstration: stage or write exact state through a real target, prove it independently, introduce the reviewed defect, inspect failure, restore the target and pass with unchanged baseline. Record exact commands rather than a proposed future CLI shortcut.

No new SDK, framework adapter API, hosted execution or parallel runner belongs here. Test helpers must not conceal the real PTY or process behavior they claim to prove.
