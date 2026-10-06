# 12 — Decision register, risks and backlog

Status: planning baseline. The owner is the Playtestr maintainer unless a later execution record names another responsible person. Decisions below are not external-action authorizations.

7 October execution: the user invoked P0–P2 and authorized the scoped commits/pushes and synthetic acceptance PRs. D10 describes the original planning change, not this execution. Q01–Q05 and authoring/state-oracle Q09 now have scoped conclusions in [authoring/PR ADR](../decisions/p0-authoring-and-pr-contract.md) and [managed/commerce ADR](../decisions/p0-managed-backend-and-commerce.md). Q06 has a provisional hosted route and source-verified requirements; actual seller facts/approval remain owner gates before P7. Q04 deployed CPU/cold-start proof remains before P5. Q08 free restricted-fork execution is accepted with actual passing/defect/recovery evidence in P2; future App API publication/tenant binding remain P3. Pricing/demand/operations/100-project acceptance are not inferred from this batch.

## Direction decisions selected for this plan

| ID | Decision | Rationale |
| --- | --- | --- |
| D01 | Position as terminal regression checks for PRs | One narrow user job across local and team use |
| D02 | Free standalone core/recorder/basic CI; paid review automation | Preserve useful adoption path and identify a distinct paid benefit |
| D03 | No AI or automatic correctness inference | Deterministic authoring/execution; explicit developer intent |
| D04 | Customer-owned Actions execution and evidence | Avoid hosting arbitrary target code and its compute bill |
| D05 | Managed serverless service with small metadata only | Minimize routine operations and pre-revenue cost |
| D06 | One provisional $49 tier; no consulting-led revenue | Simple self-service offer aligned with low support effort |
| D07 | Complete product plus 100 accepted real projects before marketing | User-selected launch gate |
| D08 | Operator testing is not adoption/install evidence | Honest claims and no Marketplace-count confusion |
| D09 | Preserve evidence; replace active plans | New direction without erasing provenance |
| D10 | No implementation in this change | Explicit user boundary |

## Decisions to close during implementation

| ID | Question / default | Evidence needed | Deadline |
| --- | --- | --- | --- |
| Q01 | Can paid baseline-policy review justify the offer? | Concrete workflows beyond free check/report, comparison and effort model; demand remains unproven | P0, reassess postlaunch |
| Q02 | Recorder controls and public format changes? | One complete wizard spec and unsupported-input/error cases; strict reader compatibility | P0/P1 |
| Q03 | Review UI versus native GitHub review event? | Exact role/revision semantics, minimal permissions and self-service usability | P0 |
| Q04 | Worker/D1 free-tier viable? | Worst allowed payload, signature/crypto CPU, atomic jobs, retries and indexed queries | P0, actual deployed proof before P5 |
| Q05 | Thin TypeScript integration justified? | ADR comparing provider fit and maintenance; Go core preserved | P0 |
| Q06 | Which eligible payment route? | Actual seller/product/geography verification, no-monthly-minimum terms, payout/refund/portal capabilities | P0 feasibility; production eligibility before P7 |
| Q07 | Price/limits economical? | Measured service cost, worst allowed account, fee/payout model, support sensitivity | P5; freeze before P7 |
| Q08 | GitHub permission/API route sufficient for forks? | Real restricted fork run, manifest/run association, App publication and role tests | P2/P3 |
| Q09 | Scope of persisted-state assertions? | Existing harness lifecycle proof; minimal new hook only if necessary | P1/P5 |
| Q10 | Can 100 meaningful projects qualify? | Candidate denominator, category coverage, repeated blockers and effort forecast | First 10 and every batch |
| Q11 | Which final version/channel? | Actual changed contracts and exact-byte qualification plan | Before V5/P7 freeze |
| Q12 | Marketplace ready? | Installation count, publisher/listing approval and current commercial agreement | Before enabling Marketplace billing; external route may launch first |
| Q13 | Low maintenance demonstrated? | 14-day rehearsal and all intervention hours, rollback/restore/deletion drills | P7 |
| Q14 | Public paid-service terms/licensing complete? | Accurate ownership/license boundaries, privacy/retention/refund/provider obligations | P7 |

No unresolved critical feasibility decision may be disguised as a later implementation detail. If a chosen provider cannot satisfy the constraints, record alternatives and select one before committing the dependent feature.

## Risk register

| Risk | Early signal | Mitigation / stop |
| --- | --- | --- |
| Paid service is a redundant comment | Team scenario requires no review automation beyond free Git | Redesign paid value at P0; no paid launch on cosmetic value alone |
| Recorder generates brittle tests | Stale anchors, replay failures or long edits | Explicit checkpoints/fresh fixtures; pause broad campaign for a shared fix |
| Backend exceeds free CPU/resources | Worst-case request exceeds allowance | Smaller bounded work or alternate managed plan; no hidden spend |
| Marketplace/payment eligibility blocks first sale | Rejected/unavailable provider route | Eligible hosted fallback; block paid launch if none works |
| PR weakens its tests unnoticed | Changed selection/policy incorrectly passes | Trusted-base comparison and exact revision approval |
| False evidence association | Old run/foreign repo marked successful | Mandatory provenance checks; critical launch blocker |
| Service becomes support consultancy | Repeated manual fixes/authoring | Better self-service, scope limits; reject bespoke launch commitments |
| Corpus count is padded | Demo/fork duplicates or trivial workflows | Canonical IDs and independent count audit |
| Project population insufficient | High exclusions/common unsupported interactions | Re-estimate early; user decision, not lowered criteria |
| 100-project scope grows indefinitely | Overrun in each batch | Bounded triage/reserves; fixed feature scope at 80 |
| Upstream changes invalidate pins | Install disappears/dependency drifts | Integrity, retained fixtures, exact dependency locks |
| Free installs/abuse consume paid margin | High API/row use without collections | Global/per-tenant controls; preserve billing/deletion capacity |
| Provider outage blocks required reviews | Long pending checks | Durable retry, honest status, documented owner override; no false green |
| Large integration dependency burden | Frequent compatibility incidents | Small surface, pinned versions, scheduled compatibility checks |
| No one pays after engineering | No repeat paid feature use/conversion | Bounded 30/60/90-day commercial decision; preserve useful free product |

## Deferred backlog and entry criteria

Hosted execution requires explicit new product economics/security approval. Additional SCM providers need paying demand. More tiers need observed capacity/value segments. JUnit, parallel runner, SDKs, broad mouse/styles/graphemes and change-based test selection need named blocked workflows, a minimal contract and maintenance cost. Enterprise SLAs/on-prem/consulting conflict with the present operating model and are not implicit growth milestones.

A recorder compatibility fix needed for an admitted promised workflow is current-scope triage, not automatically backlog. Autonomous discovery/AI remains outside this direction unless the user explicitly changes it.

P0-P2 acceptance is complete in [the dated record](../validation/p0-p2-2026-10-07.md). Retain its intermittent earlier Windows wizard input/resize timeout as a P5 reliability investigation; later green runs are not a proven causal fix. No broad compatibility or final commercial qualification follows.
