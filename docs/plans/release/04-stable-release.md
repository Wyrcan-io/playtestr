# R4 — Publish stable v0.1.0

Status: planned; sequencing revised 11 September 2026. Publication depends on R1/R2, R3b technical closure, and R3c nine-application validation. R3 independent adoption follows publication. Product outcome: developers can choose a documented stable version for everyday terminal regression testing, with clear support and migration expectations.

## Meaning of stable here

Stable v0.1.0 means the supported workflows have passed their release gates and the team intends to maintain the documented contract. It does not mean every terminal, architecture, framework, or Unicode layout is supported. The project remains pre-1.0; publish an explicit compatibility policy rather than assuming readers infer one from the version number.

## Entry gate

Complete the technical portion of [R3b](03b-trial-findings-and-candidate-readiness.md) and [R3c: nine-application validation](03c-cross-stack-validation.md) before the publication gate. R3c requires three Python, three Rust, and three Node.js applications with exact supported-host evidence. Contract review and draft maintenance documentation may proceed independently, but cannot mark the publication gate complete.

Require a named release owner, a frozen candidate commit, passing public-asset installation checks for all advertised targets, completed R3c technical trials, and no unresolved release blockers. Confirm evidence applies to the candidate selected for promotion; earlier green runs from different bytes remain historical. Independent reviews, voluntary reuse, and participant CI are post-publication R3 requirements, not prerequisites for building or publishing v0.1.0.

A waiting period alone is not acceptance. Technical gates determine initial publication readiness; absence of participant availability keeps adoption unvalidated without blocking an otherwise qualified initial release. Public wording must state the tested boundary and cannot claim independent adoption from operator trials.

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

Recompute all checksums, validate dependency notices, and repeat the essential passing, failing, report, cancellation, and archive-extraction paths. Preserve the exact stable commit-to-asset manifest. Run the nine R3c primary workflows with their external checks against the actual stable bytes on each eligible host. A version-label-only rebuild does not require the entire exploratory campaign again. Behavioral changes require a new candidate and affected acceptance reruns before stable publication; never attach old green results to changed bytes.

Acceptance: a complete stable asset set has evidence from the bytes to be published and prints the stable version on every target.

## Checkpoint 4 — Stage, publish, and verify

Prepare a draft stable release with the exact tag/commit, three native assets if all remain supported, checksums, release notes, and links to matching documentation. Confirm release publication is authorized in the session before publishing. Prior release-candidate authorization is not automatically stable-promotion authorization.

After publication, validate public download links and hashes. Update the website and README's install path so new users reach the stable release; avoid leaving a prerelease or expired Actions artifact as the default download. Use stable versioned examples compatible with the released binary, not unreviewed examples from moving main.

Acceptance: the website, release page, binary version, examples, and support table agree.

## Checkpoint 5 — Verify adoption after publication

Start the existing [R3 participant program](03-real-project-trials.md) using the verified stable download. Recruit three to five projects, complete at least three reviews across two stacks, obtain two voluntary second uses, and one successful participant-owned CI integration. Those metrics are owned by R3; this checkpoint requires the first participant stable run and a working triage path. Record installation or upgrade friction and regressions. Announcements must state the tested boundary without implying broad framework certification.

Prepare announcement copy independently of sending it. Public posts, direct messages, and use of participant names require their respective authorization. Release publication does not imply permission to contact third parties through every available channel.

Acceptance: at least one independent participant verifies the stable build, and the maintainer has a concrete issue triage path. If no participant is available, mark publication complete and this post-publication checkpoint pending; do not fabricate an upgrade from an earlier candidate.

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

- [ ] R2, R3b technical evidence, and R3c nine-application results apply to the promoted candidate; publication blockers are closed.
- [ ] Contract audit, changelog, compatibility policy, and support instructions reviewed.
- [ ] Stable-version binaries pass native and extracted-archive checks.
- [ ] Stable release published with explicit authorization and verified public links/hashes.
- [ ] Website and examples lead to the correct stable behavior.
- [ ] Post-publication: at least one independent stable installation or upgrade verified and issues triaged; full adoption tracked in R3.

Handoff: choose Sprint 5 using trial findings. Stable v0.1.0 is a useful stopping point even if later sprint plans are deferred.
