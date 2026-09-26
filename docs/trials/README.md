# Playtestr v0.4.0-rc.1 maintainer trials

Status: A1 recruitment opened 26 September 2026 after the engineering batch
and R6-V completed. No invitation, consent, review, repeat use, or
participant-owned CI result is counted until it actually occurs. These trials
test whether Playtestr protects a real terminal interaction well enough that a
project maintainer chooses to run the test again.

This is an optional trial for maintainers and contributors with one repeatable, non-sensitive CLI or TUI workflow. Plan for 30–60 minutes after the target is already runnable. Read the eligibility and prerequisites below, then use the [public project-trial form](https://github.com/Wyrcan-io/playtestr/issues/new?template=project-trial.yml) only for information you are comfortable publishing. Attribution is optional and a project alias is allowed.

## Program status and evidence boundaries

Operator technical evidence is recorded separately in the [R3c cross-stack record](cross-stack-validation-2026-09.md), with reusable [sanitized recipes](cross-stack-recipes.md).

A1 needs five consenting maintainers to enter the program, three completed
participant projects across at least two implementation stacks, two maintainers
who voluntarily repeat use, and one successful participant-owned CI
integration. The demo, Gum fixture, corpus, and operator campaigns are
technical coverage; they do not count as independent adoption. Use the
checksum-verified `v0.4.0-rc.1` release and the exact action pin below.

## Who should participate

A useful participant maintains or contributes to an existing interactive CLI or TUI and can choose one regression-prone workflow. Good first workflows include:

- A setup wizard that creates or changes configuration.
- An interactive selector whose choices affect output.
- A full-screen view with navigation, redraws, or resize behavior.

Choose an offline flow that can use synthetic data. Do not use production credentials, payment flows, personal data, or a task that depends on an uncontrolled remote service. Playtestr runs the selected target with the participant's own permissions; it is not a sandbox.

## Time and prerequisites

Plan for 30–60 minutes for the first integration after the target application is already runnable. Installation alone should take much less; record actual time rather than forcing the work into this estimate.

Use one advertised host: Linux amd64, macOS arm64, or Windows amd64. Start with
the [v0.4.0-rc.1 release notes](../releases/v0.4.0-rc.1.md) and
[CI installation guide](../ci-installation.md). Release binaries do not require
Go and do not install the target application's runtime or dependencies.

## What the maintainer chooses before the session

Write down these four facts before authoring a Playtestr spec:

1. The exact application version or commit to test.
2. One terminal workflow and its manual keyboard steps.
3. A concrete regression the test should catch.
4. The starting state needed to repeat the workflow.

State how the workflow is protected today: manual checklist, unit/integration test, terminal test, or no coverage. This baseline matters because a new test is useful only if it improves a real task.

Use the [project record](project-record-template.md) for these facts. A participant can keep the completed record private and send a sanitized copy; public attribution is optional.

## First trial session

### 1. Verify the intended behavior manually

Run the chosen application flow once without Playtestr. Record the visible state after every meaningful input, the expected exit behavior, and any files/state it changes. If the manual flow is already inconsistent, preserve that observation instead of hiding it with larger timeouts.

### 2. Install the published runner

Download `v0.4.0-rc.1`, verify the archive against
`checksums-v0.4.0-rc.1.txt`, extract it, and run `playtestr version`. Record the
archive name, observed checksum, host, shell, and version output. Do not use a
checkout-built runner for the trial result.

### 3. Write one small spec

Keep the first test readable at a glance. Use `expect` after input or resize to prove the new state is visible. End finite commands with an exact `exit` assertion. Add one snapshot only when a reviewed screen adds value beyond a text assertion.

```json
{
  "version": 1,
  "name": "choose the staging environment",
  "command": ["my-cli", "configure"],
  "width": 80,
  "height": 24,
  "steps": [
    {"expect": "Choose environment"},
    {"key": "ArrowDown"},
    {"expect": "> Staging"},
    {"key": "Enter"},
    {"expect": "Saved staging"},
    {"exit": 0}
  ]
}
```

This example is a shape, not a command that works without the participant's application. Commands are executed directly without a shell. Record target-specific setup separately.

Run with a machine report:

```text
playtestr test --report playtestr-results.json path/to/test.json
```

If using a snapshot, create only the named reviewed baseline, inspect it, and rerun without update:

```text
playtestr test --update --snapshot chosen-screen.txt path/to/test.json
playtestr test path/to/test.json
```

Never accept an unexpected screen by updating blindly. Terminal screens and reports may contain application data; inspect them before sharing.

### 4. Prove the test detects the intended regression

Use a known-bad application revision or make one small, reversible local change that produces the chosen regression. Do not damage real user data. The test must fail for the intended reason, return exit code 1, and provide evidence the maintainer can explain.

Record the structured failure category and failing step. A missing executable or malformed spec does not prove the intended UI regression is detected.

Restore the known-good application and confirm the same spec passes again.
Keep each run's explicit artifact directory separate so historical failure
evidence cannot be confused with the current outcome.

### 5. Repeat from the same starting state

Run ten bounded attempts against the pinned good application without automatic retry. Record every outcome and total count. If state from one attempt changes the next, stop and capture the exact files or external resources involved. Do not compensate with arbitrary delays or baseline updates.

Ten passes are evidence for this pinned flow on this host, not a universal reliability claim.

## Second-use and CI check

At least two participants need to run the test in a later working session or after another application change. Record whether they chose to keep, modify, or remove it and why.

At least one project should try CI if its target is suitable for noninteractive automation. Pin the Playtestr release URL and checksum, install the project's own dependencies explicitly, run the normal command, and retain only the selected report/screen/diff files with a finite retention period. A failing Playtestr command must keep the job failed; uploading evidence should use an `always()` condition rather than ignoring the test status.

For GitHub Actions, pin
`Wyrcan-io/playtestr/setup-playtestr@1c03904075512e67f53b0c94a13daa17f0383f1d`
and select runner version `v0.4.0-rc.1` as shown in the
[CI installation guide](../ci-installation.md). The action installs Playtestr,
not the participant's target or runtime.

## How results are classified

Record the observed layer before proposing a fix:

| Category | Meaning |
| --- | --- |
| Application behavior | The target itself is inconsistent or changed. |
| Spec authoring | The selected readiness, input, exit, or baseline is wrong. |
| Runner correctness | Playtestr reports the wrong outcome, leaks a process, or loses evidence. |
| Terminal compatibility | The emulator renders or responds differently from the required terminal behavior. |
| Environment/setup | Target dependencies, state, paths, locale, or CI setup differ. |
| Documentation | The correct workflow exists but a participant cannot discover or follow it. |

False passes, process leaks, data loss, sensitive-data persistence caused by Playtestr, and broken advertised installation are release-critical findings. Preserve a sanitized reproduction and hold any pending promotion; after publication, restrict affected guidance and verify a patch release without overwriting existing assets.

Use the [R3 observations backlog](observations.md) for accepted findings. One participant preference is useful context; repeated friction or a severe correctness issue drives roadmap priority.

## Reporting a trial

A participant can open a [project trial issue](https://github.com/Wyrcan-io/playtestr/issues/new?template=project-trial.yml) for information they are comfortable making public. GitHub issues are public. Do not include credentials, private source, personal filesystem paths, or unreviewed terminal evidence.

For a private project, keep the record private until the repository owner provides a private contact route. A sanitized project alias and reproduction can still count when the participant's identity and consent are recorded privately by the project owner.

## Outreach draft

This text is prepared for the repository owner to send to specific maintainers. It has not been sent automatically:

> I’m testing Playtestr v0.4.0-rc.1, an early prerelease for deterministic end-to-end tests of interactive terminal applications. One public workflow in your project looks relevant: [specific workflow and public source]. The optional trial takes roughly 30–60 minutes after prerequisites, uses synthetic data, and includes known-good, intended-bad, and recovery checks. Playtestr runs trusted targets with your permissions and is not a sandbox. The exact release, evidence, limits, removal steps, and trial guide are linked here: [links]. Public attribution is optional, no reply is required, and I will send at most one follow-up unless you engage. Would you be willing to try one flow?

Record the recipient and authorization before sending outreach. Do not imply compatibility with their stack before their exact flow passes.

## Completion gate

R3 is complete only when the [cohort record](cohort.md) shows:

- Three to five selected projects, with at least three completed end-to-end trials.
- At least two implementation stacks and a useful mix of interaction styles.
- A good and intended-bad result for every completed project.
- Ten-run observations for each pinned initial flow.
- Two voluntary second-use results and at least one successful participant-owned CI integration, with failed attempts retained.
- Release-critical findings resolved or affected guidance restricted pending a verified patch.
- Publication permission recorded for every public project name, quote, or artifact.

Additional internal fixtures cannot replace a missing participant result.
