# Sprint 13-C bounded comparison — 22 September 2026

Status: complete for the admitted Linux amd64 comparison. This is operator
engineering evidence, not independent onboarding, general defect-detection
coverage, or the 3,000-execution release qualification campaign.

## Frozen inputs and execution

The successful comparison used Playtestr commit
`f1ab948f13937bed9c67d8e27da4eb5e26ed67cc` on GitHub's Ubuntu 24.04 amd64
runner (`Linux 6.17.0-1022-azure`, Go 1.26.0). Alternatives were Atago
v0.23.0, Microsoft tui-test 0.1.0-beta.5, and Termlens 0.11.2 with Rust
1.85.0 and the committed Cargo lock. Checksums for every runner and target are
in the retained `versions.txt` artifact.

The exact successful workflow is [Competitive tasks run 35750618644](https://github.com/Wyrcan-io/playtestr/actions/runs/35750618644).
Its `competitive-c1-linux-amd64` artifact contains tool/version identities,
checksums, install timings, all control and attempt ledgers, per-attempt logs,
resource measurements, independent state oracles, and adversarial PID records.

Commands were:

```text
bash scripts/competitive/install-c1-tools.sh
bash scripts/competitive/run-c1-campaign.sh
bash scripts/competitive/run-c23-campaign.sh
bash scripts/competitive/run-adversarial.sh
```

Cold tool setup, including download/build where applicable, was 7,504 ms for
Playtestr, 419 ms for Atago, 310 ms for tui-test, and 7,492 ms for Termlens.
Target acquisition did not use a network: all four good/bad fixture pairs were
built afterward from the same checkout. The harness did not time those target
builds separately, so it is not folded into or presented as tool installation.

Each measured attempt used `/usr/bin/time -v` around the normal user-facing
tool invocation. It includes target startup, runner/library overhead and normal
artifact/log work. The deterministic tasks contain condition waits but no
intentional fixed sleep. The tools do not expose comparable internal phase
timings, so startup, runner overhead, and artifact time are not falsely
decomposed. Log bytes are retained separately. This limits causal performance
claims but preserves a fair launch-to-result comparison.

## Correctness controls

C1 selects `Beta` while the reviewed mutation visibly moves to `Beta` but
commits `Alpha`. C2 corrects an invalid port and independently requires the
fresh config to contain exactly `port=4242`; its mutation prints success while
writing the old `port=8080`. C3 opens a modal, resizes from 60x12 to 80x20,
dismisses it and requires the main screen; its mutation leaves stale modal
state. All tools used the same target binary, starting state, viewport, input,
budgets, and expected outcome for a task.

- 36/36 good, reviewed-known-bad and recovered controls passed.
- 360/360 counterbalanced fresh executions passed: 30 executions for every
  tool/task cell.
- Every known-bad control failed for its intended mutation, and every recovery
  returned to the good binary and expected result.
- C2's external file oracle was mandatory. During harness development a
  Playtestr screen-only test falsely passed the bad target; the retained finding
  is why a visible success message never counts as state proof.
- Termlens uses Cargo's status 101 for a failed test, rather than status 1.
  The final harness correctly admits any nonzero intended known-bad result.
- tui-test's direct `run` interface does not expose the target exit status to
  `expect exit-code`; its visible `/bin/sh` adapter emits and asserts
  `TARGET_EXIT:<code>`. That glue remains part of its authored surface.

Retained first-run failures were not deleted: run 35744015924 recorded the
incorrect `ArrowDown` token as literal input; run 35744744793 recorded the
tui-test direct-run exit-code mismatch; run 35745038582 recorded the erroneous
assumption that every known-bad tool exits 1; and run 35746801063 recorded the
missing C3 Atago target export. These are harness/operator corrections, not
product wins.

## Fresh-run measurements

Values are milliseconds and KiB. Medians and ranges describe only these 30
exploratory samples; they are not tail percentiles or universal rankings.

| Task | Tool | Runtime min / median / max | Peak RSS median / max | Log bytes median / max |
| --- | --- | ---: | ---: | ---: |
| C1 | Atago | 48 / 49 / 51 | 30,038 / 32,888 | 71 / 71 |
| C1 | Playtestr | 285 / 295 / 300 | 10,680 / 10,732 | 439 / 439 |
| C1 | Termlens | 49 / 49 / 50 | 27,714 / 27,920 | 303 / 303 |
| C1 | tui-test | 137 / 137 / 139 | 8,888 / 9,008 | 116 / 116 |
| C2 | Atago | 49 / 51 / 53 | 30,840 / 35,288 | 71 / 71 |
| C2 | Playtestr | 295 / 296 / 297 | 10,650 / 10,848 | 490 / 490 |
| C2 | Termlens | 49 / 50 / 52 | 27,674 / 27,900 | 308 / 308 |
| C2 | tui-test | 142 / 143 / 145 | 8,900 / 9,104 | 121 / 121 |
| C3 | Atago | 104 / 106 / 107 | 32,986 / 40,180 | 71 / 71 |
| C3 | Playtestr | 295 / 305 / 306 | 10,702 / 12,800 | 521 / 521 |
| C3 | Termlens | 54 / 54 / 56 | 27,738 / 27,932 | 307 / 307 |
| C3 | tui-test | 148 / 150 / 151 | 8,964 / 9,020 | 121 / 121 |

Playtestr was consistently slower than the other three on these short warm
tasks. Its peak RSS was below Atago and Termlens and above tui-test in these
measurements. No single tool won every measured cost, and the standalone CLI,
session CLI, declarative runner, and Rust library have materially different
integration models.

For the three task definitions, excluding shared targets and campaign harness,
Playtestr used three JSON files / 62 lines, Atago three YAML files / 73 lines,
and Termlens one manifest plus one Rust test file / 140 lines (plus a
341-line generated lockfile). tui-test required command sequences in the two
shared shell adapters, including its exit shim and explicit session cleanup;
because those adapters also contain shared setup/oracles, no misleading
tool-only line count is assigned.

## Adversarial results and unsupported commonality

All 12 admitted hang, cancellation, and finite-flood cells passed their
declared contracts and the external PID oracle found no survivor:

| Tool | Hang | Cancellation | Output flood |
| --- | --- | --- | --- |
| Playtestr | `run_timeout`, 510 ms | runner cancellation / structured `cancelled`, 60 ms | `output_limit`, 15 ms |
| Atago | bounded assertion timeout, 510 ms | managed-service signal and wait, 29 ms | finite 4 MiB drain, 1,525 ms |
| tui-test | timeout then explicit session kill, 621 ms | target signal, 122 ms | finite 4 MiB drain, 219 ms |
| Termlens | bounded wait then owned-process drop, 592 ms | target signal, 42 ms | finite 4 MiB drain, 10,022 ms |

Only Playtestr exposed a documented configurable raw-output limit in this
exercise. Atago, tui-test and Termlens were therefore tested with a finite
4 MiB producer and labeled `finite-drain-no-documented-limit`; they were not
scored as failures for lacking Playtestr's contract. The same rule applies to
cancellation: Playtestr's runner cancellation is not mislabeled as equivalent
to the alternatives' target/service signal operations.

The current-source native lifecycle gate separately covers blocked PTY input,
runner cancellation, output caps, natural/forced descendant cleanup and the
documented escape boundaries on Windows amd64, Linux amd64 and macOS arm64.
The new `TestSecretCanaryPersistenceBoundary` at commit
`b7b952556ce31395bcf4c312641628e77c693e5b` proves that non-rendered environment
and typed canaries do not enter structured results, runner logs, or screen
artifacts. It also proves the required limitation: target-rendered canaries are
preserved in screen evidence. Playtestr does not claim automatic redaction;
trusted targets and test authors must not render secrets.

Existing focused tests, rerun without the Go cache at that commit, cover hostile
HTML/terminal text, missing/per-file/aggregate/generated-size evidence limits,
traversal and absolute/remote/network references, escaping symlinks/junctions,
working-directory aliases, hard/shared evidence, cancelled staged snapshot
updates, stale run references, report/artifact write failures, applicable
permission failures, and atomic preservation of earlier output. The manual
package-in-a-spaced-path rehearsal remains Sprint 13-D after Sprint 11-B; these
checks do not freeze candidate bytes.

## Local and remote verification

On Windows amd64, commit `b7b9525` passed:

- `go test -count=1 ./...`
- `go vet ./...`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1`
- `go build -o bin/demo.exe ./cmd/demo`
- `go run ./cmd/playtestr test examples/menu.json examples/menu-exit.json`
  with 2/2 specs and 12/12 steps passing.

The same exact commit completed all triggered remote gates successfully:

- [Native gap checks 35752035704](https://github.com/Wyrcan-io/playtestr/actions/runs/35752035704):
  Windows amd64, Linux amd64 and macOS arm64 all passed their inspected
  15-command integrated hardening inventory with no missing or unexpected
  skips.
- [Terminal tests 35752035722](https://github.com/Wyrcan-io/playtestr/actions/runs/35752035722):
  passed.
- [Competitive tasks 35752035647](https://github.com/Wyrcan-io/playtestr/actions/runs/35752035647):
  passed again after the canary-only regression change.

No release, tag, action revision, workflow dispatch, or external message was
created. The next roadmap checkpoint is Sprint 11-B corpus depth; Sprint 13-D
then performs the development-archive rehearsal and prepares the R6-F freeze.
