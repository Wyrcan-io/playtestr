# Sprint 11 corpus checkpoint

Status: **A0/A1 complete on 20 September 2026 and Sprint 11-B complete on 24
September 2026.** Sprint 11-B implements all 120 admitted workflows, closes the
300 focused risk cells, and records one detected known-bad plus recovery for all
15 projects. This is discovery/depth evidence, not R6 frozen-byte qualification
or broad cross-platform application compatibility.

The machine-checked artifacts are:

- [`manifest.json`](manifest.json): 15 frozen projects, exact source/package or
  binary identities, install/lock/state/resource/limit/disposal contracts and
  explicit host status.
- [`risk-map.json`](risk-map.json): 300 distinct risk/layer cells with exact test
  anchors. The contract verifies every referenced file/test anchor exists.
- [`boundary-map.json`](boundary-map.json): two reviewed rejection,
  cancellation, or meaningful-boundary workflows for every project.
- [`results/`](results): 15 machine-checked result records with exact target and
  fixture hashes, commands, viewports, independent postconditions, costs,
  cleanup, exclusions, known-bad detection, and recovery.
- [`pilots/records.json`](pilots/records.json): the five pilot commands, manual
  routes, independently specified results, separate runner/campaign outcomes,
  negatives, recovery and cleanup.
- [`../scripts/corpus/generate-risk-map.go`](../scripts/corpus/generate-risk-map.go):
  deterministic generator for the reviewed allocation. `go test ./...` checks
  the 15/120/300 cardinalities, exact identities, host cells and pilot record.

## Sprint 11-B outcome

The completed depth checkpoint is recorded in
[`docs/validation/sprint-11-b-corpus-depth-2026-09-24.md`](../docs/validation/sprint-11-b-corpus-depth-2026-09-24.md).
The machine-checked denominators are 15 projects, 120 distinct workflow specs,
300 reviewed focused risk cells, 15 intended known-bad detections with 15
passing recoveries, and 30 reviewed rejection/cancellation/boundary workflows.

Thirteen application suites ran as native Windows amd64 targets. TIG and
taskwarrior-tui ran as pinned Linux amd64 targets under WSL on a Windows amd64
runner and are explicitly not native-Windows or native-Linux-host claims. Linux
and macOS application suites remain unrun; only the portable focused tests have
three-host native evidence. Those exclusions carry into candidate freeze and
qualification rather than being converted into green support cells.

## A0 outcome

| ID | Representative behavior | Discovery result | Warm offline setup | Measured target runtime |
| --- | --- | --- | ---: | ---: |
| `GUM-01` | choose second item | Current Windows: 3/3 pass; wrong selection failed at the intended snapshot; restored spec passed | 242 ms | median 292 ms, max 299 ms |
| `LG-01` | stage one exact file | Candidate Windows and WSL samples each 10/10; index-lock screen pass was rejected by Git oracle; recovery passed | 795 ms | Windows median 918 ms for the retained 10-run sample |
| `CV-01` | validate prompt/scaffold | Windows 3/3 and historical WSL 3/3; missing template failed; recovery passed | 3,265 ms | median 450 ms, max 466 ms |
| `BT-06` | resize/redraw | Windows 3/3 and historical WSL 3/3; missing helper failed; recovery passed | 435 ms | median 2,479 ms, max 2,499 ms |
| `LG-08` | fresh workspace/session | current Windows adapter-backed 3/3 with pre-deletion oracle and cleanup; the historical persisted commit draft produced a screen pass but wrong Git result; clearing it recovered | 466 ms | median 995 ms, max 1,368 ms (includes workspace/oracle) |

The exact Gum discovery command is:

```powershell
go build -o bin/playtestr-stage11.exe ./cmd/playtestr
1..3 | ForEach-Object {
  ./bin/playtestr-stage11.exe test --report ".trial-private/stage11-gum-$_.json" examples/external-gum.json
}
./bin/playtestr-stage11.exe test --report .trial-private/stage11-gum-negative.json corpus/pilots/gum-01-negative.json
./bin/playtestr-stage11.exe test --report .trial-private/stage11-gum-recovery.json examples/external-gum.json
```

The deliberate-negative command must exit 1 with `snapshot_mismatch`; that is a
successful campaign detection, not a passing runner report. Its reviewed diff is
`Beta -> Alpha`. The other exact commands and target-owned oracle order are in
`pilots/records.json`; private machine paths are represented by named parameters
instead of being published.

Setup acquisition and run time remain separate. The setup column is a measured
Windows warm/offline preparation from retained verified inputs: copy/hash or
archive extraction, fixture/config creation, and (for create-vite) a private-cache
tarball install. It ranges from 242 to 3,265 ms and is not a network download or
source-build benchmark. The promoted September campaign did not instrument
hands-on acquisition time, and this is retained as a gap rather than back-filled
from filesystem timestamps. Measured run medians give a first serial floor: using
the slowest measured pilot median (2.479 s), 3,000 executions are about 124
aggregate minutes. If every attempt also paid the slowest observed warm setup,
the deliberately conservative arithmetic scenario is about 287 minutes before
artifact handling and contingency. The qualification budget therefore remains
60-minute bounded jobs, with sharding chosen after native cold-setup measurements.

`LG-08` closes the required pre-deletion lifecycle directly. The checked-in
[`fresh-workspace-adapter`](../scripts/corpus/fresh-workspace-adapter/main.go)
requires a clean copied index, unchanged required file and file-empty managed
home before it launches real Lazygit on inherited PTY streams. After target exit
it rechecks the index/file and emits `PLAYTESTR_FRESH_ORACLE=passed`; the spec
asserts that marker before successful v2 cleanup deletes the workspace. `LG-01`
separately reads the staged path/bytes before its harness resets the repository.

## Historical A1 admission and gaps (20 September 2026)

The 120 IDs in the catalog are frozen as eight intents for each manifest prefix.
An intent is admitted to the design corpus, not marked implemented. The exact
expected result remains the third column of the catalog and the application pin,
starting-state, resource and disposal rules come from the manifest.

Focused allocation and inventory:

| Family | Total | Reviewed existing | Visible gap |
| --- | ---: | ---: | ---: |
| Spec/schema/CLI validation | 55 | 11 | 44 |
| Process/input/lifecycle | 60 | 24 | 36 |
| Render/readiness/resize | 60 | 24 | 36 |
| Snapshots/suites | 40 | 16 | 24 |
| Workspace/environment/filesystem | 45 | 16 | 29 |
| Reports/install/artifact handling | 40 | 8 | 32 |
| **Total** | **300** | **99** | **201** |

Every gap remains `planned_gap`; unsupported or unrun host cells are never green.
The present roster has more than five plausible applications per advertised host,
but only Windows has real native application evidence in these pilot records.
WSL is historical WSL, and macOS real applications are unrun. Final qualification
still requires five actually verified applications per native host and three
shared applications across all three.

## Historical A1 blockers and next decisions

1. **Native breadth:** macOS has no real-app cell and Linux evidence here is WSL.
   Sprint 13's native jobs must run at least five admitted apps per host and three
   shared apps before broad support can be claimed.
2. **Cold setup cost:** retained trials measured target execution but not active
   acquisition/build time. Instrument cache-cold and cache-warm setup separately
   in the first native lane before choosing shards or paid capacity.
3. **New-candidate route validation:** fzf, micro, tig and taskwarrior-tui are
   exactly source-pinned but not executed. Tig's Windows native build is explicitly
   blocked; replace it for that host or document a supported build before depth.
4. **Focused gaps:** 201 risk/layer cells remain for Sprint 11-B/13, led by native
   process/render boundaries. They are prioritized ahead of adding projects.
5. **Authoring friction:** no two pilots are blocked by the same missing input or
   focused-assertion feature. Sprint 12-B is therefore deferred; recipes and
   diagnostics proceed without widening the spec.

Sprint 10 receives `BT-06` as redraw evidence: the selected sequence passes, so
there is no current pilot-backed reason for a broad emulator rewrite. Sprint 6's
CI-local evaluation case is `GUM-01` wrong-selection -> snapshot mismatch -> same
baseline recovery; it is deterministic, local and requires no service. These are
entry decisions, not completion claims for those later checkpoints.
