# Playtestr product and launch roadmap

Planning baseline: **6 October 2026**. Execution update: **7 October 2026**, P0–P2 authorized through the [full batch prompt](docs/plans/p0-p2-full-implementation-prompt.md). P0, P1 and P2 accepted within their scoped boundary: recorder/export/replay, generated free workflows, actual same-repository/fork PR journeys and final native/race evidence. Exact status and failures live in the [acceptance record](docs/validation/p0-p2-2026-10-07.md). Later phases remain planned. The [planning index](docs/plans/README.md) owns detailed plans; [archived plans](docs/archive/prelaunch-2026-10-06/README.md) preserve history.

## Direction

Build a self-service, AI-free terminal regression product for pull requests. Proposed launch message:

> Record an important CLI workflow once. Check it on every pull request. Review exactly what changed.

The same reviewed tests run locally and in customer-owned GitHub Actions. Developers choose meaningful workflows and approve expectations. Playtestr records inputs, generates candidate tests, executes them deterministically, and presents evidence. It does not infer intended application behavior or promise automatic whole-application coverage.

The free standalone Go runner, recorder, and basic CI remain useful without an account. The proposed paid GitHub App adds baseline-change review, policy enforcement, and compact review history inside a GitHub-centered workflow. A subscription must deliver those benefits beyond the existing free Actions check and HTML report. No launch claim assumes that people have agreed to pay.

Operate the integration on managed serverless infrastructure. Target zero mandatory recurring infrastructure spend before the first paying customer, conditional on a measured free-tier feasibility gate. Customer applications never execute on the Playtestr backend. Managed scaling removes server administration; security maintenance, defects, and exceptional support still need an owner. Low routine effort is an acceptance target; passive income is not a guarantee.

## Hard constraints

- P0–P2 and the invoked early ten-project P5 reliability pass are complete within their scoped boundaries. Billing accounts, production deployment, spending, releases, marketing and outreach remain outside this authorization.
- Finish the defined product experience and validation before a new commercial launch or marketing campaign.
- Complete **100 distinct independently maintained real projects**, with meaningful pass/defect/recovery evidence. Repetitions, forks, framework demos, and multiple workflows do not inflate the count.
- Keep the application under test language/framework independent and the local execution core in Go. A thin serverless integration may use a provider-native language only after a scoped architecture decision.
- No LLM dependencies, AI test inference, self-healing assertions, or autonomous game exploration.
- No dedicated servers, Kubernetes, customer application hosting, custom enterprise deployments, consulting-led sales, or unlimited support in the launch offer.
- Current release evidence stays valid only within its recorded scope. New plans do not reclassify historical tests as new validation or adoption.
- Publication, spending, remote pushes, and each outreach/PR/issue/discussion mutation still need the applicable explicit authorization. The invoked P0-P2 batch created and closed exactly its two authorized synthetic acceptance PRs; further remote mutations need their applicable authorization.

## Existing foundation and new work

The [baseline audit](docs/plans/00-baseline-and-decisions.md) distinguishes source, recorded verification, and future work. The runner already provides real PTY execution, assertions, text snapshots, bounded outcomes, suites, fixtures/workspaces, offline reports, and an exact-version setup Action. A demonstrated ordinary PR workflow exists. Recording and workflow generation are delivered in the P0-P2 source candidate. The commercial App, entitlements and paid baseline policies remain new work.

The historical corpus records 15 projects and 120 workflows. It is reusable input, **not 15 automatically accepted entries in the new campaign**. Every reused project must meet the new protocol. Current campaign count: **0/100 accepted under this plan**. This is an evidence-accounting reset, not a claim that prior engineering did not happen.

## Dependency order and acceptance

P0–P2 and early P5 runner reliability are accepted within their recorded scopes; P3/P4 and remaining P5–P9 remain **planned / not started**. Effort ranges remain planning forecasts, not an elapsed-time report.

| Phase | User-visible outcome | Exit requirement | Dependencies | Focused effort |
| --- | --- | --- | --- | --- |
| P0 — product and feasibility contracts | A precise promise, paid boundary, and affordable delivery model | Scope, pricing hypothesis, permissions/data model, provider/payment feasibility and known limits decided | This plan; later execution instruction | 1–2 weeks |
| P1 — guided local authoring | Record a real flow and generate a reviewable, rerunnable test | Checkpoints, readiness, fixtures, exits, cancellation, secret avoidance, and compatibility proven | P0 | 3–5 weeks |
| P2 — complete free PR workflow | Committed tests run on a PR and give useful evidence | Build → test → retained failure → local reproduction → reviewed update, including fork restrictions | P1; reuse existing Actions work | 1–2 weeks |
| P3 — paid review integration | Install the App and review changed test contracts/baselines | Revision-bound policy, least privileges, metadata, invalidation, role checks and outages proven | P0 and P2 | 3–5 weeks |
| P4 — automated commercial lifecycle | Buy, activate, cancel, reinstall, export and delete without operator intervention | Payment sandbox, reconciliation, duplicate/out-of-order events, refunds and outage drills pass | P3; eligible provider route | 2–3 weeks |
| P5 — hardening and first 10 projects | Complete experience works on diverse real applications | Ten accepted projects; native/security/format checks; cost and operations measurements | P1–P4 | 2–4 weeks |
| P6 — 100-project validation | Evidence supports a precise compatibility statement | 100 accepted projects, visible failures/exclusions, 20 reserved late projects, native matrix and cost ledger | P5; 10 → 30 → 60 → 80 → 100 | 6–12+ weeks |
| P7 — launch qualification | A frozen, recoverable product can be sold and supported | Final-byte campaign, payment/service rehearsal, docs parity, economics, operations gate and launch packet | P6 | 2–3 weeks |
| P8 — explicit launch decision | Publish the reviewed offer | Owner authorizes exact publication/deployment and selected marketing actions | P7 | Decision, not automatic |
| P9 — low-maintenance operation | Routine purchases and runs need no manual work | Measure incidents, support minutes, margin and repeat use | Actual launch | Ongoing |

Sequential total: approximately **20–36+ focused engineering weeks**, with substantial uncertainty in recorder reliability, App integrity, and project onboarding. This is not a promised launch date. Re-estimate after P0, the first ten projects, and every batch. An overrun triggers a visible scope/date decision; it never silently lowers the 100-project gate.

Keep one implementation slice active. Candidate screening may overlap, but broad qualification follows the complete product. Avoid finishing 100 runner-only demonstrations while the actual paid PR experience remains untested.

## Ready-to-launch definition

1. The claim matches delivered behavior, including the human role in choosing tests and expectations.
2. Free local/CI execution works without service availability. Paid policy checks never fabricate success when evidence, entitlement, or service is unavailable.
3. Authors can record and maintain selected workflows using documented steps. Operator measurements are labeled; human usability evidence is not invented.
4. 100 real projects meet [the campaign protocol](docs/plans/08-real-project-validation.md); all candidate failures/exclusions remain visible.
5. Native and exact-byte evidence cover advertised runner platforms. Project-level host coverage is reported separately.
6. Commercial lifecycle and restricted fork handling pass [security/fault tests](docs/plans/07-security-and-data.md).
7. Install, purchase, cancel, permissions repair, data removal, quota handling and rollback pass without routine manual database edits.
8. Processor fees, infrastructure, founder effort and payout timing are modeled. A measured free-tier path and eligible payment route exist before taking money.
9. No open critical/high-severity trust, cleanup, data-loss, tenant-isolation, billing or core-flow defect remains. Limits are visible before purchase.
10. The [launch packet](docs/plans/11-launch-and-operations.md) identifies exact artifacts, price, policies, evidence, unknown demand and owner decision.

Independent adoption and willingness to pay remain unknown before external use. They are postlaunch commercial measurements unless unsolicited, consented use supplies evidence earlier. Forbidden prelaunch outreach is not a hidden engineering prerequisite. Testing 100 external codebases neither creates 100 customers nor satisfies Marketplace installation eligibility.

## Commercial and infrastructure direction

Working offer: **$49/month per GitHub account or organization**, up to three selected repositories and a bounded result allowance; the annual option is specified in [06](docs/plans/06-commercial-model.md). This is a hypothesis for one simple tier. The conversation's $15 hosting example is not a selected provider bill or subscription price.

Preferred backend: a small Cloudflare Worker, D1 metadata, GitHub-native evidence, and hosted checkout/portal. There is no dedicated server per customer. Capacity grows within provider limits; plan upgrades may require billing decisions. Automatic operation must not imply unlimited automatic spending.

GitHub Marketplace supplies distribution/billing, not backend hosting. Paid-app eligibility requires an early-sales fallback. Prefer an eligible merchant-of-record checkout with no monthly minimum when Marketplace is unavailable. Resolve actual eligibility before committing to a provider; see [dated sources](docs/plans/13-source-register.md).

## Governance and next action

Status lives here; details live in the plans; execution evidence belongs in dated validation records. Public contracts stay accurate to shipped behavior until implementation changes them. Use [milestones](docs/plans/09-delivery-milestones.md), [quality gates](docs/plans/10-quality-and-release.md), and [templates](docs/plans/14-execution-templates.md) when execution is requested.

**Next implementation gate: P3 paid review integration, when invoked.** P0–P2 and early P5 runner reliability are complete. P0 ADRs are in `docs/decisions/`; no provider signup, release or marketing starts automatically.


10 October 2026: [ten-project early reliability pass](docs/validation/ten-project-user-pass/README.md) completed: 33 reviewed scenarios, 330 final fresh passes, 10 detected actual target regressions and all restored scenarios passing on exact source 53561e6. Order: early P5 reliability -> P3 -> P4 -> remaining P5 -> full 100-project campaign. Full P5 and the campaign remain unqualified.
