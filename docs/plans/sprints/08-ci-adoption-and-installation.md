# Sprint 8: make installation and CI adoption repeatable

Status: proposed. The setup action and commands in this plan do not exist yet. Start after [Sprint 7](07-failure-diagnosis.md) provides a usable artifact workflow and stable release assets are available.

## User problem and outcome

A developer has a useful local test but must maintain custom scripts to choose an OS archive, download it, verify it, extract it, and put the correct binary on PATH. Their CI can accidentally run a stale executable or upload nothing after a failure.

The outcome is one supported, version-pinned setup action plus a complete external-repository example. A maintainer chooses a runner version, installs their own trusted target, executes ordinary Playtestr commands, and retains useful evidence. Installation convenience must not obscure which binary ran or change test semantics.

## Entry gate and user evidence

Require two adopter setup-friction records from release trials: copied download plumbing, version drift, platform selection errors, or missing CI evidence. Obtain permission for any external repository changes separately during implementation. The planning request does not authorize publishing an action, opening third-party PRs, or contacting maintainers.

Verify the exact release assets and their supported OS/architecture pairs before designing mappings. Existing successful native targets provide a starting point, not a promise that every GitHub-hosted or self-hosted runner works.

Success is an external repository using a pinned published runner to pass a known-good flow, reject a seeded regression with the correct failure category, and expose readable artifacts. Record setup edits, time, assistance, and whether a later version upgrade required rewriting the workflow.

## Required scope and conditional work

Required work is a setup-only GitHub Action, its installation checks, a documented CI recipe, and one adopter integration. Keep a direct-download fallback for users outside GitHub Actions. The action invokes the standalone Go binary; it is not a second implementation of the runner.

Package-manager distribution is conditional. At checkpoint 8.1, record demand for one channel and a maintainer commitment. If that evidence exists, plan one channel, such as Scoop or Homebrew according to the actual users. Do not implement both by default. If no channel qualifies, record the decision and finish the required setup-action scope; an unneeded package manager is not an unfinished acceptance item.

Excluded: hosted services, PR comments, automatic snapshot commits, repository write permissions, a matrix of package managers, a universal installer, self-update, and automatic upgrades to an unpinned latest release.

## Proposed integration contract

The following is a conceptual recipe, not a published action reference or a copy-and-run workflow yet:

```yaml
# Pin each action to a reviewed immutable commit when publishing the example.
- uses: Wyrcan-io/playtestr@<setup-action-commit>
  with:
    version: 'v0.1.0'
- run: playtestr test --artifacts-dir artifacts/playtestr --report artifacts/results.json --junit artifacts/results.xml tests/terminal
# Add an artifact upload step with an appropriate always/failure condition.
```

Finalize action location and supported action version separately from the installed runner version. If the required CLI flags first ship after v0.1.0, the actual example must pin the first release that contains them. Never publish this conceptual version combination as a verified example.

Inputs should be minimal: an exact release version, and only a necessary installation/cache option. An omitted or floating version should fail with guidance in the initial action. Derive OS and architecture from the runner and reject unsupported pairs before downloading anything.

Outputs should identify the installed version and resolved binary path. Print the selected release and platform, without environment values or token contents. Do not print a claimed verified identity before checking the downloaded bytes and executed binary.

The action only installs Playtestr. It never discovers or runs specs, installs arbitrary target dependencies, sends reports, opens a browser, or modifies baselines. Target installation and test commands remain explicit workflow steps under the repository owner's control.

## Distribution and installation design

Choose the smallest maintainable action implementation after inspecting platform shell availability. A composite action with small platform-specific scripts is preferable if it meets the verified environments; do not add a JavaScript service or another product runtime merely to wrap a download. Scripts must quote paths, preserve exit status, and handle spaces on Windows and Unix.

Download only from the documented release origin for an exact version. Validate asset naming and checksums using the published manifest. Checksums detect accidental corruption and mismatched bytes; a checksum obtained from the same compromised source is not an independent signature. Do not invent signing claims or disable TLS verification when installation fails.

Extract into a fresh owned directory. Check archive members before extraction where required by the extraction tool; reject path traversal, unexpected executables, and ambiguous layouts. Verify executable permissions on Unix and invoke the extracted absolute path for version/help checks before changing PATH.

If caching is justified, key by exact release, platform, architecture, and expected content identity. A cache hit still needs binary/version validation. A failed or partial download must not leave a cache entry treated as valid. Prefer no cache in the first slice if download time is negligible; cache plumbing is not user value by itself.

Do not require elevated installation or persistent machine-wide PATH edits on hosted runners. Publish the chosen binary path through the action mechanism. Ensure the following workflow step resolves the selected binary even when a different Playtestr is already on PATH.

Bound download time, retries, and archive size. Authentication is optional for rate limits or permitted private distribution, with the least necessary read permission; no personal access token is required for the public-release happy path. Missing credentials or throttling must produce an actionable error, not trigger endless fallback attempts.

## CI evidence and permissions

The recipe builds or installs a pinned trusted target, invokes the normal CLI, and uploads the explicit artifact directory even when a test fails. Do not upload the whole working directory or inherited environment. Give evidence retention a documented finite value, with a reminder that screens can contain application data.

Distinguish a real regression from a broken setup. The seeded-failure example must check exit status and the expected structured failure category/step, and confirm useful screen/diff evidence. A launch failure returning nonzero does not prove snapshot checking works.

An expected failure in Playtestr's own demonstration can be handled inside a successful validation step after checking its exact result. A user's ordinary regression workflow must stay failed when tests fail; do not teach blanket `continue-on-error` as the normal integration.

Use read-only repository permissions where possible. Exercise a pull request from a fork without secrets, assuming only trusted test targets are eligible under the repository's own contribution policy. Do not introduce `pull_request_target` execution of untrusted checkout code, automatic commenting, or write permissions for a setup-only task.

## Implementation checkpoints

### 8.1 — Freeze the supported install contract

Review both friction records, current release layout, action location, version policy, supported hosts, retry limits, and conditional package-manager evidence. Decide how action updates and binary releases are maintained independently.

Acceptance: a short contract with no floating version default, no invented platform coverage, and an explicit yes/no decision on one distribution channel.

### 8.2 — Install a release in fresh native jobs

Build the download/verify/extract/version/PATH sequence using actual released archives, without relying on checkout-built binaries. Use isolated temporary install directories and introduce an intentionally stale executable on PATH in one test.

Acceptance: the next step runs the selected version on each advertised host. Wrong checksum, missing version, unsupported architecture, corrupt archive, and failed download are bounded actionable failures.

### 8.3 — Package and validate the setup action

Expose minimal inputs/outputs, add self-tests, and verify quoting and failure propagation. Inspect artifact provenance before constructing a reviewable action release or tag. Publication remains an explicit authorized step, not a side effect of local testing.

Acceptance: an action test exercises installation in a fresh job, including subsequent-step PATH resolution. A successful archive build alone does not satisfy this checkpoint.

### 8.4 — Build the complete CI recipe

Create a small documented example with target prerequisites, a pass, a deliberately checked mismatch, report/JUnit output, and failure-artifact retention. Update the website/README only with commands available in the pinned version.

Acceptance: both test semantics and artifact accessibility are verified. Inspect the downloaded artifact and local HTML report, not just the workflow's green status.

### 8.5 — Complete the selected distribution addition, if justified

For a channel approved in 8.1, generate versioned metadata from release assets, verify install/upgrade/uninstall in a fresh environment, and document who updates checksums and handles withdrawn releases. Prepare any third-party submission fully before requesting the necessary publication approval.

Acceptance: the chosen channel installs the expected binary and removes only its owned files. If this checkpoint was excluded by the entry decision, preserve the reason and keep the direct-download/action routes complete.

### 8.6 — Integrate with an independent repository

Have the adopter review and run the workflow. Introduce and remove a controlled regression. Repeat installation at another exact released version when available to check upgrade mechanics; do not publish a dummy release just for this test.

Acceptance: the owner can explain version selection, find failure evidence, and update the pin. Record any unresolved external approval or publication as incomplete, rather than calling prepared files a deployed integration.

## Acceptance matrix

| Scenario | Expected behavior |
| --- | --- |
| Exact supported version | Downloaded bytes, invoked version, and subsequent PATH agree. |
| Existing different binary | Selected action version wins within the job; original installation is not deleted. |
| Corrupt/mismatched download | Installation fails before exposing a runnable binary. |
| Missing release/unsupported host | Clear bounded failure with direct-download/support guidance. |
| Network timeout/rate limit | Finite retry policy; useful error without leaked credentials. |
| Cache hit or partial cache | Identity revalidated; invalid entries cannot silently execute. |
| Paths with spaces | Installation and invocation work natively on the claimed host. |
| Passing and deliberately failing target | Correct categories and artifacts, not merely expected shell status. |
| Fork PR without secrets | Read-only recipe works for the verified fixture. |
| Package upgrade/uninstall, when selected | Exact version changes; unrelated user files remain intact. |

## Definition of done and handoff

- [ ] Required checkpoints and any explicitly selected distribution checkpoint complete.
- [ ] Actual published assets installed on advertised native targets; resulting runs recorded.
- [ ] External repository integration demonstrates both success and a real assertion regression.
- [ ] Version pinning, permissions, evidence retention, failure handling, and maintenance owner documented.
- [ ] No publication, upstream submission, or outreach is claimed without evidence and authorization.

Handoff to [Sprint 9](09-repeatable-workspaces.md): a reproducible CI installation path. Installation consistency does not solve mutable target state; the next sprint addresses that separate, demonstrated source of nondeterminism.
