# Sprint 5 engineering validation — 15 September 2026

Status: engineering acceptance complete locally, from a fresh public clone, and in native CI on Linux amd64, macOS arm64, and Windows amd64. Independent participant-owned CI acceptance remains open; no participant or JUnit results consumer was supplied or recorded.

## Acceptance project and frozen choices

The repository's two-spec mission-control example is the bounded operator acceptance project. Before Sprint 5 it required two explicit paths and failure evidence was written beside source specs. Its frozen directory selection is, in order:

```text
examples/suite/menu-exit.json
examples/suite/menu.json
```

The project needs recursive directory selection, not custom globs or filters. Its CI consumes report v1 plus uploaded files and has no configured JUnit results viewer, so JUnit is deliberately omitted. Limits are 10,000 visited entries, 1,000 selected specs, and 10,000 aggregate valid steps. The complete path and exclusion contract is in [Test suites and CI evidence](../suites.md).

## Local results

The following checks passed on Windows amd64:

```powershell
go test ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
go build -o bin/demo.exe ./cmd/demo
go build -o bin/playtestr.exe ./cmd/playtestr
.\bin\playtestr.exe test --list examples\suite
.\bin\playtestr.exe test --artifacts-dir artifacts\playtestr --report artifacts\suite-results.json examples\suite
```

The list contained exactly the two frozen paths on repeated resolution. The real-PTY suite passed 2/2 serially and its report summary was `total=2 passed=2 failed=0 cancelled=0 not_run=0`.

A separate seeded `snapshot_mismatch` exited 1, named step 4 and category `snapshot_mismatch`, and wrote independently addressable screen and diff files beneath one unique run directory. Running the green directory afterward passed 2/2 in a second run directory; its report contained no stale screen or diff reference. Unit and real-PTY tests additionally cover ordinary continue-after-failure, exact expected nonzero exit, cancellation with `cancelled`/`not_run`, duplicate basenames, hard-file deduplication, symlink non-traversal, case behavior, Windows separators, zero matches, missing roots, output aliases, shared update baselines, all suite limits, and evidence-write failure separation.

The workflow file now lists and runs the directory suite, places deliberate-failure evidence under the explicit artifact root, and uploads only that explicit root and reports. GitHub Actions run [34983854289](https://github.com/Wyrcan-io/playtestr/actions/runs/34983854289) for commit `4b12547443fd93605f5daa9aea1c2a06f8461224` completed successfully on Ubuntu, Windows, and macOS; each matrix job passed the suite, deliberate regression, and artifact upload. The artifact retention is 14 days.

The final documentation commit was independently exercised by Terminal tests run [34984166487](https://github.com/Wyrcan-io/playtestr/actions/runs/34984166487) and Website run [34984166381](https://github.com/Wyrcan-io/playtestr/actions/runs/34984166381); both passed. All three native Terminal-test artifacts were downloaded and audited. Each contained a 2/2 passing suite report, a 4/4 explicit-file report, and a deliberate `snapshot_mismatch` at step 4 with resolvable screen and diff references. The screen SHA-256 and diff SHA-256 matched across Linux, macOS, and Windows, and no unrelated file types were present.

A fresh public clone of commit `20ce06281de7af46b3ccbeda7dbda106eb185b7b` also passed `go test ./...`, native binary builds, the exact two-path list, the 2/2 directory suite, a seeded exit-1 snapshot mismatch with isolated evidence, and a subsequent 2/2 recovery whose report contained no stale evidence reference. This clean-clone exercise used only repository instructions and generated state outside the source checkout.

The native release workflow now gates future archives on the same deterministic list, 2/2 suite run, isolated deliberate-failure evidence, legacy adjacent evidence, cancellation, checksum, archive layout, version, and packaged-binary checks. The prepared [Sprint 5 suite adopter walkthrough](../trials/sprint-5-suite-adopter.md) keeps independent evidence explicitly separate from these operator checks.

## Remaining external acceptance

No independent maintainer walkthrough or participant-owned CI integration is available in the repository. Per checkpoint 5.6, engineering completion is recorded without substituting operator work for adoption. The adopter review, released-binary rerun, observed diagnosis friction, and CI consumer validation remain open until a consenting project supplies them.

The current stable `v0.1.0` predates Sprint 5. The next release decision should therefore be a suite-capable `v0.2.0-rc.1` from the verified main branch, followed by the adopter walkthrough above. Sprint 7 remains the recommended engineering candidate when diagnosis friction is the observed problem; Sprint 6 remains conditional on missing reproduction context. Publication of a new tag/release still requires explicit authorization and successful native-release evidence for that exact tag.
