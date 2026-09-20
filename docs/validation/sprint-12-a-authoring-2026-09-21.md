# Sprint 12-A authoring and diagnostics evidence

Date: 2026-09-21. Source checkpoint: `ebc5f7c` plus the Sprint 12-A changes
committed with this record. Host: Windows amd64. This is maintainer-operated
engineering evidence, not an independent usability result or a claim about
Linux or macOS application behavior.

## Result

Sprint 12-A is complete. The public [recipe index](../recipes/README.md) provides
three short spec-v1 flows with exact prerequisites, positive readiness,
independent outcomes where screen text is insufficient, deliberate failures,
recovery, and safe cleanup instructions. No init, validate, recorder, new
action, schema version, or automatic unreviewed baseline generation was needed.

| Recipe | Pin and proof | Pass / deliberate failure / recovery | Measured setup and runs |
| --- | --- | --- | --- |
| Selector | Gum 0.17.0; exact `Beta` snapshot and exit 0 | 5/5 pass; wrong-selection control exited 1 with `snapshot_mismatch` and `Beta` to `Alpha` diff; unchanged recipe 5/5 pass | retained binary; 424 ms / 396 ms / 377 ms |
| Stateful wizard | create-vite 9.2.1 retained tarball; parsed package and required-file oracle, no project `node_modules` | 11/11 pass plus oracle; wrong package-name oracle exited 1; correct oracle passed; deleted owned project and clean rerun passed 11/11 plus oracle | local tarball install 25.013 s; initial run 611 ms; oracle 652 ms; clean recovery 747 ms |
| Full-screen modal/resize | bottom 0.14.9; exact helper PID/executable oracle | 19/19 pass; absent marker exited 1 with `assertion_timeout` at step 7; fresh marker recovered 19/19 and passed identity oracle | helper build/copy 1.577 s; 6.858 s / 5.192 s / 2.767 s |

Target identities are pinned in [`corpus/manifest.json`](../../corpus/manifest.json).
The create-vite project and both marker processes were owned by the harness.
The project path was resolved and checked below the recipe root before deletion;
each process path was checked before its exact PID was stopped.

## Ten authoring mistakes

The focused regression tests execute these cases. Syntax and semantic failures
below reject before launch and do not copy typed text into diagnostics. Missing
baseline existence remains an execution-time artifact check under the current
contract, after a clean target exit; its error points to `--update`.

| Mistake | Timing | Category and next useful context |
| --- | --- | --- |
| Wrong version | Before launch | `invalid_spec`; unsupported version value |
| Unknown field | Before launch | `invalid_spec`; exact misspelled field |
| Invalid key | Before launch | `invalid_spec`; step number and key |
| Mixed actions | Before launch | `invalid_spec`; step number and one-action rule |
| Missing command | Before launch | `invalid_spec`; command requirement |
| Malformed duration | Before launch | `invalid_spec`; duration field decode context |
| Missing baseline | During execution | `artifact_failure`; baseline name and `--update` action |
| Snapshot without readiness | Before launch | `invalid_spec`; step, snapshot, and required successful `expect`/exit |
| Workspace path escapes fixture | Before launch | `invalid_spec`; field and below-fixture constraint |
| Empty selection | Before launch | CLI exit 2; select a `.json` file or directory containing specs |

Only two diagnostics required code changes: unknown keys and invalid snapshot
paths now include their step number. Regression coverage also proves eight
invalid specs do not launch or enter cleanup, missing-baseline timing stays
accurate, and empty selection explains the next selection action. A manual
invalid-key run exited 1 in 24 ms with `step 1 unknown key "F13"`; its sentinel
command was never launched.

## Authoring journey and limitations

The copy-and-adapt manual demo changed the selector to choose `Gamma`, added its
reviewed exact baseline, and passed all six steps. The measured interval from
starting the copy/edit through the completed run was 32.1 seconds. This is a
single experienced-maintainer measurement with warm tools and excludes target
acquisition, so it is only a lower-bound engineering observation.

The journey was: reuse verified prerequisite; first launch; preserve positive
header readiness; edit the input and exact accepted-output baseline; run the
invalid-key case; run the wrong-selection behavior; inspect its category and
one-line diff; restore the reviewed recipe and rerun. The exact-output diff made
the changed behavior diagnosable without a focused-region feature. Stateful
success still requires an external state oracle. Continuously repainting screens
still require explicit redraw waits and post-resize positive evidence. Initial
target acquisition, independent first-use timing, native non-Windows recipe
execution, and accessibility observation remain for their named later gates.

For adoption A1, the onboarding task is to choose the nearest recipe, acquire
its exact prerequisite, run the reviewed pass, introduce one assertion or state
expectation defect, explain the category/evidence, and recover without changing
the target to fit the test. Proposed observation targets—not release gates—are:
prerequisite-to-first-launch within 10 minutes when the documented toolchain is
already present, first valid adapted result within another 10 minutes, and
failure diagnosis plus recovery within 5 minutes. Record assistance, confusion,
abandonment and acquisition time separately instead of grading participants.

## Verification

Focused authoring tests passed before the real recipes. The checkpoint also ran
the full Go suite, vet, race script, example smoke tests, JSON/spec validation,
and a tracked-diff review before commit. Exact final results are recorded in the
commit handoff. Sprint 12-B remained a separate evidence gate and was
subsequently [deferred](sprint-12-b-decision-2026-09-21.md); completing A did not
authorize a new public input or assertion contract.
