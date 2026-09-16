# Sprint 5 suite adopter walkthrough

Status: prepared for a suite-capable release candidate. Do not record a participant result from `v0.1.0`; that release predates directory selection and `--artifacts-dir`.

This walkthrough asks one independent maintainer to evaluate a real, small suite in 30–60 minutes. It does not ask them to test Playtestr's own examples. Use synthetic data, a disposable application state, and a checksum-verified release archive. Playtestr runs the target with the participant's permissions and is not a sandbox.

## Before the session

The repository owner records the candidate tag, commit, successful native-release workflow, archive checksum, and participant consent. The participant chooses:

1. An existing interactive CLI or TUI they can run deterministically.
2. Two or more related JSON specs that previously required explicit paths.
3. The exact paths expected from directory discovery, in order.
4. One reversible application regression that should fail a specific spec.

Copy the [project record](project-record-template.md) before starting. Never collect credentials, environment values, typed secrets, personal paths, or unreviewed terminal screens.

## Run the suite

After verifying the archive checksum and `playtestr --version`, run from the project root:

```text
playtestr test --list path/to/terminal-tests
playtestr test --artifacts-dir artifacts/playtestr --report artifacts/playtestr-results.json path/to/terminal-tests
```

Compare the list output with the frozen expected set before launching the suite. A missing, extra, or reordered path is a finding; do not work around it by silently enumerating files. The green run must report every selected spec exactly once and exit 0.

## Seed, diagnose, and recover

Apply the chosen reversible regression and rerun the same suite command. It must exit 1 for the intended product failure, name the failing spec and step/category, and point to readable evidence beneath the explicit artifact root. Measure from command completion until the participant can explain the failure without coaching. Do not update a snapshot to make an unexpected screen pass.

Restore the application, rerun the identical command, and confirm it exits 0. The recovery report must not reference evidence from the failed run. Preserve the failed run directory only after reviewing it for sensitive content.

Record whether the participant could:

- predict the selected files from the documented rules;
- find the first failing spec and evidence without browsing source directories;
- distinguish the current report from prior run artifacts;
- explain the regression and choose to keep, change, or remove the suite command.

## Participant-owned CI check

If the target is suitable for CI, the participant—not the Playtestr operator—adds the same command to its workflow. Pin the candidate archive and checksum, retain the JSON report and explicit artifact root for a finite period, and upload them under an `always()` condition while leaving the Playtestr command's failure status intact. Use read-only repository permissions where possible.

The CI check needs one green run and one controlled regression. Confirm the results UI or downloaded archive exposes the same failing spec and resolvable evidence. If the project has no JUnit consumer, report v1 plus files is sufficient; do not introduce JUnit solely for this trial.

## Acceptance and handoff

The Sprint 5 independent gate passes only when a consenting maintainer completes directory list, green run, intended failure, recovery, and participant-owned CI on a real project. Internal examples, operator-owned workflows, and clean-clone checks remain engineering evidence and cannot substitute for adoption.

Classify friction as application behavior, spec authoring, runner correctness, terminal compatibility, environment/setup, or documentation. A false pass, process leak, data loss, sensitive-data persistence caused by Playtestr, or broken advertised installation blocks promotion. Otherwise, use diagnosis friction to choose the next milestone: Sprint 7 when evidence is hard to interpret; Sprint 6 only when captured evidence is understandable but insufficient to reproduce the failure.
