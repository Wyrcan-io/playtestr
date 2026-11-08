# Continuation checkpoint v47: 9 November 2026

Branch `work/p0-p2-implementation` is based on pushed commit `9a56ec99`.
Campaign status remains four of twenty new projects qualified on exact rc.6
(14/30 cumulative); eight new applications have some historical admission,
including four rc.5-only. The original ten have zero current-candidate rc.6
qualification. No credit is added by this checkpoint.

## Skim

Run `42506300345` remains the independently audited exact rc.6 Linux/Windows
series packet: 240 ordinary outcomes and nine fault phases per host. Readback
v8 records both provider archive digests, exact candidate/target identities,
every batch/report/finished receipt hash, 240 unique invocation IDs per host,
passed report steps, and checked cleanup. Public route and campaign closure are
still required for admission.

Preserve the later zero-launch failures:

* Run `42512413573` refused contract freeze on both hosts because V29's workflow
  source hash was stale. No final series started.
* Run `42513718526` Linux again refused freeze with
  `Skim final harness changed after declaration:
  .github/workflows/runner-readiness-next20-skim-final.yml`; no target cases
  launched. Its Windows job remained in progress at last inspection.

V30 was generated immutably before discovering that its test and independent
plan-audit consumers still pointed at V29. Preserve V30 as superseded. V31 now
binds the current workflow, public route, final-series planner, test and plan
auditor from staged bytes. Its targeted local suite passed 28 tests with four
native-platform skips. Exact comparison of all 55 declared harness entries and
the final workflow freeze must pass in the next hosted attempt before any target
execution. Candidate remains unchanged rc.6. Skim is uncredited.

Hosted source development run `42513718435` passed Linux's 20 source-built
cases; its Windows job was still running the three source faults at last check.
This is development evidence, not exact-archive admission evidence.

## Taskell

The previous exact run `42512546590` retained its first failure: Linux passed
the upstream suite and native build but case E11M failed in batch 11; remaining
series outcomes are not counted. macOS failed before target execution because
the signed LLVM closure references bundled `libxml2.16.dylib` and
`libz.1.dylib` that the owned prefix does not yet include. The matching fault
workflow also failed at that bounded setup point.

The corrected run `42513404363` at `17ce3f80` is still active on Linux upstream
tests; its macOS job again failed at those two missing package dependencies.
Fault run `42513404405` Linux was building the pristine runtime at last check;
macOS likewise failed before runtime/fault execution. Do not count candidate
cells or fault phases until the exact current runs finish and evidence audits.
Helper suite last passed 10 tests (two Windows-only symlink skips).

## Next actions

1. Verify V31's 55 staged harness hashes locally, stage its immutable JSON and
   checkpoint/docs, and inspect the exact staged diff.
2. Commit and push the scoped V31 correction using the existing authorization.
   Let its exact native Skim workflow reach and pass freeze before target launch;
   audit all newly produced artifacts independently.
3. Inspect the Taskell E11M report from its retained artifact and solve the
   actual contract/runtime mismatch. For macOS, acquire only the reviewed,
   signature-verified dependency families needed to close LLVM's recursive
   dylib graph; keep extraction bounded and reject unresolved or escaping links.
4. Continue project selection and qualification sequentially after Skim and
   Taskell target cleanup. Do not start another external application while
   either native attempt still owns a target/runtime tree.

Protected ignored directories `.codex-go-cache/` and `.codex-test-tmp/` remain
untouched. Do not claim 30/30, Skim admission, Taskell admission, or original-ten
rc.6 qualification.
