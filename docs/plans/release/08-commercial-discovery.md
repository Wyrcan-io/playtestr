# A2: evidence-gated commercial discovery

Status: preparation only. Substantive discovery is gated on A1 demonstrating
at least two voluntary later uses. As of 26 September 2026 there are no
consenting participants, repeat uses, willingness-to-pay statements, approved
budgets, or pilots. This document is an interview and decision instrument, not
commercial validation.

## Entry and consent

Invite only willing A1 participants after repeat use. Explain that the
conversation is optional, separate from the product trial, and asks about
current costs and buying process. Record whether notes may be retained, whether
an anonymized finding may be published, and whether a follow-up about a bounded
pilot is welcome. Keep identity, private project details, raw communications,
budgets, and security constraints outside the repository unless the participant
permits that exact publication.

Do not accept payment, promise an SLA, incur service costs, add billing or
accounts, or treat compliments and hypothetical interest as demand.

## Interview script

1. What was the last terminal regression this workflow caught or allowed to
   escape? What did reproduction and diagnosis cost in engineer time?
2. How often does this class of work occur, and how severe is a missed defect?
3. Which current test, manual check, evidence-sharing, and CI handoff steps are
   costly or unreliable? Why would the team retain its present approach?
4. What onboarding or compatibility help would have made the verified
   Playtestr workflow materially easier?
5. Who owns this cost, who approves a purchase, and what procurement, security,
   privacy, deployment, retention, and deletion constraints apply?
6. Would scoped onboarding, compatibility investigation, or ongoing support
   solve a current named problem? Which outcome would justify payment?
7. Which pricing structure fits that task: fixed onboarding, a bounded support
   block, or another existing purchasing pattern? Record ranges as hypotheses,
   not commitments.
8. Is hosted history/sharing necessary, or are local execution and offline
   reports preferable? What exact repeated workflow would it improve?
9. Would the team sponsor a bounded paid pilot with a named payer, success
   criteria, dates, privacy terms, and renewal decision? “Maybe” is not an
   approved pilot.

## Structured findings

Use opaque interview IDs and classify each signal independently:

| Signal | Required evidence |
| --- | --- |
| Problem acknowledged | A recent concrete workflow and cost described |
| Active use | Participant completed a qualifying A1 workflow |
| Repeat use | Separate later voluntary use observed |
| Willingness to pay | Participant states a price/engagement they would pursue for a current need |
| Approved budget | Identified buyer confirms authority and available budget |
| Paid pilot | Written scope and payment completed; not authorized by this plan alone |

For each interview retain the current alternative, frequency, severity,
time/cost estimate with its basis, desired outcome, buyer/approval path,
security/privacy constraints, offer preference, price hypothesis, hosted need,
pilot status, objections, and allowed follow-up. Aggregate only consented,
anonymized findings.

## Cost and offer model

Calculate a range, never a single invented point estimate:

- current monthly cost = incidents per month × people per incident × hours ×
  loaded hourly cost, plus explicitly reported CI/infrastructure cost;
- onboarding delivery cost = preparation hours + live hours + follow-up hours +
  any approved direct cost;
- support delivery cost = expected monthly hours × loaded delivery cost;
- contribution margin hypothesis = proposed fee − delivery cost − approved
  direct cost.

Exclude unmeasured productivity, market-size extrapolation, volunteer time
valued without a stated basis, and hypothetical hosted infrastructure. A first
proposal, if later authorized by evidence, is one fixed-scope onboarding or
compatibility engagement: one project, one workflow, explicit prerequisites,
known-good/intended-bad/recovery, participant-owned CI when suitable, a capped
support-hour budget, privacy/retention terms, acceptance criteria, and an end
date. Price and payment require separate approval.

## Hosted-history decision

Do not build hosted history unless at least two independent teams repeatedly
request it and one has an approved concrete paid-pilot scope. Before a build
decision, document data categories, tenancy, encryption, access, regions,
retention/deletion, incident response, deployment model, operating cost, owner,
and how the standalone local runner and offline reports remain useful without
an account.

## Exit decision

A2 ends with exactly one evidence-backed disposition:

- proceed with one separately approved bounded paid pilot;
- continue discovery for a named missing signal and finite interview target;
  or
- no-build/no-commercialization because observed value, budget, margin, or
  constraints do not support it.

Until A1 repeat use opens the gate, the current disposition is **preparation
complete; substantive A2 not started**.
