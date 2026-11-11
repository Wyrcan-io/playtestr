# Runner readiness continuation checkpoint v139

Campaign remains **16/30 cumulative admissions** and **6/20 new-project admissions**. No candidate, fault or project-admission credit was added in this continuation.

## Source fix and local validation

- Commit `df7fd54375e411542ce899c0e05b19db643ba64b` fixes bare target-command lookup to use the test's effective target `PATH` and target working directory. It adds Windows `PATHEXT` handling and regression coverage for conflicting runner/target executable paths.
- Native Windows checks passed: `go test ./...` (runner 158.6 s), `go vet ./...`, and `scripts/test-race.ps1` (runner 329.9 s). JOE-focused Python tests (4), three v2 declaration preflights, workflow YAML parsing, Python compilation, campaign JSON parsing and `git diff --check` passed. Local `actionlint` is unavailable.
- Commit `df7fd54375e411542ce899c0e05b19db643ba64b` was pushed to the authorized branch. The automatic JOE v2 source-fault workflow `43054584381` is queued; additional exact candidate/scenario workflows for this commit are running. Their results are not counted until artifacts are retrieved and audited.

## Candidate v2 predeclaration

- The separate `native-exit-v2` / `v0.4.0-rc.7` private candidate is predeclared in `replacement-candidate-declaration-native-exit-v2.json` (SHA-256 `81fa347ef97b0c90526699e7a68f72a95c5e1d601db99aaf720c0a374c97227a`). It pins production source commit `df7fd54375e411542ce899c0e05b19db643ba64b`, and declares native Linux amd64, macOS arm64 and Windows amd64 source/test/vet/race/package checks.
- The candidate workflow's source pin is updated locally to that full source SHA. The workflow plus declaration still need the follow-up commit/push to trigger it. No archive has been built or audited yet.
- The v2 JOE calibration workflow currently references exact rc.6 artifacts; even a successful run is not transferable to rc.7 admission without repeated exact-candidate evidence.

## Next

Commit/push the candidate declaration and workflow pin, then monitor and independently audit all native source/fault artifacts. Freeze rc.7 only after source maps and archives match the declaration. Re-run JOE v2 against exact rc.7, audit baseline/fault/recovery evidence and cleanup on both native hosts, then continue public route, oracle/model and admission gates. Continue the remaining project packages and original-ten/current-candidate, migrations, controls, delivery, fresh checkout, storage, cleanup and final audit gates.
