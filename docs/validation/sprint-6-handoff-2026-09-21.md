# Sprint 6 ordinary failure-handoff decision

Date: 2026-09-21. Decision: **ordinary instructions are sufficient; defer the
reproduction-manifest branch**. The experiment used source revision
`c5d9894fa4587bc4d043a91013b38b9b305ec481` on Windows amd64 in a newly prepared
repository-owned directory. This is operator engineering evidence, not
independent adoption or a cross-host claim.

## Frozen handoff inputs

| Input | Identity |
| --- | --- |
| Runner built from the named revision | SHA-256 `CC17892A5D58D868835BE5DD846A4B523ADECF2668FEBC3567A056CBA3E21B35` |
| Gum v0.17.0 Windows amd64 | SHA-256 `0327F1C91A9E75D831FA4C62174BC4EDC183FD8106109271E7CF74F77BC83BC9` |
| Broken spec `examples/recipes/selector-wrong.json` | SHA-256 `CD6DF2FA6684F13EBE847F126FCE7EA85401CC1FFC18C6417D1C58DD7229C1C9` |
| Corrected spec `examples/recipes/selector.json` | SHA-256 `ACDA6672C56BDAB14CD204E503B1F8433081622199C77ADB88A2392A2B99B878` |
| Baseline `examples/recipes/snapshots/selector.txt` | SHA-256 `977FE4F3DA44D8D29129D1135C219221A22A721B6C89862AF2178DA577EF9B4A` |

The spec supplies the `60x12` viewport, 15-second step budget, 30-second run
budget and 500,000-byte output cap. The only prerequisite is the reviewed Gum
binary at `.tools/external/gum.exe`; the target writes no persistent state and
requires no secret or inherited application data.

## Experiment

The handoff directory contained only the runner, target, two specs, baseline and
empty artifact root at their documented relative paths. From that directory:

```powershell
.\bin\playtestr.exe test -report artifacts\failure.json -artifacts-dir artifacts\evidence examples\recipes\selector-wrong.json
.\bin\playtestr.exe report -input artifacts\failure.json -evidence-root . -output artifacts\failure.html
.\bin\playtestr.exe test -report artifacts\recovery.json -artifacts-dir artifacts\evidence examples\recipes\selector.json
```

The first command exited 1 in 968 ms. Its report identified
`snapshot_mismatch`, snapshot step 4, target exit 0, confirmed Job Object
cleanup, and fresh screen/diff paths. The reviewed diff was exactly `Beta` to
`Alpha`. The existing offline renderer produced a 7,476-byte self-contained
report without launching the target. The corrected spec then passed 5/5 in 327
ms with the same target and baseline.

A second clean handoff directory deliberately omitted Gum. The corrected spec
exited 1 in 1,034 ms with `launch_failure` and console context that
`./.tools/external/gum` was not found. This was not mistaken for the snapshot
failure. The original baseline and evidence remained unchanged; every run used
a unique artifact directory.

## Decision

All necessary facts were recoverable from a short reviewed recipe plus the
existing spec, report, screen and diff. No context omission remained, repeated
or otherwise. A new manifest would duplicate strict spec/report data while
adding format, privacy, path, old-reader and maintenance costs. The optional
6.2–6.6 branch is therefore not entered; proposed `--repro` and `reproduce`
commands remain explicitly nonexistent.

Reopen only after a repeated real CI-to-local case cannot be classified using
the [ordinary handoff](../ci-failure-handoff.md), and the missing safe fact
cannot reasonably be added to that recipe. Unknown databases, services,
scheduling, secrets and application state remain limitations, not permission to
capture environments or source bundles. Independent comprehension and timing
belong to adoption A1.

The next roadmap checkpoint is Sprint 13-B/C integrated hardening and bounded
comparison.
