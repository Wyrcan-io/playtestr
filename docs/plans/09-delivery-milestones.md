# 09 — Implementation slices and dependencies

Execution update 7 October 2026: P0–P2 explicitly authorized by the invoked [batch prompt](p0-p2-full-implementation-prompt.md). P0-P2 scoped acceptance is complete, including final native/race and real same-repository/fork journeys; evidence and retained failures are tracked in the [dated record](../validation/p0-p2-2026-10-07.md). P3 onward remain unstarted. [Roadmap](../../roadmap.md) sets phase estimates and constraints.

## Working method

One active user-visible slice, one bounded acceptance statement, relevant success/failure/timeout/cleanup checks, manual demonstration when behavior changes, and documentation in the same change. Reuse existing runner/report/installer assets. Stop at a phase boundary for recorded review unless a later execution instruction explicitly authorizes continuation.

Each slice records source base, changed paths, dependencies, format implications, tests, real example, risks and exit decision using [14](14-execution-templates.md). Estimates are updated using observed effort; no speculative implementation of later phases is needed to close an earlier slice.

## P0 — resolve product and provider contracts (1–2 focused weeks)

| Slice | Concrete work when authorized | Exit |
| --- | --- | --- |
| P0.1 baseline audit | Inspect current code/contracts and map reuse versus gaps; reconcile repository instructions with new scope | No duplicate suites/report/installer implementation proposed |
| P0.2 authoring contract | Prototype one fixture-backed wizard recording on paper, choose controls/checkpoints/export/version policy | Clear generated test, failure behavior and terminal restoration contract |
| P0.3 PR trust contract | Select head/merge identity handling, trusted config, exact changed-file policy, approval mechanism and permissions | Every transition in 04 has a testable rule |
| P0.4 backend feasibility | Compare minimal Worker/D1 path, CPU/payload/atomic job limits and thin integration language | Measured safe path or named blocker; zero-spend claim remains conditional |
| P0.5 commercial feasibility | Verify payment-provider eligibility and payout timing; choose first-sale route and provisional offer | At least one plausible self-service billing route; no account/spend without authorization |
| P0.6 freeze decisions | ADRs, API/schema sketches, risk register, revised estimates and candidate-screening contract | Owner can review one internally consistent scope |

Acceptance includes falsification: if paid review adds no useful behavior beyond free checks, revise scope here rather than hide the issue in marketing. If the free tier cannot run the minimum safe backend, resolve the specific cost constraint before investing in billing/UI.

## P1 — guided local authoring (3–5 weeks)

| Slice | Behavior | Required acceptance |
| --- | --- | --- |
| P1.1 safe capture | Forward bounded input to a trusted target and mark checkpoints | Target error/hang/flood, unsupported input, cancellation and terminal restoration |
| P1.2 readable export | Create a reviewed candidate spec/snapshot set | Atomic writes, overwrite/path validation, secret-bearing input preview, strict schema compatibility |
| P1.3 readiness replay | Generated test waits for meaningful state | Slow/fast redraw, stale anchors, noisy output; no timing-only false pass |
| P1.4 fresh-state authoring | Reuse fixtures/home/temp controls | Dirty state, relocation/spaces, repeated runs and cleanup failure |
| P1.5 maintenance flow | Rerecord/edit selected steps and baselines | Existing manual tests remain usable; intended update versus target regression stays distinct |

Use real wizard, selector and full-screen examples. Run relevant native and race checks for PTY/input concurrency. Do not launch broad corpus construction before these fundamentals work.

## P2 — complete free PR flow (1–2 weeks)

P2.1 generates a reviewable workflow from explicit build/test choices. P2.2 preserves failing exit, creates bounded summaries/artifacts and exact context. P2.3 demonstrates pass, deliberate target failure, recovery and local reproduction on an authorized test PR, including fork constraints. P2.4 documents supported triggers, required checks, artifact expiry and removal.

Reuse the existing setup Action, example and report helper. Gate: a fresh repository can follow the documented local → commit → PR → failure → diagnosis → update path without hidden maintainer setup. Do not count a locally simulated event as a real PR integration result.

## P3 — paid review integration (3–5 weeks)

| Slice | Behavior | Required acceptance |
| --- | --- | --- |
| P3.1 installation/auth | Selected repos and verified account identity | Private/public, personal/org, missing permission, revoke, rename/transfer |
| P3.2 result association | A completed run maps to the correct current PR | Malformed result, duplicate event, stale head/base, wrong repo, rerun/cancel, missing artifact |
| P3.3 change inventory | Show altered tests/fixtures/baselines/policy | Renames/deletions, zero selection, changed workflow, policy self-weakening |
| P3.4 reviewer policy | Approve exact change set and publish a distinct check | Unauthorized/self/stale approval, role change, new revision, failed tests |
| P3.5 minimal review/settings UI | Explain pending states and permit account/repo configuration | Keyboard/screen reader, CSRF, tenant checks, useful links and bounded data |

Test synthetic tenants and adversarial artifacts before exposing private repository data. Gate: no route to an accidental green check through stale, missing or mismatched evidence; clearly document the customer-controlled CI trust boundary.

## P4 — automated commerce (2–3 weeks)

P4.1 hosted sandbox checkout and portal; P4.2 durable idempotent entitlement transitions; P4.3 selected-repo/usage enforcement; P4.4 cancellation/refund/reinstall/transfer handling; P4.5 reconciliation, export/deletion and billing fault recovery.

Gate: complete normal buyer lifecycle without manual database edits, custom invoice, per-customer deployment or founder-issued token. Webhook receipt and browser redirect are tested separately. No live payment collected merely to finish a development task. Marketplace adapter is conditional on eligibility; one approved first-sale route is mandatory for launch.

## P5 — hardening and ten complete projects (2–4 weeks)

Admit ten diverse real applications. Complete each package from 08, validate native lifecycle boundaries, establish first authoring/support-cost measurements, run security/tenant/billing tests, and begin unattended operations rehearsal. Reconcile unsupported terminal families against actual workflows.

Gate: ten projects accepted, whole product path exercised, no open critical/high defects, testable unit costs, and a justified revised forecast. This is the checkpoint for rejecting an oversized scope before investing in 90 more projects.

## P6 — broad validation (6–12+ weeks)

Advance 10 → 30 → 60 → 80 → 100 using the frozen admission ledger. Work in bounded batches; fixes need reduced regressions and an evidence-invalidation decision. Capture changing upstream pins rather than letting latest dependencies drift. Do not alter final count semantics to meet a date.

At 80, freeze feature scope and build the candidate before revealing reserved projects. At 100, all acceptance packages must be complete or explicitly remain unaccepted. Shared backend/billing testing complements project workflows; it does not create extra project credits.

## P7 — exact release and operations qualification (2–3 weeks)

Freeze runner archives, recorder, Action, service deployment/configuration/schema, policy and billing adapter. Execute final 130+ project-host matrix and 3,900+ good first attempts plus controls. Complete migration/rollback, native lifecycle, provider outage, quota, production-payment rehearsal when authorized, artifact availability, accessible onboarding/review and public-doc parity checks.

The 14-day unattended rehearsal may overlap candidate qualification, but relevant behavior changes invalidate affected results and may restart the rehearsal. Produce a signed-off checklist and launch packet with failed attempts/limitations preserved. “All code merged” is not the gate.

## P8/P9 — launch decision and operation

P8 prepares exact release/deployment/publication actions for authorization. Source availability or a previous prerelease does not authorize a new commercial announcement. P9 measures real conversion, retained use, support burden and margins after launch. Follow [11](11-launch-and-operations.md).

## Scope control and severity

- Critical/high correctness/security/billing defects interrupt feature work.
- A target-specific unsupported case may be deferred with a visible exclusion; a common promised workflow failure blocks its phase.
- New feature requests enter [12](12-risks-and-decisions.md) with observed need, minimum design, maintenance cost and gate impact.
- A missed throughput/time target requires an explanation and decision. Never weaken correctness or erase initial failures to hit it.
- Native validation uses standard GitHub-hosted runners when local hosts are absent. Actual runs and retained artifacts are required; no demand that the user acquire devices.
- No absolute launch date until P5 supplies realistic effort and provider constraints.


10 October 2026: [ten-project early reliability pass](../validation/ten-project-user-pass/README.md) completed before paid integration: ten diverse applications, 33 scenarios and 330 final fresh passes, with actual target-regression/restoration evidence and temporary applications removed. Order: early P5 reliability -> P3 -> P4 -> remaining P5 -> full 100-project campaign. Full P5 and the campaign remain unqualified.
