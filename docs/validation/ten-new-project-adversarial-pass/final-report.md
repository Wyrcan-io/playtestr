# Final frozen-source validation report

The scoped terminal/state matrix passed its strict retained-evidence audit. This completes the ten-project engineering qualification; the usability assessment retains explicit measurement limits. This is early runner hardening, not full P5 or commercial launch acceptance.

- Frozen source: `e8682f866622442c421005c7f477cd45fcc66fc5`.
- Actual successful [native run 38802794545](https://github.com/Wyrcan-io/playtestr/actions/runs/38802794545).
- [Strict audit](final-audit.json) and [immutable native manifest](native/38802794545/manifest.json).
- 130 distinct scenarios, 21 qualified project/host pairs.
- 2,740 ordinary final repetitions, including 1,300 on native Linux.
- 2,740 separately executed final-group state probes; not additional scenarios or same-execution file assertions.
- 31 distinct real target source-fault controls, 65 executions across hosts, with actual restored recovery evidence.
- 10 distinct independent-state corruption controls; 21 executions across hosts.
- Full-product 100-project campaign credit: **0/100**.

## Project matrix

Every row uses ten fresh ordinary executions and ten separate state probes per scenario on each listed host. Counts below are per host. All listed native jobs verified owned application removal.

| Project / exact upstream revision | Normal / edge | Qualified native hosts | Ordinary + separate state per host |
| --- | ---: | --- | ---: |
| [cookiecutter](cookiecutter/README.md), `c88fbe921c97c58b65f1883ba90a0ab53cc91b34` | 5 / 5 | Linux, Windows | 100 + 100 |
| [copier](copier/README.md), `04a8619f3b083bc278b70e556bd085551a2b3f79` | 6 / 6 | Linux, Windows | 120 + 120 |
| [lf](lf/README.md), `5d3c7b702515dfb72d8d496673fa1c4144d1dbed` | 6 / 6 | Linux, Windows | 120 + 120 |
| [superfile](superfile/README.md), `66fe169b87021f7424522ed5aadd711c5676601e` | 6 / 6 | Linux, macOS | 120 + 120 |
| [helix](helix/README.md), `ba40e547426b0f9896c8bdc699a4ab11f2b37dbc` | 6 / 6 | Linux, Windows | 120 + 120 |
| [glow](glow/README.md), `8b0600fa445535b9c53194c0d4f7fe3cf700ef3e` | 6 / 6 | Linux, macOS | 120 + 120 |
| [broot](broot/README.md), `41cb4c78d9d7736dfe83c65f8a393fc962e50662` | 6 / 7 | Linux, macOS | 130 + 130 |
| [yazi](yazi/README.md), `f220cb6fb1018c7c656077e30b1aefbac136f719` | 7 / 7 | Linux, macOS, Windows | 140 + 140 |
| [ranger](ranger/README.md), `46e957af9762dd2fcaabfbef4d3c45c16edd1184` | 7 / 9 | Linux, macOS | 160 + 160 |
| [nnn](nnn/README.md), `c3e00d99cc83c71a9a0d285669775ae3c82db38e` | 7 / 10 | Linux, macOS | 170 + 170 |

The scenario total is 62 useful normal cases plus 68 distinct edge cases. Platform variants remain one scenario. The registry screened nineteen candidates and records pins, licenses, reserves and exclusions; see [candidate registry](candidates.json).

## Product controls and runner identities

The [coverage matrix](coverage-matrix.md) maps 88 distinct product controls. Actual frozen normal and race events contain every applicable definition: 80 on Linux, 80 on macOS and 86 on Windows. The macOS freeze also passed fifty additional race-instrumented stubborn-descendant checks. The historical wizard sequence passed 100 actual frozen-binary reproductions on Linux and macOS, and two separately instrumented Windows variants of 100 each. These are reduced product controls, not external project scenarios.

| Native host | Frozen runner SHA-256 | Detailed race events |
| --- | --- | --- |
| [Linux](core/frozen-host-evidence-Linux.json) | `1eec08e3589bad7bb9066fe72e6e8b44752c4153389d02a93de3cdc557f66844` | [Events](core/final-race-events-Linux.jsonl) |
| [Darwin](core/frozen-host-evidence-Darwin.json) | `e3fdfb495f1a0eb35d68a90a25e3be954577db7895f8daebae6a2d7e3a2789c3` | [Events](core/final-race-events-Darwin.jsonl) |
| [Windows](core/frozen-host-evidence-Windows.json) | `9a05973c401bd191b318329734539c8c3573581a74fc457e73829a9f3c884117` | [Events](core/final-race-events-Windows.jsonl) |

## Repairs, failures and useful confidence

The [findings register](findings.md) retains general runner, recorder, lifecycle, input, environment and evidence repairs, their before/after controls and affected requalification. Production Go code has no target-name special cases. Actual application mutations were confined to owned checkouts and restored; minimal patches and evidence remain, not application source or dependencies.

The first frozen attempt failed Copier Windows Git-update preparation and remains rejected. Twenty traced probes justified its predeclared Windows-only 20-second budget; assertions, snapshots, Unix deadline and the total scenario budget stayed unchanged. Corrected Copier qualification preceded this new all-ten run. [Calibration and first failure](copier/git-update-budget-calibration.json). The host-case selection audit repair preserved all 390 driver mappings and changed no public contract or Go input.

One earlier macOS stubborn-descendant readiness failure has no established cause. Subsequent successes do not resolve its cause. Windows Superfile and Glow remain unqualified after real pinned-upstream input-race findings. [Known limits and unsupported claims](limitations.md).

The demonstrated confidence is specific: the declared trusted applications can be driven through useful interactive workflows with reviewed rendered-screen assertions, bounded accurate failure outcomes, fault/restoration evidence and owned cleanup on the listed hosts. The independent state checks detect declared corruptions that terminal snapshots alone miss. Arbitrary app behavior, exhaustive terminal compatibility and every possible investor stress test remain unproven.

## Usability, accounting and next scope

The [usability assessment](usability-assessment.md) retains short public-command routes, maintenance, failure diagnosis, rerecord and relocation evidence. All recorded first routes meet five-command and twenty-recorder-control ceilings. Eight elapsed measurements are automated prepared walkthroughs; human authoring time is unmeasured there. This is an experienced operator assessment, not independent beginner or adoption research.

[Final negative-attempt dispositions](final-negative-attempts.json) bind all 46 non-passing final-run command records to 21 actual saved-state corruption probes and 25 deliberate harness calibrations; no unexplained non-passing command remains in that final run. Their original failure categories remain unchanged.

[All-attempt accounting](all-attempt-accounting.json) snapshots the original categories, unfinished IDs and ledger hashes. Setup, parent commands, intentional failures and retries are not added to final repetition credit. The original quarantined ledger remains unchanged. The completed native manifest preserves reports, fault screens, state inventories, restoration identities and hosted deletion receipts. Raw downloaded archives also duplicate historical provenance; per-project budget inventories are distinct from those whole archive sizes and do not measure peak resource usage.

[Final local cleanup receipt](core/final-local-cleanup.json): no task-owned external application checkout remains locally. Every qualified host confirms removal before the next repository starts. Shared Playtestr toolchains and existing caches are preserved.

P3 paid review integration, P4 buyer lifecycle, remaining complete-product P5 and the full 100-project campaign remain planned. No release, outreach or marketing follows automatically from this engineering pass.
