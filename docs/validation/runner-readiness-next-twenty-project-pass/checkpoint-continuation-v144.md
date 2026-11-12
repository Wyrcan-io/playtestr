# Runner readiness continuation checkpoint v144

## Current milestone and count

Campaign goal: thirty rigorously admitted distinct applications. Current audited count is **17/30**: ten original admissions, six next-twenty rc.6 admissions, and JOE on exact rc.7. Pick is still 0 admission credit. No existing project's evidence transfers to rc.7 without the exact-current-candidate gates.

## Pick native attempts

Pick is pinned to `mptre/pick` commit `caae95938359b2e814b3e7406f396f486c9d99fb`, MIT, with source archive SHA-256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`. On both Linux and macOS, native build, upstream tests, candidate archive install and storage checks pass. Linux v4 run `43320083737` passed N01, then failed N02: ArrowDown followed by Enter returned `amber` where the text-only contract expected `blue`. The screen oracle had matched visible `blue` before selection and did not prove cursor movement. macOS attempted 12 reports: N01-N08 and E01-E03 passed, E04 was rejected before target launch because `expect_not` did not repeat an exact earlier `expect`; eight cases were not attempted. All 11 launched macOS targets have confirmed process/workspace cleanup; source/runtime cleanup safely refused because the invalid-spec report digest was not whitelisted. Exact host receipts preserve reports, provider artifact hashes, failure categories and not-attempted counts. The failed run grants no scenario or admission credit.

Immutable v6 now replaces N02 with an initial `-q blue` selection and exact returned-line oracle, while retaining v5's corrected exact E04 prior observation. v6 has not been launched. Local Python contract and cleanup tests: 18 tests, 15 passed and three host-specific skips; bytecode compilation and `git diff --check` pass.

## Next actions

1. Commit/push the scoped v5/v6 contracts, test/generator changes, v3/v4 immutable attempt receipts and this checkpoint on `work/p0-p2-implementation`; standard hosted native runs are already authorized.
2. Audit the v6 development run artifacts independently on Linux and macOS; preserve every first result and diagnose any remaining failure without altering a launched contract.
3. Complete Pick's 20-scenario development, 12x final qualification per host, three real fault calibrations, public authoring/maintenance/Unicode/CI route, old-project transfer checks, all required controls, storage/process cleanup and independent admission audit before counting it.
4. Continue sequentially through the exact candidate ledger; maintain **17/30** until one complete admission is independently closed.

Do not count build-only or partial scenario results as project admissions. No release, PR, issue, discussion, outreach or paid-runner action is authorized.
