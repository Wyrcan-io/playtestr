# Sprint 9: repeatable workspaces for stateful CLIs

Status: proposed. Workspace fields and flags below are design targets, not current spec features. This sprint follows [Sprint 8](08-ci-adoption-and-installation.md) unless trial evidence justifies moving it earlier.

## User problem and outcome

A setup wizard creates a configuration file on its first run. The second run sees that file and skips the screen the test expects. Developers manually delete state, point a test at their own project, or depend on a CI checkout that happens to be clean. This produces misleading regressions and risks modifying personal files.

The outcome is an opt-in workspace created from a small reviewed fixture for each spec. The target starts from known files and a documented working directory. Repeated tests receive fresh copies, evidence survives cleanup, and failure/cancellation removes only runner-owned temporary state after process cleanup.

This is repeatable test setup for trusted programs. A temporary directory is not a sandbox and does not stop a target from accessing other paths, the network, registries, or external services.

## Entry evidence and success measure

Select one real stateful flow from the trials: project initialization, configuration editing, or a first-run wizard. Capture a baseline reproduction where the second execution differs because of persisted state. Identify the exact files and environment variables the application uses; do not assume changing its working directory changes its home or cache directory.

Success means that the same spec can run repeatedly from a reviewed fixture with the expected outcome and no change to the fixture or original project. Demonstrate a seeded UI regression and a cancelled run as well. Record the target/version and file locations actually checked; this is not proof of complete filesystem isolation.

If the stateful problem is entirely external, such as a remote account or database, this sprint must not pretend a copied directory solves it. Choose a local case or separately plan the missing resource contract.

## Scope and public compatibility

Required: bounded fixture copying, a fresh per-spec workspace, explicit working-directory behavior, narrowly defined optional home/temp directories, process-before-files cleanup ordering, and safe retained-workspace inspection on explicit request.

Excluded: Docker orchestration, arbitrary setup/teardown shell hooks, network services, database provisioning, file-content assertions, parallel workers, automatic retries, and reusable workspace caches. The first slice copies small fixtures; optimize only if real measurements justify it.

The current spec schema rejects unknown fields. Introduce an opt-in spec version 2 for the selected workspace contract, retaining version 1 parsing and behavior. Publish a separate schema and migration notes; do not silently reinterpret existing `cwd`, `env`, or command resolution. If another approved sprint has already introduced v2, reconcile its contract before choosing the next version number.

Proposed fragment, intentionally incomplete until checkpoint 9.1 settles naming:

```json
{
  "version": 2,
  "workspace": {
    "fixture": "fixtures/new-project",
    "cwd": ".",
    "home": "temporary",
    "temp": "temporary"
  }
}
```

The real spec still needs its normal command and steps. `fixture` resolves relative to the spec's directory. `workspace.cwd` resolves inside the copied fixture and must exist as a directory. Reject simultaneous top-level `cwd` and workspace mode to avoid ambiguous precedence. The exact opt-in defaults must appear in schema, help, examples, and validation together.

## Filesystem contract

Create a unique owned root under an explicit or documented OS temporary parent. Keep internal ownership metadata outside the target working tree. Copy only the requested fixture's regular files and directories; reject symlinks, junctions, other reparse points, devices, sockets, and unsupported special entries in the first version. This deliberate limitation is preferable to copying a developer's home through a link.

Reject a fixture root that resolves outside the allowed spec-relative fixture policy. Explain how users place shared fixtures in an explicitly selected project root if that real use case is admitted at 9.1; do not loosen traversal checks by accident. Do not copy the entire checkout implicitly.

Provisional limits: 1,000 regular files, 32 MiB total contents, 8 MiB per file, depth 32, and a 30-second copy budget bounded by the enclosing run budget. Confirm these against the chosen application before freezing them. Validate and enforce limits during copying as well as enumeration, because files can change between those operations.

Preserve executable permission where supported and required for fixture scripts. Do not preserve ownership, privileged mode bits, or host-specific attributes merely because an archive or source file contains them. State platform differences, including unsupported fixture names and case collisions.

Do not promise an atomic snapshot of a fixture that another process is editing. Detect size/type changes where practical, fail clearly, and require fixtures to remain unchanged during setup. Avoid copying open streams without size/time bounds.

### Executable and working-directory resolution

Resolve the target command using an explicit documented rule before switching to the copied working directory. Preserve v1 behavior. For v2 workspace mode, decide between a spec-relative executable path and a PATH executable, and make that distinction explicit in examples. Never accidentally execute a different file named like the target inside a fixture because `cwd` changed.

If executing a fixture-provided program is admitted, make that selection explicit and document its trusted-code status. Do not add interpolation of arbitrary shell strings or automatic `go run`/package installation during setup.

### Home, temporary directories, and environment

Separate workspace working files from optional temporary home and temp directories. At 9.1, list exact platform environment mappings required by the chosen target: for example HOME/XDG locations on Unix and the applicable Windows profile/application-data variables. Test those mappings natively rather than claiming a universal home redirect.

Keep the existing explicit environment inheritance model. Define precedence: reject explicit spec environment values that conflict with opted-in managed home/temp variables, with a clear explanation. Never inherit secrets or copy the user's real home to make the target work. If a target needs a credential or external configuration, the author must supply it through the existing explicit test setup and understand its effect on repeatability.

## Lifecycle, failures, and evidence

Workspace preparation belongs to a bounded session setup phase. Time spent copying counts toward the documented total execution budget. Cleanup has its own existing bounded allowance so an expired execution budget does not skip necessary process termination.

The required order is: validate inputs and output paths; create owned directories; copy fixtures; launch the trusted target; execute steps; observe/stop the process tree; capture/write evidence outside the workspace; remove owned workspace state. Baseline files remain in their existing reviewed source location and are never stored in a directory that cleanup will delete.

Update snapshot transaction handling deliberately: a workspace cleanup failure prevents declaring the run wholly successful or committing staged baseline changes. Review existing commit/rollback ordering before implementation and cover this boundary with an integration regression.

If setup fails, never launch the target. If process cleanup cannot confirm termination within the supported platform's limits, do not recursively delete files underneath a potentially active target. Retain the owned directory, report the cleanup failure separately, and explain the manual recovery path.

Deletion must verify the resolved absolute path and ownership against the created root immediately before removal, avoid following links introduced by the target, and stay within that root. Use platform-native safe deletion logic; do not string-build cross-shell recursive deletion commands. Target-created symlinks/junctions must never cause deletion of their destinations.

Proposed `--keep-workspace=on-failure` is an explicit debugging option. Retained workspaces can contain target data and are local evidence, not an automatic CI upload bundle. Successful runs still clean up. Interrupted preparation and retained failure directories must identify what remains and why. Do not implement an unattended sweeper that guesses which temporary directories are safe to delete.

### Format and reproduction interaction

Represent workspace setup/cleanup failures accurately. Existing report v1 cannot accept arbitrary new fields or enum values. Select a versioned report extension or a separate versioned workspace artifact, and specify how primary test failure and cleanup failure coexist. Preserve existing v1 reports for existing commands; any new default report version needs migration notes and an explicit compatibility review.

Extend Sprint 6 prerequisite checks so a reproduction needs the selected fixture and relevant workspace configuration. Do not bundle a whole home or hash sensitive files to claim complete identity. Reproduction metadata states any unverifiable state and treats a changed fixture as a material context difference. Sprint 7 can display workspace setup/cleanup observations without deciding outcomes itself.

## Implementation checkpoints

### 9.1 — Prove the contamination case and settle v2

Run the chosen target twice with existing setup and record the state difference. Design the smallest fixture that controls it. Freeze path roots, command resolution, environment precedence, limits, failure/report versioning, and baseline transaction ordering.

Acceptance: a concrete before/after workflow and schema examples for accepted and rejected combinations. No lifecycle implementation until ambiguity about cwd and executable paths is resolved.

### 9.2 — Prepare and inspect a bounded fixture copy

Implement ownership, enumeration/copy limits, permission handling, and validation without launching a target. Expose useful errors with paths relative to the declared fixture root where possible.

Acceptance: copying leaves source files unchanged; missing fixtures, size limits, case/path problems, symlinks, junctions, and mid-copy cancellation are bounded failures with safe partial cleanup.

### 9.3 — Execute the real stateful flow

Integrate preparation with the ordinary runner and the selected home/temp mappings. Keep evidence paths outside owned workspace roots. Run the same spec twice and verify that both begin with the fixture's state.

Acceptance: the real target behaves consistently, its intended writes land in the workspace, and the original project/fixture remains unchanged. Run native paths for every supported home/temp mapping.

### 9.4 — Complete cancellation and cleanup behavior

Cover natural exit, expected nonzero exit, timeout, flood, a parent/child target, locked files, target-created links, and interruption during copy or deletion. Preserve primary failure and cleanup diagnostics; apply explicit retention policy.

Acceptance: no deletion escapes owned roots, descendants are handled before deletion, and cleanup failure does not commit staged snapshots. Run the race detector and existing real-PTY lifecycle regressions.

### 9.5 — Integrate reproduction and diagnosis

Add the approved format/schema changes, fixture prerequisites, and local retained-directory guidance. Demonstrate an original failed run and a new fresh-workspace reproduction. Do not imply the whole machine state was captured.

Acceptance: changed/missing fixture context is visible before a rerun, the original evidence survives, and the report explains setup versus assertion versus cleanup failure.

### 9.6 — Repeat the adopter's workflow

Run at least ten bounded attempts, including a deliberately broken target and cancellation, and report counts/outcomes rather than a statistical reliability claim. Check source fixtures and known personal-state sentinels before and after. Document which locations were checked and any target-specific limitations.

Acceptance: the maintainer can remove their manual state-reset workaround and explain how to inspect an explicitly retained workspace.

## Acceptance matrix

| Case | Required result |
| --- | --- |
| Two identical executions | Separate roots; each begins with reviewed fixture state. |
| Existing user's project/config | Known sentinels unchanged; no claim of OS sandboxing. |
| Missing/oversized/linked fixture | Prelaunch failure with bounded partial cleanup. |
| Conflicting cwd/env | Validation error, no silent precedence. |
| Same executable name in fixture | Explicit resolution rule prevents accidental target substitution. |
| Setup timeout/cancel | No target launch; owned partial state cleaned or clearly reported. |
| Target hangs/spawns descendants | Existing process guarantees before directory cleanup. |
| Target creates link outside root | Cleanup removes only owned entries, never external destinations. |
| Locked file or unconfirmed process exit | Separate cleanup failure; safe retention; no baseline commit. |
| Explicit keep-on-failure | Local path explained; artifacts survive; no automatic public upload. |
| v1 spec/report | Original behavior and schema remain supported. |

## Definition of done and handoff

- [ ] Checkpoints 9.1–9.6 complete using a real stateful application.
- [ ] New spec/artifact contracts, strict validation, migration examples, and schema tests agree.
- [ ] Source fixtures and known original state remain unchanged across recorded repeated runs.
- [ ] Preparation, execution, cancellation, and deletion are bounded and tested natively.
- [ ] Documentation consistently describes repeatable directories rather than isolation.

Handoff to [Sprint 10](10-terminal-compatibility.md): fixtures can reproduce stateful rendering issues reliably. Parallel execution remains deferred until resource independence and measured suite performance justify a separate scheduling design.
