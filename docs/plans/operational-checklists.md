# Operational checklists for executing the roadmap

Status: proposed execution instructions, 19 September 2026. These commands and checks have not been run as a new native campaign during the planning audit. The [roadmap](../../roadmap.md) owns order; the [execution contract](execution-contract.md) owns evidence and invalidation rules.

## First checkpoint: 13-A0

Record checkout identity and modifications, host OS/architecture, Go version, PowerShell availability and applicable race compiler. Keep existing changes intact. Use native Linux amd64, macOS arm64 and Windows amd64 for their respective support cells. A developer's WSL run is labeled separately.

The following are existing source-test entry points, not proposed product commands. Execute from the repository root and save command exit status plus bounded output separately for each command:

```text
go test -count=1 -json ./internal/setupaction
go test -count=1 -json -run '^TestWorkspace' ./internal/runner
go test -count=1 -json -run '^TestRenderHTML' ./internal/report
```

Inspect JSON test events as well as the process exit code. The installer tests explicitly skip when neither `pwsh` nor `powershell` is available, and on unadvertised hosts. Exit zero with skipped required tests does not close installer verification. Record each required test as passed, failed, skipped or absent. Preflight the shell rather than discovering the skip after declaring the job green.

Required installer tests currently include `TestSetupActionInstallsVerifiedBinaryAndOverridesStalePath`, `TestSetupActionRejectsUnsafeOrUnverifiedInputs` and `TestSetupActionBoundsNetworkTimeout`. Required workspace families include freshness, failure retention, setup rejection before launch, cancellation, unsafe fixture inputs and cleanup. Require the corresponding native link/junction and locked-file cases where applicable; an unavailable privilege is a visible evidence gap, not a passing filesystem guarantee. Inventory exact test names at the implementation revision because names may change.

The focused commands are triage, not full release acceptance. Integrated verification also runs repository-wide tests/vet, relevant race checks, CLI/schema tests and manual examples as required by AGENTS.md. A missing Windows race compiler remains a prerequisite to resolve. Report rendering tests do not replace actual offline browser checks.

Deliver one table with test/path, source identity, host, command, exit status, required pass/skip counts, evidence location, unresolved gap and next action. Do not dispatch remote jobs or publish simply because the checklist mentions them.

## Pilot handoff: 11-A0

Use the five pilot IDs in the [catalog](corpus-catalog.md). For each, admit an exact target version, license, reproducible install, command and fixture before writing the interaction. Record the real user task, screen assertion, independent state oracle, deliberate defect, recovery and cleanup check. Measure setup time, execution time and artifact size to budget the larger campaign.

For state-writing workflows, choose the oracle location before implementation. Successful v2 workspaces are deleted before the runner returns. Use the catalog's externally owned isolated resource, verified pre-exit adapter or v1 harness-owned disposable directory route. No post-run read of an already deleted successful workspace can establish correctness. No silent target replacement or fake failure to retain successful state is acceptable.

## Reader and version compatibility gate

Confirm this matrix against actual frozen binaries before R6-F; these rows describe planned expectations from the audited release history, not newly executed compatibility results.

| Consumer | Input | Required result |
| --- | --- | --- |
| Existing supported v1 runner | Reviewed compatible v1 spec | Preserve documented behavior and reviewed baseline |
| Runner predating workspace support, including v0.3.0-rc.1 | Spec v2 | Clear unsupported-contract rejection before launching the target |
| v0.3.0-rc.1 report renderer | Report v1 | Render its supported evidence accurately |
| v0.3.0-rc.1 report renderer | Report v2 | Clear rejection; never silently omit workspace outcome |
| Candidate runner/renderer | Supported v1 and v2 inputs | Preserve each contract and mixed-suite facts; exercise setup/cleanup failures |
| Any strict reader | Unknown version or disallowed field | Bounded diagnostic, no accidental launch or destructive output replacement |

Older releases without an HTML command are not report-renderer compatibility targets. Resolve Q09 in the [decision register](decision-register.md) for optional fields, minimum versions and forward-reader behavior. Do not infer forward compatibility from a semver label or loosen validation only to make this matrix green.

## Candidate freeze and publication gates

- Release source must be a clean immutable commit containing every shipped code/build input. Dirty development runs remain useful evidence with patch identity, but cannot masquerade as the final release source. Record toolchain, dependencies, flags, version and hashes separately.
- Select an explicit new version. The audited release workflow defaults to `v0.1.0`; never rely on that default for the next candidate. Before a new release, check both local and remote tag/release identities. If remote state is unavailable, novelty is unverified and publication remains blocked. Historical rebuilds must be explicitly labeled and cannot overwrite existing assets.
- Review the exact version at freeze and again before publication. If another publication has consumed it, select a new version, rebuild and requalify changed bytes. Do not rename already qualified bytes while claiming their embedded version changed.
- Separate development rehearsal, frozen candidate, published download and immutable public action evidence. The existing install-smoke workflow uses `uses: ./setup-playtestr`; it cannot alone prove an external consumer can use the published action SHA. Prepare a consumer check using the actual repository/subdirectory and immutable commit, with runner version independently pinned.
- Make candidate and public-download hash comparison explicit for every advertised host. Review the complete local kit before requesting any publication action. A hash mismatch prevents handoff to adoption until investigated and resolved.

## Scenario review and required response

| Scenario | Correct next action | What cannot count as closure |
| --- | --- | --- |
| macOS unavailable | Continue independent pilot/docs work; assign missing native run before advertised release readiness | Cross-compilation or a configured job |
| PowerShell missing; Go exits zero | Mark required installer tests skipped; provide prerequisite and rerun | Green aggregate exit status |
| False pass in a seeded project defect | Preserve artifacts; reduce, fix and requalify affected candidate | Retrying until a failure is detected |
| Target version cannot perform proposed catalog task | Amend admission with rationale and equivalent meaningful task; preserve exclusions and count definitions | Invented expected behavior or duplicate padding |
| File oracle runs after workspace deletion | Move validation to a supported lifecycle route and recheck oracle sensitivity | Screen-only success for a state-writing task |
| Native link test lacks privileges | Obtain applicable native proof or explicitly limit the claim through review | Silent skip or unrelated mock |
| Binary changes after freeze | New identity and qualification under invalidation rules | Old results attached to new hash |
| Demo text alone changes after freeze | Check links/version/claims; rerun changed executable walkthrough if any | Automatically repeating all 3,000 runs |
| Archive changes, executable identical | Rerun packaging/install/download gates; cite executable evidence by hash | Skipping archive checks |
| Artifact budget is exceeded | Fail or stop affected attempt with bounded evidence; investigate budget/design | Truncating away the failure and claiming a pass |
| Old renderer receives report v2 | Verify clear unsupported-contract diagnostic and minimum-version instructions | Treating omitted workspace evidence as success |
| Public bytes differ from frozen candidate | Halt acceptance and investigate distribution/build provenance | Assuming same version means same binary |
| No maintainers respond after engineering | Record recruitment outcome and revise A1 outreach within its authorized scope | Inventing adopters or reopening optional engineering indefinitely |

These are planning stress cases. Actual execution must attach observations; a completed checklist of intended responses is not runtime proof.
