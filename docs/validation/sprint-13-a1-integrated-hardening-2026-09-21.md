# Sprint 13-A1 integrated hardening evidence — 21 September 2026

Status: complete on Windows amd64, Linux amd64, and macOS arm64 at commit
`1a098bd32f1a0e819d6ccb8e1731ed7656f80f56`. The successful
[`Native gap checks` run `35571028383`](https://github.com/Wyrcan-io/playtestr/actions/runs/35571028383)
uploaded all three `integrated-hardening-*` artifacts. The matching
[`Terminal tests` run `35571028547`](https://github.com/Wyrcan-io/playtestr/actions/runs/35571028547)
and [`Website` run `35571028376`](https://github.com/Wyrcan-io/playtestr/actions/runs/35571028376)
also passed.

## Boundary

The checkpoint adds `scripts/test-integrated-hardening.ps1`, which records one
machine-readable row per command in `commands.json` and host provenance in
`environment.json`. Every row contains the source commit and dirty state,
native OS/architecture and description, Go and PowerShell toolchains, exact
command, expected result and exit, observed result and exit, elapsed time,
artifact location, and remaining limitation. A missing C compiler produces
`blocked_missing_c_compiler`; it is never recorded as a race pass.

The native workflow now runs, on each mapped host:

- uncached repository tests and vet;
- the race detector when a native C compiler is available;
- the enforced installer, workspace, report, lifecycle, cancellation, flood,
  descendant-cleanup, link/junction, and cleanup-failure test inventory;
- a current-source build;
- a real-PTY mixed spec-v1/spec-v2 suite and report-v2 HTML export;
- an intentional snapshot failure with retained evidence and HTML export; and
- a corrected recovery run.

The focused inventory retains distinct checks for workspace setup and cleanup,
target outcomes, artifact-write failures, report validation, v1/v2 rendering,
prior-state freshness, cancellation, output bounds, and platform-native
no-follow behavior. No public schema or runner behavior changed in this slice.

## Local Windows result

The pre-commit checkout was based on
`cbd18747aa0f4f55fe194b8c2346ea3da251d4d0` with only this checkpoint patch
dirty. Windows build `10.0.26200`, amd64, Go `1.27.0`, Windows PowerShell `5.1`,
and the project-local GCC completed the following. Generated evidence is
ignored under `artifacts/sprint13-a1-local/`.

| Command group | Expected | Observed | Exit | Artifact | Remaining limitation |
| --- | --- | --- | ---: | --- | --- |
| `go test -count=1 ./...` | all packages pass uncached | passed in 32.6 s | 0 | `full-tests.log` | Dirty pre-commit source; final identity comes from CI |
| `go vet ./...` | no vet findings | passed | 0 | `vet.log` | Same |
| `go test -race -count=1 ./...` | all packages pass under race detector | passed in 58.5 s | 0 | `race.log` | Windows-only local evidence |
| enforced focused native inventory | every required event passes; only reviewed platform skip permitted | 39 top-level tests passed; local unprivileged symlink subtest remained the recorded Windows skip while junction checks passed | 0 | `focused-native-gaps.log`, `focused/summary.json` | Final hosted Windows privilege result comes from CI |
| current-source build | native runner builds | passed | 0 | `build-runner.log` | Development version, not frozen candidate bytes |
| mixed v1/v2 real-PTY run | both specs pass; v2 workspace prepared and cleaned | passed | 0 | `mixed-v1-v2.json` | Source rehearsal, not release qualification |
| mixed report HTML | renderer accepts the generated v2 document | passed | 0 | `mixed-v1-v2.html` | Browser presentation remains separately bounded |
| deliberate snapshot mismatch | intended failure is retained | detected `snapshot_mismatch` | 1 | `deliberate-failure.json` | Expected nonzero runner result |
| deliberate-failure HTML | retained v1 evidence renders offline | passed | 0 | `deliberate-failure.html` | None |
| recovery | corrected spec passes after failure | passed | 0 | `recovery.json` | None |

The rehearsal uses the documented relative artifact layout. Absolute evidence
references remain rejected by the offline renderer as specified; the runner's
existing report-v1 path semantics were not changed merely to simplify the
campaign harness.

## Native completion gate

After this checkpoint commit is pushed, the required run must finish with three
successful jobs and uploaded artifacts named:

- `integrated-hardening-windows-amd64`;
- `integrated-hardening-linux-amd64`; and
- `integrated-hardening-darwin-arm64`.

The final handoff records the exact run URL and commit. Any failed or absent
job, missing artifact, unexpected test skip, or `blocked_missing_c_compiler`
row keeps the affected claim open. This source checkpoint does not freeze or
publish runner bytes.

The first exact-commit attempt, run `35570373489` at `9bc6d18`, failed on all
three hosts because the new manual rehearsal did not build `bin/demo` and
`bin/fixture` in a clean checkout. Its intended-negative command also accepted
any exit status 1 without proving `snapshot_mismatch`, so the launch failure
could have been misclassified as successful campaign detection. The failed
artifacts are retained. The repair builds both native targets and adds positive
machine checks for mixed-contract identity, workspace preparation/cleanup, the
exact negative category and evidence, and recovery without stale references.

The final artifacts record clean source, Go `1.25.0`, and 15 passing command
rows on every host. Linux ran Ubuntu `24.04.5` amd64 with `/usr/bin/cc`; macOS
ran `15.7.9` arm64 with `/usr/bin/cc`; Windows ran build `10.0.26100` amd64 with
`C:\mingw64\bin\gcc.exe`. Every host completed the race row as `passed`, not
blocked, and every focused group reported zero unexpected skips and zero
missing required tests.
