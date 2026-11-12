# Runner readiness continuation checkpoint v147

## Campaign count

The current audited total remains **17/30 admitted distinct projects**: ten first-batch projects, six new rc.6 projects, and JOE on exact rc.7. Pick remains unadmitted. Partial native scenarios, target builds or upstream tests do not change the count.

## Pick native progress

Pick is pinned to `mptre/pick` commit `caae95938359b2e814b3e7406f396f486c9d99fb`, MIT, archive SHA-256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`. Both Linux and macOS native builds, upstream tests, exact rc.7 installation and source cleanup have passed in the latest completed attempts.

- v4 run `43320083737`: preserved Linux N02 selection-oracle failure and macOS E04 prelaunch invalid-spec failure/cleanup refusal; zero credit.
- v6 run `43322068022`: 14/15 passed on both hosts; E07 exposed pinned Pick's retained CR behavior for CRLF input. Five cases per host not attempted. Cleanup/storage passed; receipts retained.
- v7 run `43323052844`: 15/16 passed on both hosts, including the CRLF source boundary. E08 immediate Ctrl+C raced app readiness and produced exit 130. Four cases per host not attempted. Cleanup/storage passed; receipts retained.
- v8 run `43323672213`: 18/19 passed on both hosts, including E08 after query readiness. E11 timed out trying End navigation without a preceding positive interactive checkpoint; saved screen showed item00-item06. One case per host not attempted. Cleanup/storage passed; receipts retained.
- v9 now inserts `expect item00` after the query and before End, while requiring item29 in the scrolled screen and selected output. v9 is locally frozen and awaits native Linux/macOS launch.

All earlier failures remain immutable. There is no complete 20-case development matrix and no project admission credit for Pick.

Local unit suite: 18 tests, 15 passed and 3 host-specific skips; Python bytecode compilation and whitespace/diff checks pass.

## Next actions

1. Commit/push v8 receipts, v9 scenarios and checkpoint on `work/p0-p2-implementation`; monitor and audit both native artifacts.
2. Complete all twenty scenarios on both hosts. Iterate immutable contracts only after launch and preserve all first failures.
3. Run 12x final ordinary matrix per host, three distinct safe target faults and mandatory calibration phases, public authoring/maintenance/Unicode/delivered-CI routes, current-candidate and original-project transfer checks, required controls, process/storage cleanup and independent admission audit.
4. Continue the candidate ledger through the complete 30 admissions. Maintain **17/30** until a full independent audit closes a new project.

No release, pull request, issue, discussion, outreach or paid-runner action is authorized.
