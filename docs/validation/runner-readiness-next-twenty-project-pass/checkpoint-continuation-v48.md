# Continuation checkpoint v48: 9 November 2026

Branch `work/p0-p2-implementation` is pushed at `530893f4`. The campaign
remains four of twenty new projects qualified on exact rc.6 (14/30 cumulative);
original-ten current-candidate qualification remains zero.

## Skim

Historical exact rc.6 packet `42506300345` remains independently audited in
readback v8 (240 ordinary outcomes and nine fault phases per host). The newer
V31 run `42514930671` passed the exact-series preflight and independent plan
audit, ran all 240 ordinary cases and nine fault phases on both Linux and
Windows, and completed source/process proof, bounded cache cleanup and checked
target removal on both hosts. It earns no admission credit yet.

The public-authoring route then failed on both hosts before any route target
launch. `NextCampaign(phase='public-authoring')` refused the new phase because
`readiness_evidence.Campaign` omitted it from the explicit allowlist. The plan
receipt was therefore not created; the outer command audit records the refusal.
This is a harness phase-validation defect, not an application result. The first
two later immutable contract-freeze attempts were separately preserved as
zero-launch V29/V30 hash failures.

V32 fixes the phase allowlist, adds an explicit allowed-phase regression, and
includes `test_readiness_evidence` in the hosted preflight suite. All 46 focused
Skim planner, cleanup, acquisition, storage, evidence and phase tests passed
locally; four tests skipped only for Unix symlink/socket/FIFO behavior that
cannot be created on this Windows host. All 57 staged V32 harness hashes match
the Git index. Readback v9 independently verifies V31's provider ZIP digests,
24 batch hashes, all 480 report and finished-receipt hashes, passed steps,
unique invocation IDs, three faults, nine phases, recovery, and source/target
restoration on both hosts. V31's public route still failed before launch. Next,
push V32, confirm both hosted freeze/plan audits pass, run and independently
audit the exact series, faults, public route and cleanup.

## Taskell

Exact rc.6 run `42513404363` finished with zero admission credit. Linux built
the pinned target and ran all twelve batches, but case E11M failed in eleven
batches and passed only in the larger-viewport batch 4. The retained failure
report records `unexpected_exit` before the `Could not parse file.` expectation;
its bounded final-screen evidence contains that diagnostic, and the same-run
file-state evidence confirms the malformed fixture remained unchanged. Treat
this as an unresolved candidate/output-observation defect; do not mask it by
reordering the contract or counting the earlier source-built route.

The macOS exact job and paired source-fault job both stopped before target
execution because LLVM 12's signed MacPorts dependency graph also needs
`libxml2.16.dylib` and `libz.1.dylib` inside the owned prefix. The latest fault
Linux attempt built the target and entered the three source-fault phases; its
artifact must be audited separately. Taskell is not admitted.

## Remaining work

After Skim's V32 host jobs have completed cleanup, continue Taskell's exact
candidate investigation and close the signed MacPorts dependency graph with
bounded extraction and independent signatures. Then qualify the remaining
selected applications sequentially, refresh the original ten on the claimed
candidate, and complete applicable migrations, 88+33 whole controls, archive
controls, two refreshed delivered-CI triplets, tamper controls, exact storage,
fresh checkout and campaign cleanup. Preserve `.codex-go-cache/` and
`.codex-test-tmp/`; neither is campaign scratch.
