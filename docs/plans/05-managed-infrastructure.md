# 05 — Managed infrastructure and unattended operation

Status: proposed architecture, subject to P0 feasibility. [Commercial model](06-commercial-model.md) · [Security/data](07-security-and-data.md).

## Topology and responsibilities

| Component | Responsibility | Operator burden |
| --- | --- | --- |
| Customer GitHub Actions | Build and execute targets, retain artifacts | Customer chooses runner/retention; GitHub provisions hosts |
| Cloudflare Worker | Signed events, GitHub API calls, settings/review endpoint, entitlement decisions | Provider operates runtime; we maintain code/secrets/configuration |
| Cloudflare D1 | Small tenant, subscription, job and review metadata | Provider operates storage; we own schema/indexes/retention/recovery |
| GitHub | Identity, repository authorization, checks and artifact access | API compatibility and permissions remain our concern |
| Hosted billing provider | Checkout, invoices, payment portal and subscription events | Provider onboarding and exceptional disputes still require attention |

One deployment serves multiple isolated tenants. No server per customer, target execution service, persistent terminal session, raw recording service, Redis cluster, VM or container fleet. No separate managed Postgres/Supabase subscription is required by this plan.

Use a provider-generated endpoint initially if an owned domain would introduce pre-revenue cost. The public product website can remain separate from the small authenticated service. Do not use GitHub Pages as an assumed commercial application backend.

## Language boundary

Keep runner/recorder in Go. A thin TypeScript Worker is the preferred integration candidate because it uses native request/crypto/D1 interfaces; P0 must document why this bounded second language reduces deployment burden. It may not reimplement terminal logic or change the standalone dependency requirement. If a supported Go deployment option has lower measured maintenance, choose it in the ADR instead.

## Metadata and jobs

Store stable GitHub IDs, installed permissions, repository selection, policy versions, subscription/provider IDs, entitlement period, delivery deduplication keys, bounded pending jobs and compact review outcomes. Never store source trees, target executables, raw terminal streams or payment-card data.

A received event is verified and durably recorded before acknowledgment. Process short tasks synchronously where bounded. Longer/retry tasks use a small D1-backed due-job table plus scheduled worker batches if a feasibility spike proves atomic claiming, bounded contention and recovery. Otherwise evaluate a managed queue and its free-tier/cost implications before adding it. Do not rely on a background promise completing after a response without durable state.

Jobs have type, tenant, external identity, lease, attempt count, next-attempt time, payload reference and terminal outcome. Unique keys and atomic state changes prevent duplicate effects. GitHub publication reconciles against an existing external check ID. Payment reconciliation uses provider state/version, not arrival order alone.

## Launch quotas — proposed starting contract

| Limit | Initial target | Customer-visible handling |
| --- | ---: | --- |
| Selected repositories per paid account | 3 | Explicit selection; no silent rotation to evade limits |
| Accepted review evaluations per billing month | 1,000 total across selected repositories | Usage meter/reset time; no automatic overage charge |
| Paid result metadata envelope | 64 KiB decompressed (P0 revised) | Compact summaries; raw reports stay in GitHub; reject oversized/unknown fields |
| Test results in envelope | 1,000 | Require summary/chunk contract if genuinely needed later |
| Backend raw screens/artifacts | 0 retained | Links to customer-owned GitHub artifacts |
| Retained review/outcome metadata | 30 days | Explain expiry and export before deletion |
| Event delivery audit | 7 days, IDs/status only | Debug without retaining raw event bodies |
| Retries per evaluation job | 5 within 15 minutes | Exponential backoff/jitter; terminal unavailable outcome |
| Maximum target runtime in customer CI | Customer-configured bounded job/spec budgets | Customer pays for chosen capacity; no hosted minutes sold |

Duplicate delivery of the same run attempt does not consume another evaluation. A genuinely new attempt can consume one. Failed user tests count once because review processing still occurred; rejected unauthenticated payloads do not bill the tenant. Free local/CI runs are not metered by Playtestr. Final values require P0/P5 workload measurements and consistent checkout/docs wording.

## Zero-spend feasibility gate

Provider free allowances are finite. [Sources](13-source-register.md) record current Workers/D1 constraints, including CPU limits. P0 measures signature verification, token signing, GitHub calls, indexed D1 queries and bounded result parsing using worst-case allowed inputs. A request-count allowance alone cannot prove viability.

Gate: the complete first-customer path works within free CPU/memory/storage/request limits with headroom, durable retries and reliable billing callbacks. Test bursty events and expired credentials. Simulate limits locally first; deployed free-tier proof requires a later explicit deployment instruction.

If the minimum safe path exceeds free capacity before revenue, choose smaller payloads/work units or another managed free tier. Record failure honestly. Do not silently subscribe or claim zero cost. If no safe no-spend route works, return that specific decision before commercial launch.

## Capacity and cost controls

The provider scales runtime within configured limits; account upgrades, database limits, external API quotas and spend controls do not disappear. Target a single plan upgrade with no application rearchitecture for the first paid growth step. Do not promise upgrades happen automatically or that payment is instantly available as cash.

Use per-tenant and global rate limits before expensive work, explicit CPU bounds, bounded scheduled batches, indexed queries, concurrency caps, payload limits and retention jobs. Measure actual requests, CPU, rows read/written, retained bytes, API calls and queue age per accepted evaluation.

Proposed operating thresholds: alert at 60% and 80% of each relevant allowance; at 90% pause new installations/evaluations as needed and show degraded status while reserving capacity for billing, deletion and recovery. Percentage targets are application controls, not assumed provider hard spending caps. Paid-tier emergency limits must be tested; provider budget alerts alone may not stop a bill.

Before a capacity upgrade, verify collected revenue/payout timing, recent unit cost and an explicit spend ceiling. The owner can authorize a standing bounded budget later; no such authorization exists in this plan. Scaling within that approved envelope should be automatic.

## Deployment, recovery and portability

Plan separate test and production environments, versioned configuration, staged deploys and automated smoke checks. Use backward-compatible expand/migrate/contract database changes. Keep previous Worker version rollback available; verify older code handles transitional schema. Never roll back by deleting current customer records.

Exercise database export/restore with a provider-supported mechanism available on the selected plan. Specify recovery-point and recovery-time targets after measuring restore behavior; provisional goals are 24 hours for compact metadata and four hours to restore service during staffed response. Do not sell an SLA based on these internal goals.

Reconcile installation, subscription and run state from upstream sources after a lost/delayed webhook. Recovery should not require inspecting every customer manually. If the provider cannot replay all deliveries, scheduled reconciliation supplies missing state; document the interval and bounded search window.

## Operations acceptance

Run a 14-day prelaunch unattended rehearsal with synthetic accounts/events and injected dependency failures. Require zero routine manual entitlements, invoices, result corrections or job restarts; record all exceptional interventions. Verify alert deduplication, budget protection, rollback, deletion, provider reconciliation and credentials rotation. Synthetic duration supports operational readiness, not a uptime guarantee or customer adoption claim.
