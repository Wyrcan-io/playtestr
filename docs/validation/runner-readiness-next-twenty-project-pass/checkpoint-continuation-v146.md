# Runner readiness continuation checkpoint v146

## Count

The current audited count remains **17/30 admitted distinct projects** (ten first batch, six rc.6 new projects, and JOE on exact rc.7). Pick has not completed an admission and remains at zero credit. The scope continues sequentially through all required project and candidate gates.

## Pick progress

Canonical target: `mptre/pick`, commit `caae95938359b2e814b3e7406f396f486c9d99fb`, MIT; source archive SHA-256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`. Linux and macOS native builds/upstream tests and exact rc.7 installation pass. Prior failed attempts v1-v7 are retained in immutable receipts; none contributes admission credit.

- v4 run `43320083737`: Linux failed N02's ambiguous down-selection screen oracle; macOS E04 was rejected as invalid before launch. Mac source cleanup correctly refused deletion because the cleanup invocation lacked an explicit invalid-spec report digest. Both exact receipts and provider artifacts are recorded.
- v6 run `43322068022`: Linux/macOS each passed 14 cases then failed E07. Exact pinned source preserves CR when splitting CRLF choices, so the visible row is `eta`, not `beta`. Both hosts independently reproduced it. All target cleanup, exact source restoration and storage checks passed; five scenarios per host were not attempted. v6 receipts preserve exact report and artifact hashes.
- v7 run `43323052844`: both hosts passed 15 reports including E07 with the source-proven CR behavior, then failed E08 because immediate Ctrl+C was sent before positive target readiness; Pick exited 130 instead of graceful cancel status 1. Process cleanup, exact source restoration and storage checks passed. Four scenarios per host were not attempted. v7 receipts preserve all reports. No complete 20-case development matrix exists yet.
- Immutable v8 is locally materialized: E08 types and observes `none` before Ctrl+C, then asserts exact exit 1. This positive input checkpoint avoids treating startup timing as application cancellation behavior. It has not been launched.

Local contract/cleanup unit suite: 18 tests, 15 passed and 3 host-specific skips. Python bytecode compilation and `git diff --check` pass.

## Next actions

1. Commit/push v6 Darwin and v7 receipts plus v8 contract/checkpoint on `work/p0-p2-implementation`; monitor and independently inspect v8 Linux/macOS artifacts.
2. Continue with new immutable contracts only after attempts launch. Complete the full 20-case development set on both hosts before final qualification.
3. Run 12x final ordinary qualification per host, all three safe source faults and required calibration phases, authoring/maintenance/Unicode/delivered-CI routes, late transfer/current-candidate checks, controls, storage/process cleanup and independent admission audit.
4. Resume the exact canonical project ledger and continue until thirty complete admissions. Keep **17/30** until Pick or a later complete project audit closes every gate.

No releases, PRs, issues, discussions, outreach or paid runners are authorized.
