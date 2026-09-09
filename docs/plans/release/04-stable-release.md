# R4 — Publish stable v0.1.0

Status: planned. Depends on R1–R3. Product outcome: developers can choose a documented stable version for everyday terminal regression testing, with clear support and migration expectations.

## Meaning of stable here

Stable v0.1.0 means the supported workflows have passed their release gates and the team intends to maintain the documented contract. It does not mean every terminal, architecture, framework, or Unicode layout is supported. The project remains pre-1.0; publish an explicit compatibility policy rather than assuming readers infer one from the version number.

## Entry gate

Complete [R3b: trial findings and candidate readiness](03b-trial-findings-and-candidate-readiness.md) before entering this plan. It covers the Linux controlling-terminal fix, unresolved real-app findings, installation CI repair, a new published candidate, and the remaining R3 adoption evidence. Local fixes and the historical primary-run sample alone do not satisfy this entry gate.

Require a named release owner, a frozen candidate commit, passing public-asset installation checks for all advertised targets, completed independent trials, and no unresolved release blockers. Confirm that the evidence applies to the candidate selected for promotion; earlier green runs from a different build are historical context only.

A waiting period alone is not acceptance. One to two weeks of trial use may reveal issues, but R3's concrete tasks and blocker status determine readiness. If the cohort is not available, record that dependency and delay stable promotion rather than claiming internal tests satisfy it.

## Checkpoint 1 — Review the contract and release audit

Read spec v1, report v1, their schemas, CLI help, release notes, and README together. Build a parity checklist for defaults, empty/null values, unknown fields, limits, path semantics, exact exit statuses, and snapshot normalization. Investigate disagreements and decide whether to preserve behavior, document it, or migrate it before calling the contract stable.

Audit release-critical paths against the actual implementation: late cancellation before baseline writes, failed baseline rollback, separate cleanup errors, report-write failures, report/evidence size limits, unknown target exit codes, terminal-output secrets, and expected-failure CI verification. These are review targets, not assertions that every suspected issue exists.

The current workflow checks the deliberate regression's exit code. Also inspect its report category and expected screen/diff artifacts so a launch error cannot accidentally satisfy that acceptance check. Keep the check small and shared with the documented user behavior.

Acceptance: every discovered discrepancy has a disposition. No false-pass or destructive failure path is waived as documentation debt.

## Checkpoint 2 — Publish maintenance expectations

Prepare a changelog with user-visible additions, fixes, limitations, and migration notes. State the spec/report versions accepted by v0.1.0. Explain how patch releases preserve existing test semantics and how future incompatible formats will be versioned. Do not promise support windows the maintainer cannot sustain.

Document how to report a minimal bug using runner version, target version, host, spec, and sanitized evidence. Define a short release-blocker list and a private route for sensitive reports if one is actually staffed. Avoid promising a response-time SLA without a maintainer commitment.

Acceptance: users can identify what changed, what is supported, how to migrate an unversioned prototype test, and how to report a problem.

## Checkpoint 3 — Produce stable bytes

Stable binaries must identify themselves as `v0.1.0`. Do not simply rename `rc.1` archive files while leaving the embedded version unchanged. Select the final source commit, inject the stable version, build on every supported native host, package, extract, and execute those stable bytes.

Recompute all checksums, validate dependency notices, and repeat the essential passing, failing, report, cancellation, and archive-extraction paths. Preserve the exact stable commit-to-asset manifest. If there is a code change since the last tested candidate, assess whether another candidate trial is needed; version-label-only rebuilds still need binary smoke tests.

Acceptance: a complete stable asset set has evidence from the bytes to be published and prints the stable version on every target.

## Checkpoint 4 — Stage, publish, and verify

Prepare a draft stable release with the exact tag/commit, three native assets if all remain supported, checksums, release notes, and links to matching documentation. Confirm release publication is authorized in the session before publishing. Prior release-candidate authorization is not automatically stable-promotion authorization.

After publication, validate public download links and hashes. Update the website and README's install path so new users reach the stable release; avoid leaving a prerelease or expired Actions artifact as the default download. Use stable versioned examples compatible with the released binary, not unreviewed examples from moving main.

Acceptance: the website, release page, binary version, examples, and support table agree.

## Checkpoint 5 — Verify adoption after publication

Invite existing trial participants, with authorization, to install the stable build and run their agreed flow. Record upgrade friction and regression reports. A release announcement should demonstrate a real short interaction and its failure evidence, state the compatibility boundary, and avoid claiming broad framework certification.

Prepare announcement copy independently of sending it. Public posts, direct messages, and use of participant names require their respective authorization. Release publication does not imply permission to contact third parties through every available channel.

Acceptance: at least one existing trial project verifies the stable build, and the maintainer has a concrete issue triage path.

## Failure and rollback policy

| Finding | Action |
| --- | --- |
| Candidate still has a blocker | Continue candidate fixes; do not relabel it stable. |
| Stable archive is corrupt or incomplete | Mark affected download guidance clearly; publish corrected versioned assets through a patch release. |
| Stable test semantics regress | Preserve the previous available version, reproduce the issue, and ship a reviewed patch or migration. |
| Platform only cross-compiles | Exclude it from supported downloads until native evidence exists. |
| Feature needed by one adopter is too large | Keep it in a separate sprint; communicate the limitation honestly. |

Never silently overwrite a published tag or replace a published binary under the same version. If an asset must be withdrawn for a serious issue, explain the affected version and recovery path.

## Definition of done

- [ ] R2 and R3 evidence applies to the promoted candidate; blockers are closed.
- [ ] Contract audit, changelog, compatibility policy, and support instructions reviewed.
- [ ] Stable-version binaries pass native and extracted-archive checks.
- [ ] Stable release published with explicit authorization and verified public links/hashes.
- [ ] Website and examples lead to the correct stable behavior.
- [ ] At least one adopter upgrade verified and issues triaged.

Handoff: choose Sprint 5 using trial findings. Stable v0.1.0 is a useful stopping point even if later sprint plans are deferred.
