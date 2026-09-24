# Sprint 11-B corpus depth evidence — 24 September 2026

## Conclusion

Sprint 11-B is complete at the admitted depth boundary: 15 pinned projects, 120
distinct implemented workflows, 300 reviewed focused risk cells, 15 intended
known-bad detections with passing recoveries, and two reviewed rejection,
cancellation, or meaningful-boundary workflows for each project. No target was
silently removed and no workflow count is inflated by host or viewport aliases.

This is not candidate qualification. Thirteen suites exercised native Windows
amd64 targets. TIG 2.6.1 and taskwarrior-tui 0.27.0 exercised pinned Linux amd64
targets under WSL from the Windows runner; those two records are neither native
Windows support nor a native Linux-host run. macOS application workflows and
native Linux-host application workflows remain excluded.

## Exact inventory and measured discovery runs

Every linked result has schema version 1, exact executable/package identity,
fixture manifest hash, runner commit, command, viewport, screen expectation,
independent postcondition, per-step/run/output bounds, setup cost, workflow
duration, cleanup result, control outcome, recovery, and exclusions.

| Project | Exact version | Host scope | Warm offline setup | Eight-workflow time | Known-bad category | Result |
| --- | --- | --- | ---: | ---: | --- | --- |
| GUM | v0.17.0 | Windows amd64 native | 222 ms | 2,689 ms | `snapshot_mismatch` | [`gum-windows-amd64.json`](../../corpus/results/gum-windows-amd64.json) |
| LG | 0.65.0 | Windows amd64 native | 44 ms | 14,461 ms | `unexpected_exit` | [`lazygit-windows-amd64.json`](../../corpus/results/lazygit-windows-amd64.json) |
| FZF | v0.74.4 | Windows amd64 native | 60,432 ms | 4,225 ms | `snapshot_mismatch` | [`fzf-windows-amd64.json`](../../corpus/results/fzf-windows-amd64.json) |
| POST | 2.10.0 | Windows amd64 native | 107 ms | 31,482 ms | `assertion_timeout` | [`posting-windows-amd64.json`](../../corpus/results/posting-windows-amd64.json) |
| LITE | 1.17.1 | Windows amd64 native | 26 ms | 11,255 ms | `assertion_timeout` | [`litecli-windows-amd64.json`](../../corpus/results/litecli-windows-amd64.json) |
| MITM | 12.2.3 | Windows amd64 native | 21 ms | 72,565 ms | `assertion_timeout` | [`mitmproxy-windows-amd64.json`](../../corpus/results/mitmproxy-windows-amd64.json) |
| BT | 0.14.9 | Windows amd64 native | 15 ms | 5,772 ms | `assertion_timeout` | [`bottom-windows-amd64.json`](../../corpus/results/bottom-windows-amd64.json) |
| GUI | 0.28.1 | Windows amd64 native | 32 ms | 10,323 ms | `unexpected_exit` | [`gitui-windows-amd64.json`](../../corpus/results/gitui-windows-amd64.json) |
| TV | 0.15.9 | Windows amd64 native | 125 ms | 5,654 ms | `snapshot_mismatch` | [`television-windows-amd64.json`](../../corpus/results/television-windows-amd64.json) |
| NPK | 0.12.2 | Windows amd64 native | 15 ms | 18,687 ms | `assertion_timeout` | [`npkill-windows-amd64.json`](../../corpus/results/npkill-windows-amd64.json) |
| CV | 9.2.1 | Windows amd64 native | 22 ms | 3,707 ms | `unexpected_exit` | [`create-vite-windows-amd64.json`](../../corpus/results/create-vite-windows-amd64.json) |
| IPM | 1.3.3 | Windows amd64 native | 23 ms | 5,339 ms | `unexpected_exit` | [`ipm-windows-amd64.json`](../../corpus/results/ipm-windows-amd64.json) |
| MICRO | v2.0.14 | Windows amd64 native | 21,129 ms | 4,510 ms | `unexpected_exit` | [`micro-windows-amd64.json`](../../corpus/results/micro-windows-amd64.json) |
| TIG | 2.6.1 | Linux amd64 target under WSL | 293 ms | 23,698 ms | `assertion_timeout` | [`tig-windows-amd64.json`](../../corpus/results/tig-windows-amd64.json) |
| TASK | 0.27.0 | Linux amd64 target under WSL | 124 ms | 133,922 ms | `assertion_timeout` | [`taskwarrior-tui-windows-amd64.json`](../../corpus/results/taskwarrior-tui-windows-amd64.json) |

The recorded warm/offline setup total is 82,630 ms, dominated by source builds
for FZF and Micro. The recorded final eight-workflow runs total 348,289 ms; the
slowest single workflow is TASK-07 at 33,115 ms. These are discovery measurements
on one machine, not comparative performance claims. Checked-in corpus metadata
occupied 384,243 bytes before this evidence document; ignored raw reports,
executables, source trees, and transient screens are not claimed as durable data.

## Sensitivity, recovery, and independent state

Each result record points to the exact reviewed bad spec and recovery spec. All
15 bad runs returned runner status 1 for the recorded intended category; all 15
recoveries returned 0. The controls include source-level behavior mutations for
stateful targets, reviewed fixture/selection sensitivity where labeled, and
external oracles that reject a green-looking screen when Git, files, SQLite,
Taskwarrior data, HTTP protocol state, or process state is wrong.

TIG's mutation removes the Enter binding from the pinned source/build and fails
when the diff never opens. Taskwarrior's mutation changes the completion key
from `d` to `D` and fails at the missing completion prompt. Both were cleanly
rebuilt; their unmodified recoveries passed. Workspace results confirm target
exit, workspace cleanup, and unchanged original fixtures.

[`boundary-map.json`](../../corpus/boundary-map.json) names exactly two distinct
boundary workflows per project (30 total) and explains the rejection,
cancellation, empty-state, resize, or lifecycle boundary each exercises.

## Focused risk cases

[`risk-map.json`](../../corpus/risk-map.json) contains 60 independently described
risks across five boundaries: pure contract, runner integration, Windows amd64,
Linux amd64, and macOS arm64. This yields 300 stable case IDs. Each cell now
references an exact test function (or the reviewed continuous-repaint workflow),
and the corpus contract rejects missing files and stale test anchors.

The native layers reuse portable focused behavior only when that exact test ran
on the named native host. Sprint 13-A1, 13-B, and 13-C provide the prior
three-host hardening/setup and adversarial executions; the checkpoint CI reruns
the full current suite on Windows, Linux, and macOS. Application support is not
inferred from those portable risk tests.

The audit added explicit null-command rejection and found a validation defect:
only the first command element was checked for emptiness. The runner now rejects
every empty command element before launch, with a regression that proves the
target was not started and no typed secret was persisted.

The final full-suite run also exposed a Windows-only setup-test harness defect:
PowerShell can duplicate the executable path in the copied fixture's argument
vector. The old exact argument-count guard missed that form and recursively ran
the test suite. Fixture detection now requires the private marker plus a final
`--version`, has a regression for the duplicated-path form, and the affected
installer test completes in 2.88 seconds without retained fixture processes.

## Commands and outcome policy

Representative depth execution uses the result record's exact command, for
example:

```powershell
go run ./cmd/playtestr test --report .trial-private/corpus-task-stable2.json `
  corpus/workflows/taskwarrior-tui/task-01.json `
  corpus/workflows/taskwarrior-tui/task-02.json `
  corpus/workflows/taskwarrior-tui/task-03.json `
  corpus/workflows/taskwarrior-tui/task-04.json `
  corpus/workflows/taskwarrior-tui/task-05.json `
  corpus/workflows/taskwarrior-tui/task-06.json `
  corpus/workflows/taskwarrior-tui/task-07.json `
  corpus/workflows/taskwarrior-tui/task-08.json
```

The final Taskwarrior suite passed 8/8 twice. Its mutation control failed with
`assertion_timeout` at step 3, and the unmodified recovery passed 9/9. TIG passed
8/8 twice; its mutation failed at the intended missing diff assertion and its
recovery passed. The same pass/fail/recovery rule is encoded in every result.

## Explicit remaining work

- No 3,000-execution sample has run. It starts only after candidate bytes are
  frozen and belongs to Sprint 11-C/R6-Q.
- Linux and macOS real-application depth is not established by this checkpoint.
  Candidate freeze must define the support boundary before qualification.
- Warm retained-input verification is not cold acquisition timing. R6 lanes
  must measure cold setup separately.
- No release, tag, action revision, marketplace revision, workflow dispatch, or
  maintainer outreach occurred.

The next checkpoint is Sprint 13-D plus R6-F candidate freeze.
