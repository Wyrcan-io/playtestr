# 08 — Validation on 100 distinct real projects

Status: campaign designed; **0/100 accepted under this protocol**. No downloads, project execution, CI jobs, PRs or upstream contact are initiated by this planning task. [Candidate discovery](15-candidate-discovery.md) · [Record templates](14-execution-templates.md).

## Runner campaign before the paid campaign

16 October 2026: [16](16-runner-stability-and-usability.md) adds a runner-readiness campaign **before P3/P4**, with its own 0/100 ledger. Reuse the safety, canonical-project, diversity, provenance, failure-preservation and cleanup rules here. Plan 16 owns the stricter runner scenario, public state-assertion and usability gates. Paid App approval and commerce are excluded from runner admission and remain mandatory for later complete-product admission. The original requirements below describe that later complete-product campaign, whose count remains 0/100. A runner qualification is not paid-product qualification. Historical projects can be re-admitted only with the relevant complete package and current candidate evidence.

## What the count means

An accepted project is a distinct independently maintained upstream application with an actual interactive terminal workflow, tested at a pinned revision/version with repeatable synthetic state. Count the canonical upstream identity once. Multiple packages in one repository, forks/mirrors, language ports maintained as the same application, examples shipped by a framework, multiple specs, OS lanes and repeated runs cannot inflate the count.

An operator-authored test on an external project is engineering validation, not an endorsement, maintainer adoption, Marketplace installation or independent human evaluation. The campaign does not require contacting upstream maintainers. Prior refusal/no-contact records remain respected.

Target **100 accepted projects** and publish the total attempted/screened/excluded/failed denominator alongside that number. This is stricter than merely attempting 100 projects. If fewer than 100 can qualify within scope, the launch gate remains open; seek an explicit scope/date decision rather than quietly changing the definition.

Maintain two counters: **accepted on the recorded development candidate** and **qualified on the final launch identities**. The staged 10/30/60/80/100 exits use the first counter; launch requires 100 in the second. A development acceptance never implies final-byte qualification. Relevant changes can invalidate the second counter until reruns complete, without erasing useful prior work.

## Admission and inventory

Screen approximately 130–150 candidates to create an initial 100 plus reserves; this is a planning allowance, not a claimed available population. Use [15](15-candidate-discovery.md) for discovery. Before running each target, record canonical URL, license, maintainer independence, exact pin and integrity source, supported hosts, dependencies, build/install commands, expected meaningful workflow, fixture, risk, resource estimate and disposal strategy.

Reject/defer targets whose only useful path requires real production credentials, costly live infrastructure, uncontrolled external services, undistributable fixtures, unsupported mouse/protocol behavior, or unbounded setup. Keep the reason and attempted evidence. Local disposable service dependencies may be admitted only with explicit setup/teardown and budget.

Existing corpus projects may be reused after satisfying all new criteria, including the recorder/PR integration path where applicable and final frozen-byte requalification. Historical pass counts do not transfer automatically.

## Breadth allocation

Each accepted project gets one primary application category; language/framework/platform are separate dimensions. Proposed distribution to freeze after the first ten projects:

| Primary category | Target projects | Typical meaningful outcome |
| --- | ---: | --- |
| Interactive setup/scaffolding/configuration | 20 | Selected options produce expected files/config |
| Selection/search/navigation | 15 | Correct item selected and emitted/opened |
| Git/repository/developer workflow tools | 20 | Intended local repository state changed |
| Editors/file managers/viewers | 15 | Navigation/edit/save or file operation verified |
| Data/database/HTTP clients using local fixtures | 15 | Query/request/result or saved state verified |
| Monitoring/task/other interactive utilities | 15 | Meaningful stable local interaction completed |
| Total | **100** | |

Coverage goals: at least five implementation-language families and four UI implementation families; no one framework over 40% of accepted projects; at least 30 full-screen applications, 30 prompt/selector applications and 30 stateful outcomes (overlapping dimensions). If admission evidence makes the distribution impractical, document the tradeoff before freezing the next batch. Never substitute trivial `--help` tests to meet a quota.

## Per-project acceptance package

Every accepted project must include:

1. **Pinned installation/build proof:** exact target/runner/dependency/fixture identities and native host. A failed build is not a Playtestr terminal failure.
2. **Three useful workflows:** one primary happy path; one cancellation/invalid-input/boundary path; one second meaningful path such as persistence, resize, navigation, or alternative selection. Three minor input variations of the same trivial command are insufficient.
3. **Reviewed authoring:** use the delivered recorder on at least the primary workflow; keep generated output, reviewed edits and time separately. A manual-only project may supply useful runner evidence but cannot be accepted toward this complete-product campaign until its primary recorder path qualifies. The other two workflows may be authored manually.
4. **Independent oracle:** expected rendered state plus exact exit when relevant, and observable file/Git/database/request state when the workflow changes it. Validate the oracle itself using an intentionally wrong outcome.
5. **Real target defect:** a small local source/configuration change to the target that changes application behavior, caught by an unchanged reviewed test. Record the patch and independently expected symptom. A deliberately wrong snapshot/spec alone is a harness negative, not this requirement.
6. **Recovery:** revert only the target defect and pass the unchanged spec/baseline. Keep hashes proving the test was not weakened.
7. **Fresh-state repeats:** ten first attempts for each of the three workflows on its primary host with the recorded candidate. Repeat the required package against the final candidate for launch qualification. Keep initial failures, timing, output and cleanup evidence; retries are separate attempts.
8. **CI flow:** build/test/report/artifact path for this target using the delivered workflow in an owner-controlled harness. A real authorized synthetic PR demonstrates event-to-result association; copying a report into the UI does not qualify.
9. **Paid review flow:** on that harness entry, an intended snapshot/spec change requires the App policy and a revision-bound approval. Shared sandbox tenants are fine; do not create fake customers or 100 Marketplace installations. Distribute volume across a small documented set of test accounts or an explicitly separate test configuration, keeping production quota logic covered at its actual boundaries. Test entitlements are never revenue or a hidden production payment bypass.
10. **Cost/limits:** authoring/build/run/review effort, resource usage, unsupported behavior, assistance, discovered defects and disposition.

If a project cannot support a safe meaningful target mutation, leave it unaccepted or use a reproducible real historical good/bad target pair with independent issue/commit evidence and unchanged expectations. Mutation labels must distinguish source defects, configuration-induced target behavior, input changes and baseline-only controls.

## Platform matrix

Every project has one actual native primary host. Target at least 60 Linux, 20 Windows and 20 macOS primary-host entries where admission allows it; freeze the final allocation before the broad campaign. Build on existing native GitHub-hosted runners rather than require local devices or SSH hosts.

Select 20 projects for a second supported native host, with ten of those also on the third. This yields at least **130 project-host cells**, not 300. Choose cases across input, lifecycle, full-screen, state and Unicode risks. All three workflows and mutation/recovery run on each admitted extra host.

Minimum final good attempts under that matrix: 130 cells × 3 workflows × 10 fresh attempts = **3,900**. Add at least 130 intended-defect detections and 130 recoveries, tracked separately. Application support claims name actual project/version/workflow/host; the three-host runner test matrix does not imply every app works everywhere.

These are bounded sample counts, not proof of zero flakiness. A campaign can expose defects and demonstrate the exercised sample; it cannot prove arbitrary future behavior.

## Stages and holdouts

| Stage | Cumulative accepted count | Exit / decision |
| --- | ---: | --- |
| V0 screening | 0 | Candidate registry, exact admission rules, resource caps and initial pins |
| V1 pilot | 10 | Complete product journey; repair common authoring/provenance gaps; re-estimate effort |
| V2 breadth | 30 | Multiple stacks/categories; revise docs and fixture patterns from observed failures |
| V3 scale | 60 | Service burst/cost/tenant validation; audit project-count integrity |
| V4 development set | 80 | Freeze feature scope and reserve final qualification inputs |
| V5 reserved projects | 100 | Twenty projects not previously used to tune recorder/runner/App behavior |
| V6 final qualification | 100 on final identities | Rerun all required cells against final artifacts; evidence complete |

Reserve 20 candidates by canonical identity before V2. Metadata screening is allowed; do not author/tune their workflow tests until the product candidate is frozen. Reveal them at V5. If a holdout drives a fix, label it consumed and use a predeclared reserve for any claimed fresh holdout assessment; retain the original failure. The accepted campaign still includes useful repaired projects, but they are no longer untouched holdouts.

## Budget and stop rules

Initial screening target: 30 minutes of operator effort per candidate. Initial authoring/build investigation cap: two hours per candidate before triage, excluding bounded package downloads/build execution. These are investigation limits, not evidence that real apps can all be integrated that quickly. Repeated infrastructure fixes belong in a common harness repair rather than 100 bespoke scripts.

Before each batch forecast runner minutes per OS, dependency downloads, storage, wall-clock deadlines and operator hours. Record actuals afterward. Start serially; shard independent campaign jobs only within a stated concurrent-job cap and safe fixture isolation. No production parallel-runner feature follows from CI sharding.

Stop a batch for any false pass, cross-tenant result, unsafe cleanup, leaked secret, unbounded job or unpaid automatic cost escalation. Reduce the issue, fix with a regression, and rerun affected evidence. A target-specific blocker can be deferred/replaced transparently; a systemic failure cannot be dodged by selecting easier projects.

After every 20-project batch audit category balance, operator effort and rejection causes. If the forecast exceeds the roadmap range, report options and consequences. Do not silently expand runtime budgets or redefine “accepted.”

## Evidence ledger and claims

Per attempt record unique ID, project/workflow/cell, exact identities, mutation status, scheduled inputs, expected result, observed result, duration/resources, artifact hashes, cleanup and classification. First attempts are immutable; corrections append explanatory records. Distinguish target defect, Playtestr defect, test/oracle defect, dependency/build issue, transient infrastructure and unexplained failure.

Retain compact provenance in the repository and bounded raw artifacts under an explicit retention/export policy. An expired remote artifact with no retained admissible copy is missing evidence. Verify availability before launch. Final results must not rely only on old screenshots or summary tables.

Allowed launch statement: “Validated these named workflows on 100 distinct projects at the listed versions and hosts.” Disallowed: “Supports every CLI,” “100 customers,” “100 maintainer endorsements,” “zero flakes,” or “automatically tests your whole repository.” Public project naming follows actual license/attribution requirements and must not imply endorsement.
