# Sprint 9 engineering validation — 2026-09-19

This record covers local Windows engineering acceptance for repeatable workspaces. It does not claim independent maintainer adoption or Linux/macOS runtime evidence. Outside feedback and maintainer adoption are deferred until after Sprint 10 by product decision.

## Entry case and frozen contract

The selected real stateful case is Lazygit v0.65.0 on Windows amd64. Trial observation R3-T09 recorded a commit draft persisting across launches: one terminal sequence passed while the Git oracle remained at the baseline, and the next attempt submitted duplicated persisted input. The corrected trial recipe cleared the input, but the incident demonstrated that both project files and application home state can contaminate a repeated interactive flow.

Spec v2 therefore requires a fixture below the spec directory. It copies only that reviewed directory, selects `workspace.cwd` inside the copy, and can map a runner-owned temporary home and temp directory. Executables resolve from the spec directory or `PATH` before the cwd change. Managed environment names conflict rather than silently overriding `env` or `inherit_env`. Spec/report v1 remain unchanged; workspace and mixed suites use report v2.

The frozen limits are 2,000 filesystem entries, 1,000 regular files, 32 MiB total, 8 MiB per file, depth 32, a 30-second setup ceiling within `run_timeout_ms`, and a separate five-second cleanup allowance. Fixture links, Windows junctions/reparse points, special files, escaping paths, case collisions on case-insensitive hosts, and detected file changes fail setup.

## Real application repetition

The ignored local spec `.trial-private/sprint9-lazygit-workspace.json` used the checksum-pinned trial Lazygit v0.65.0 binary, copied the 38-file/38,477-byte Git repository fixture, selected managed home/temp paths, waited for `alpha.txt`, and exited with Ctrl+C. It did not use the original Lazygit config directory.

Command: `bin/playtestr-sprint9.exe test .trial-private/sprint9-lazygit-workspace.json`, repeated ten times without retry.

Result: 10/10 passed. Every attempt prepared a separate root, observed the expected repository, exited zero, and removed its workspace. Recursive SHA-256 manifests of the original repository were identical before and after. The SHA-256 of `.trial-private/config/windows/lazygit/state.yml` was also unchanged. These checks cover the named fixture and known trial config only; they do not prove filesystem isolation.

The public deterministic state-writing example also passed with report v2:

```text
go build -o bin/fixture.exe ./cmd/fixture
go build -o bin/playtestr-sprint9.exe ./cmd/playtestr
bin/playtestr-sprint9.exe test --report .trial-private/sprint9-example-report.json examples/workspace.json
```

The target created state in its copied cwd, managed home, and managed temp. The reviewed `examples/workspace-fixture/seed.txt` remained unchanged and no state file appeared beside it.

## Failure and lifecycle coverage

Focused native tests cover two fresh executions, ordinary failure cleanup, explicit failure retention, setup failure without launch, missing and oversized fixtures, mid-copy cancellation, executable resolution, expected nonzero exit, output flood, assertion timeout, runner cancellation, parent/child termination, target-created junction handling, locked-file cleanup failure and retention, ownership-marker tampering, and snapshot rollback after cleanup failure. Windows junction creation and locked-file tests ran natively; symlink creation requiring unavailable Windows privilege was skipped, with the equivalent cleanup no-follow test present for Unix.

Report/CLI tests prove report v2 selection, workspace serialization, retained-path output, semantic rejection, and offline HTML rendering. Schema tests prove distinct frozen v1/v2 contracts and workspace categories. A v1-only suite still selects report v1.

The deliberately broken assertion and cancellation tests are bounded expected failures, not flaky successful attempts. Together with the ten real Lazygit passes, the acceptance campaign contains 12 explicitly classified attempts: 10 passed real-app repetitions, one expected assertion failure with cleanup, and one expected cancellation with confirmed process exit and cleanup.

## Limits and handoff

- A workspace is repeatable local setup for trusted programs, not a sandbox.
- Retained paths can contain target data and are never uploaded automatically.
- Unconfirmed process exit retains the directory rather than deleting under a possibly live target.
- Linux and macOS mappings are implemented and covered by build-tagged/unit behavior, but native Sprint 9 runs on those hosts remain open.
- Independent adoption and feedback remain open until after Sprint 10.

## Final local checks

- `go test -count=1 ./...`: passed.
- `go vet ./...`: passed.
- `scripts/test-race.ps1`: passed with the project-local Windows race compiler. An initial run exposed a test-only 100 ms exit deadline; increasing only that success-path test deadline to 3 seconds made the instrumented run pass without changing product deadlines.
- `scripts/site.ps1 build`: passed; 25 HTML pages and all four canonical schemas were validated.
- Built-binary walkthrough: both existing menu specs passed, the workspace example passed and emitted report v2, and `playtestr report` rendered that report to self-contained HTML.
