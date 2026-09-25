# R6: freeze, qualify, publish and verify the completed batch

Status: R6-F, R6-Q, and R6-K complete 25 September 2026 for `v0.4.0-rc.1`; **kit ready, publication pending**. R6-P/V require new publication authority and public bytes. Follow the [root roadmap](../../../roadmap.md) and [evidence invalidation rules](../execution-contract.md).

## Entry and release boundary

Before freeze, 13-A0/A1/B/C/D, 11-A/B and 12-A are complete for claimed hosts; S10, 12-B and S6 have either tested implementation or justified optional deferral. S14 scripts may be drafted, but final captures follow qualification. Independent adoption is later and never fabricated as an engineering prerequisite.

No unresolved false pass, wrong supported outcome, unbounded execution, destructive cleanup, managed-process leak, unsafe artifact handling or broken advertised installation may be waived. Missing native evidence blocks the affected support claim. A previously supported regression requires repair or an explicit reviewed support/migration decision; silently dropping its case is unacceptable.

Choose one coherent next published runner version from the actual contract audit. It may be a qualified prerelease or stable release, but the choice and embedded version must be fixed before the long campaign. There is no requirement to publish one version per sprint or both RC and stable before A1. If a qualified prerelease is chosen, later stable promotion is a separate release decision and must qualify its own rebuilt bytes.

## R6-F: freeze and build, before 11-C

1. Review the feature inventory: existing suites/report plus current setup/workspace work and any actually accepted optional behavior. Verify minimum runner versions in examples and UI. Do not present source-only v2 workspaces as available in v0.3.0-rc.1.
2. Freeze a clean immutable source commit containing all shipped code/build inputs, dependency locks, toolchain/build flags, embedded version, strict schemas, target manifest, fixtures, oracles, baselines and declared host scope. Dirty rehearsal evidence stays separately labeled. Resolve contract-policy ambiguities before choosing migration notes. Explicitly select a version not already tagged/published; the audited workflow's `v0.1.0` default is not a next-release choice. Check remote novelty again before publication. See the [operational checklists](../operational-checklists.md).
3. Build once per advertised native host; record executable SHA-256. Package those exact binaries with README/license/notices; record archive SHA-256 and members. Extract in a path with spaces and verify executable hash/version identity.
4. Run lightweight archive/readiness smokes. The immutable candidate is now available for 11-C/R6-Q. It is not yet publicly released or considered fully qualified.

Exit: candidate manifest, exact bytes, package smokes and complete qualification commands. If source/version/toolchain changes later, freeze a new candidate and invalidate affected evidence. Never use a moving branch or the word “latest” as identity.

## R6-Q: qualify the frozen candidate

11-C and R6-Q refer to the same actual qualification work; do not execute or count it twice.

| Gate | Evidence required |
| --- | --- |
| Source | Native tests/vet, relevant race tests, risk-case coverage and actual negative outcomes at the candidate source |
| Contract | Existing v1 semantics preserved; opt-in formats, current v2 HTML, CLI/schema/docs agree; explicit migration and reader compatibility |
| Archive | Exact members, integrity checks, executable identity, correct version, native extraction/run on all advertised hosts |
| Installed behavior | Complete admitted 120-workflow host matrix using extracted frozen binaries, independent postconditions and meaningful negatives |
| Repetition | 3,000 executions from 11-C with exact executable hashes and complete first-attempt ledger; no unexplained false results or managed leaks |
| Defect sensitivity | 15 project controls with reviewed genuine defects/known-bad versions and recovery; fixture-only sensitivity separately labeled |
| Installer source | Exact runner pin installs correct bytes through source action; invalid/corrupt/interrupted cases fail without publishing ready outputs |
| Upgrade preparation | Previous suitable public release and candidate both tested with compatible reviewed v1 specs; candidate alone exercises v2; baseline hashes preserved |
| Evidence | Correct primary/cleanup/oracle outcomes, report v1/v2 rendering, bounded artifact retention, safe path handling |
| Presentation input | Draft S14 stories reference implemented behavior; final captures/accessibility/publication checks are R6-K after qualification, not a prerequisite that creates a cycle |

All unsupported or blocked cells remain visible. Counts are distinct workflows/cases versus repeated executions, not one inflated coverage number. Review any proposed quota change explicitly with lost-risk explanation; do not quietly redefine success.

Use executable evidence by exact hash. A packaging/docs-only edit can reuse identical executable results while archive/layout/install checks rerun. Changing embedded RC to stable version creates different bytes and requires renewed executable qualification. Do not overwrite or reinterpret original records.

## R6-K: finish the release kit

After qualification, complete S14 final captures and clean-host instructions from the candidate. Prepare:

- Release notes with features actually shipped, known limits, compatible formats, supported hosts and migration/downgrade behavior.
- Evidence index linking native source, archive, corpus, repeat, mutation, cleanup, browser and benchmark results, with exclusions.
- Candidate checksums, exact source/toolchain identity, license/notices and immutable action revision candidate.
- Installation/archive fallback, how to inspect and remove the setup action, target prerequisites and bounded support expectations.
- Three reproducible demo stories, unchanged baselines, target patches, captured reports and draft announcement text.
- Publication commands and post-download smoke commands ready for execution, not just a generic checklist.

The owner reviews a concrete kit. No claims of independent adoption, zero flakiness, universal Unicode/framework compatibility, sandboxing or market superiority are added.

## R6-P: authorized publication

Publishing/pushing/tagging remains a separate explicit user instruction under repository policy. Complete all reviewable local work first. If instruction is pending, record “kit ready, publication pending”; keep A1's public-release gate open without inventing completion.

Publish a new immutable runner tag/assets for the exact frozen version. Publish or identify the verified immutable setup-action commit separately; action and runner pins are independent. Never replace an older version's bytes, create a dummy runner release for upgrade testing, or recommend an unverified action branch.

## R6-V: verify actual public bytes and route

Download public archives/checksums on Linux amd64, macOS arm64 and Windows amd64. Verify byte equality with the qualified candidate, extract, check executable identity/version and run representative real-project pass/intended-failure/recovery. Exercise invalid input, a cleanup/cancellation path, current report generation and relevant controlling-terminal checks. Capture all exit statuses and artifact identities.

Hash equality establishes which previously qualified executable is installed; the public smoke verifies publication/distribution path. A mismatch halts acceptance and requires investigation. Do not cite earlier source results to excuse different public bytes.

Exercise the actual immutable public setup-action SHA, not only `uses: ./setup-playtestr`. For a genuine upgrade, keep that action SHA fixed, install existing v0.3.0-rc.1 and then the newly published R6 version in separate clean attempts, and run compatible v1 pass/failure/recovery on both. Run new v2 behavior only on the new release. Confirm PATH/version changes and no baseline modifications. This can close the old→new runner upgrade gate in this batch if both releases fit the documented asset contract.

If a still-future action-code upgrade or unavailable later release cannot be observed, label that specific longitudinal check open. It does not hold A1 hostage after the current advertised route is fully verified. A broken current public action route does block claiming that route; the release owner must either fix it or explicitly publish archive-only guidance and carry the action limitation. Root status must reflect the actual decision.

## Failure, rollback and handoff

If qualification fails, preserve evidence, stop promotion of the affected candidate, reduce and fix the defect, then refreeze and rerun according to invalidation rules. If a critical issue appears after publication, correct guidance, stop recommending affected behavior and ship new versioned bytes through the same process. Never “roll back” by rewriting the tag or deleting user baselines.

R6 ends with verified public bytes, accurate download/docs links, exact supported scope and a record of any separately deferred longitudinal checks. **Start maintainer adoption A1 now**, after all engineering milestones. No optional Sprint 15 is required. Later stable promotion, support patches and adoption-driven fixes get their own explicit small boundary.

Close the still-open R5 presentation checks for the actual published material: installed-binary walkthrough on each promised native host, deployed nested routes/refresh, schema/download links, report/demo controls, search and 404 behavior. Record which repository metadata/social-preview changes were actually published. A homepage HTTP 200 is a smoke, not proof of this complete audit. Site deployment or repository-setting mutations follow the explicit publication instruction; prepare the exact changes in the kit first.
