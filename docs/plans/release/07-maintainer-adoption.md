# A1: maintainer adoption after engineering

Status: deliberately deferred until Sprints 11–14, dispositions of 6/10/12-B, and R6 are complete. This replaces older recruitment timing. Owner: project maintainer. Existing [R3 protocol](03-real-project-trials.md), participant templates and cohort ledger may be reused, without treating operator tests as independent runs.

## Entry and recruitment

Prepare the verified release, three recipes, real failure report, exact support limits, removal instructions and a one-page trial guide. With explicit authorization to contact chosen recipients, invite five consenting maintainers across at least three implementation ecosystems. Include an existing framework-test user, a custom-script user and someone relying on manual checks if feasible. Do not manufacture names, endorsements or participant CI.

Recruitment starts here, not during engineering. Unsolicited inbound feedback can be recorded earlier without claiming adoption completion. If participants are unavailable, keep the outcome open and revise recruiting, not the feature roadmap. Review progress after two weeks of actual recruitment; do not invent another engineering batch merely to postpone discovery.

## Interview and observation protocol

Ask about the last real terminal regression: what broke, how it escaped, time spent reproducing it, current tests/manual process, host/CI constraints, and which one flow matters enough to protect. Ask why they would keep their current tool. Do not lead with our feature wishlist or ask only whether they like the demo.

Observe an unassisted first attempt, then offer help and record it. Tasks: install; adapt one assertion; pass; seed or use a known defect; identify the failure; recover; review one baseline update; integrate their selected flow into their CI. Record setup time separately, abandoned attempts, errors, assistance, evidence interpretation and reasons for declining.

For a willing subset, compare their current method and Playtestr on matched fresh tasks, alternating tool order. Measure setup/diagnosis effort and preference, not just lines of JSON. Do not replace existing unit tests to force a win.

## Acceptance and follow-up

| Outcome | Target, not yet achieved |
| --- | --- |
| Initial understanding | 4/5 explain what the demo caught and the tool's boundary |
| First useful test | 4/5 complete pass/failure/recovery within 10 minutes after prerequisites; installation separately measured |
| Diagnosis | 4/5 identify seeded defect within 2 minutes from evidence |
| Real value | 3 participant-reviewed good/bad/recovered workflows across at least 2 stacks |
| CI | At least 1 successful participant-owned CI integration with actual result reference |
| Retention | At least 2 voluntary uses in separate later sessions, checked after 2–4 weeks |

Small samples guide decisions, not population claims. Record all five outcomes including dropouts. Missed targets remain findings; do not coach until a nominal pass is recorded. Respect privacy and obtain permission for quotations, names, screenshots and case studies.

If authors cannot find a valuable flow, revisit positioning. If onboarding is the barrier, fix that journey. If repeated use fails on correctness, repair the reduced defect. If teams prefer their existing tool, document why. Each resulting change gets its own narrow acceptance boundary; no automatic feature-parity roadmap.

## Commercial discovery after repeat use

Keep the standalone local workflow open-source and useful without an account. Start commercial conversations only after repeated independent use, initially with roughly five unrelated active projects as a discovery trigger, not proof of a business.

Ask who owns the cost, what failed CI/debugging consumes, whether support is purchased today, who approves spending, and what they would pay to solve a specific recurring problem. Prefer scoped onboarding, compatibility investigations or support engagements first. Prices remain interview hypotheses; no revenue forecast is justified yet.

Consider hosted history/sharing only if at least two independent teams repeatedly request it and one agrees to a concrete paid pilot. Define the pilot task, payer, success criteria, privacy/retention needs, support hours, infrastructure cost and renewal decision before building. A request alone is not willingness to pay. Keep local execution and offline reports functional if no service exists.

Advance only with measured paid value and plausible support margins. Stop or revise if customers do not return, costs exceed value, or a service distracts from runner reliability. No billing/accounts/dashboard implementation is authorized by this plan.
