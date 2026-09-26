# R6 evidence index — 25 September 2026

| Boundary | Durable record | Live run / retained raw evidence |
| --- | --- | --- |
| Adversarial rehearsal | [Sprint 13-D](sprint-13-d-rehearsal-2026-09-24.md) | Local ignored rehearsal artifacts |
| Candidate source/archive identity | [R6-F](r6-f-candidate-freeze-2026-09-25.md), [manifest](../../release/candidate-manifest.json), [checksums](../../release/checksums-v0.4.0-rc.1.txt) | [Build 36103641387](https://github.com/Wyrcan-io/playtestr/actions/runs/36103641387) |
| Native source/contracts/action | [R6-Q](sprint-11-c-r6-q-2026-09-25.md) | [Terminal 36103628695](https://github.com/Wyrcan-io/playtestr/actions/runs/36103628695), [native gaps 36103628701](https://github.com/Wyrcan-io/playtestr/actions/runs/36103628701) |
| Frozen preflight | [R6-Q](sprint-11-c-r6-q-2026-09-25.md) | [36103801262](https://github.com/Wyrcan-io/playtestr/actions/runs/36103801262), 30/30 |
| 120 workflows / 15 controls / recoveries | [R6-Q](sprint-11-c-r6-q-2026-09-25.md), [compatibility](../qualified-compatibility-v0.4.0-rc.1.md) | Sanitized classifications durable; raw local ignored reports retained |
| Exactly 3,000 first attempts | [R6-Q](sprint-11-c-r6-q-2026-09-25.md) | [36106092065](https://github.com/Wyrcan-io/playtestr/actions/runs/36106092065), three 14-day ledger artifacts |
| Upgrade preparation | [migration](../migration-v0.4.0-rc.1.md), [R6-Q](sprint-11-c-r6-q-2026-09-25.md) | Local ignored old/new runner artifacts |
| Three release stories | [story manifest](../../release/story-manifest.json), [gallery](../demo-gallery.md) | [36108031093](https://github.com/Wyrcan-io/playtestr/actions/runs/36108031093), three 14-day artifacts |
| Website/report presentation | [R6-K](sprint-14-r6-k-2026-09-25.md) | Local screenshots and browser output; interactive screen-reader audit remains open |
| Publication | [Publication and verification record](r6-publication-and-blocker-2026-09-25.md) | [v0.4.0-rc.1](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.4.0-rc.1) |
| Detected setup-action defect | [Publication and verification record](r6-publication-and-blocker-2026-09-25.md) | [36168381776](https://github.com/Wyrcan-io/playtestr/actions/runs/36168381776), failed safely on all three hosts |
| Repaired public setup action | Same record; immutable action `1c03904075512e67f53b0c94a13daa17f0383f1d` | [36172240134](https://github.com/Wyrcan-io/playtestr/actions/runs/36172240134), passed on all three hosts |
| Public bytes, behavior and genuine upgrade | Same record; workflow pin `22118a3af7f07f26a2e519dafbac518bbc8d98c6` | [36173075209](https://github.com/Wyrcan-io/playtestr/actions/runs/36173075209), six of six jobs passed |

Raw Actions artifacts are working evidence with configured 14-day retention.
The durable records preserve exact identities, counts, classifications,
measurements, exclusions, and reproduction inputs without checking target data
or potentially sensitive terminal screens into source control.
