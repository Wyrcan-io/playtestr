# Runner readiness continuation checkpoint v148

## Count and project status

The audited total remains **17/30 admitted projects**. Pick is unadmitted. Its native builds, upstream tests, rc.7 installation and cleanup pass, but its twenty-case native matrix is incomplete.

## Pick v9 result

Workflow run `43324386136` ran the frozen v9 suite on Ubuntu 24.04 and macOS 15 using the exact rc.7 archives. Each host completed 18 scenarios, then failed E11 and did not attempt E12. The E11 action sent End successfully, but `item29` never appeared; both retained screens show only `item00` through `item06`. Both reports record assertion timeout, confirmed target cleanup and cleaned workspaces. The provider artifact ZIPs and every completed report hash are in the host receipts `pick/development-attempt-run43324386136-linux-v1.json` and `pick/development-attempt-run43324386136-darwin-v1.json`. Both provider artifacts have been retrieved and hash-checked.

The v10 long-list oracle now observes four PageDown viewport transitions (`item21`, then `item28`) and uses ArrowDown to reach and select `item29`. The v9 failure remains immutable. The runner fix sends ArrowUp/Down/Left/Right using SS3 when the parsed terminal state has application-cursor mode enabled; other keys keep their existing encodings. A real-PTY regression verifies ArrowUp reaches the target as `ESC O A` after the target enables that mode.

## Local verification

- Focused cursor-mode tests pass on native Windows.
- `go test ./...` passes with native temporary-directory access.
- `go vet ./...` passes.
- The project-local Windows race script passes `go test -race -count=1 ./...`.
- The two documented demo specs pass on Windows after building the demo under `examples/bin`, where their relative command path resolves.
- Pick scenario/cleanup contract tests pass (19 tests; three host-specific skips).

The sandboxed Go runs initially failed because Windows workspace path expansion and the default Go module cache returned access denied. The successful full tests and race run used the authorized native filesystem access. The scratch artifact downloads and extraction stay under `.runner-readiness-compaction-tmp` and are not campaign evidence paths.

## Next actions

1. Review and commit the arrow-key runner fix, regression, rc.8 private-candidate qualification workflow and v10 scenario contract changes; push only to the authorized `work/p0-p2-implementation` branch.
2. Verify the three-host rc.8 source, test, vet, race and archive results; retrieve and independently audit each provider packet before freezing v3.
3. Run Pick v10 against those exact native archives. Keep the 17/30 count unchanged unless all remaining admission gates and independent audit pass.

No publication, PR, issue, discussion, outreach, paid runner or release action is in scope.
