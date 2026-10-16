# 10 — Quality, compatibility and release gates

Status: future validation protocol. Existing evidence remains dated. [Campaign](08-real-project-validation.md) · [Milestones](09-delivery-milestones.md).

## Current runner-first gate

16 October 2026: [R0-R5](16-runner-stability-and-usability.md) now precede P3/P4. Qualify the expanded standalone runner, recorder, free CI and exact candidate archives independently of unimplemented paid services. The service/payment launch requirements below remain mandatory for the later commercial product. Preparing private candidate artifacts is not publishing a release; publication still needs exact authorization and subsequent actual downloaded-artifact verification.

## Verification layers

| Layer | Proves | Does not prove |
| --- | --- | --- |
| Pure unit tests | Parsing, bounds, normalization, state transitions and policy decisions | PTY fidelity or real provider behavior |
| Real PTY integration | Input/render/process/lifecycle behavior on exact host | Every external application |
| Recorder round trip | Generated tests replay selected useful flows | Automatic discovery of unrecorded paths |
| Actions/App integration | Current revision, permissions, checks and artifacts | Malicious-admin-proof attestation |
| Payment sandbox | Provider events and entitlements under test conditions | Production account eligibility or successful payout |
| Real-project campaign | Listed workflow/version/host samples and defects | Adoption, endorsement or universal support |
| Unattended rehearsal | Recovery and routine operation over a bounded exercise | Zero future maintenance or an SLA |

## Runner and recorder gates

Run formatting, `go test ./...`, `go vet ./...`, meaningful real-PTY tests, the repository race script after lifecycle/concurrency changes, and the appropriate manual examples. Native Linux amd64, macOS arm64 and Windows amd64 runs must actually succeed for claimed support. Use instrumented-test budgets rather than weakening product deadlines. Missing compiler/race prerequisites are reported, never counted as success.

Cover natural exit, exact expected nonzero exit, unexpected exit, readiness mismatch, timeout, cancellation, forced cleanup, descendant cleanup limits, output flood, redraw/resize, Unicode within the stated contract, terminal restoration, recorder-control collisions, paste, path handling and atomic export. A regression test fails before its fix and observes behavior outside the implementation.

Do not rerun the whole suite for this Markdown-only planning change. Later implementation runs the checks its behavior requires.

## Format and migration gates

Existing strict spec/report formats stay valid. If a new action or metadata contract is needed, explicitly choose version behavior; update parser/schema/writer/reader/examples/docs and malformed-input tests together. Verify old accepted specs with the new runner, new documents with older tools' expected rejection, report rendering, mixed suites and rollback behavior.

The service metadata envelope has its own version and bounds; it must not leak fields excluded from local machine reports. A deprecated integration version fails with migration guidance rather than silently dropping assertions or policy fields.

## App and commerce quality

Use deterministic state-machine tests for duplicate/reordered deliveries, retries, revisions, reviewer permissions, term boundaries and quota counters. Add provider-contract integration tests in a sandbox and real GitHub test repositories when specifically authorized. Tenant isolation cannot be proved using a single account fixture.

Fault injection includes HTTP throttling/outage, timeout after side effect, database contention, worker restart, expired token, schema migration failure, lost webhook, retention job failure, unavailable artifact, duplicate checkout and delayed refund. Demonstrate recovery without manual mutation and without contradictory charges/checks.

## Performance and cost targets

Measure launch-to-ready, total suite time, recorder response, service acknowledgment/publication time, peak resources, metadata size, row operations and GitHub API calls. Separate application build/runtime from runner overhead and network wait from CPU.

Proposed UI/service targets under an agreed representative load: webhook acknowledgment p95 under 2 seconds after durable receipt; normal completed-run policy result p95 within 60 seconds excluding GitHub throttling; bounded 15-minute retry window; recorder controls respond without visibly blocking target I/O. Treat misses as findings and re-evaluate design, not automatic permission to hide latency behind “processing.”

The free-tier CPU gate, financial limits and routine-intervention budget are mandatory feasibility checks. Large synthetic traffic tests use authorized bounded resources. No paid load generation or new provider plan is implied by this document.

## Final candidate procedure

1. Select version/channel after scope is implemented; do not assume that relabeling an existing prerelease qualifies new bytes.
2. Freeze source, compiler/dependencies, build flags, archive hashes, Action revision, service code/config/schema, policy version, billing adapter and target/fixture pins.
3. Build once per supported native host, checksum and retain the exact artifacts. Qualify extracted binaries, not just `go run` development code.
4. Run the complete required campaign from 08 against those identities: at least 130 cells, 3,900 good first attempts and per-cell defect/recovery controls. Keep each category separate.
5. Perform upgrade/downgrade and old-format cases, including existing released runner/install paths that remain supported.
6. Finish the 14-day service rehearsal, accessibility review, billing lifecycle and an explicitly authorized small real transaction/refund if production activation is part of launch. Record payout observation separately if it has not arrived.
7. Verify retained evidence and exact public claims. Produce the launch packet; no release/deployment/publication follows automatically.
8. After explicit authorization, publish/deploy and download/verify actual served artifacts. A configuration file or successful build is not proof of deployed behavior.

## Failures and invalidation

No unexplained failure in the final sample is silently retried away. Preserve the first attempt, investigate, classify and demonstrate a fix/recovery. A final acceptance sample after a fix is a new labeled sample. “Zero unexplained failures in this sample” is permitted only with its denominator and scope; “zero flakes” is not.

| Change after freeze | Required response |
| --- | --- |
| Runner/recorder/terminal/dependency/build/version bytes | New artifact identity; rerun affected native tests and full final project matrix for a new launch candidate |
| App policy/provenance/auth code | Repeat security/PR matrix, affected complete project integrations and relevant unattended rehearsal |
| Billing/entitlement code | Repeat lifecycle/fault/tenant cases and affected production rehearsal |
| Workflow/build selection or fixtures | Rerun affected project cells and integration trust cases; update hashes |
| Documentation-only correction | Link/claim/command consistency checks; no fabricated runtime requalification |
| Target pin change | New project-cell evidence; old result remains historical |

If an impact cannot be bounded confidently, broaden validation rather than carrying stale claims forward. Reuse is allowed only with unchanged relevant identities and an explicit rationale.

## Go/no-go

Block for false pass, wrong-revision success, leaked secret, tenant escape, dangerous cleanup, unbounded resource use, unauthorized charge, missing mandatory native/corpus proof or a broken primary journey. Lower-severity issues need visible limitations and owner disposition. Price/demand uncertainty is explicitly documented; engineering readiness cannot prove market demand.
