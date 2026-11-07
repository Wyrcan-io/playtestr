# Skim resume checkpoint

Current status (5 November 2026): the exact rc.6 Windows runner archive is installed and hash-verified. The pinned Skim Windows target build was recovered from GitHub Actions artifact 13324780409 (run 41831060729), with the provider ZIP digest checked before its redundant ZIP was removed. Two local exact-candidate N01 preflights stopped before target launch because Windows GetLongPathName returned Access Denied under the OneDrive checkout path; they receive zero scenario and cleanup credit and are preserved in [candidate smoke attempts](candidate-native-smoke-attempts-v1.json). The standard hosted Windows runner is the required path for exact-candidate qualification. Skim remains unadmitted and all candidate counters remain zero.

Next work: freeze the twelve-batch candidate profile and case variants, run the exact archive on native hosted Linux and Windows, perform candidate-phase fault calibrations, complete first-use/maintenance/relocation/CI journeys, independently audit, then clean the staged local target. Do not count source-development runs as candidate qualification.

Earlier checkpoint follows as historical record; its project-9 next-step note is superseded by the current status above.

As of 4 November 2026, Skim project 8?s corrected source-development matrix and
three development source faults passed on native Linux and Windows twice. The
first corrected run was `41827379783` (commit `47d5ff9bdaabadbf98539a8dce81ecb33fed3012`);
the source-matched repeat was `41831060729` (commit
`19e689f1d3721743146a11647fcb152048becd5d`). Each run passed 20/20 cases on
both hosts with all 40 workspaces cleaned. Windows detected all three real
source mutations and independently matched all 28 inner archive members. The
repeat receipts and per-case hashes are in
[hosted-source-repeat-41831060729.json](hosted-source-repeat-41831060729.json).

The exact 819-file pinned source tree was verified restored and the local
source/runtime root was removed through the checked native Windows cleanup. The
21,954-file inventory, 112 cleanup-confirmed reports, seven explicitly
unlaunched/invalid-spec reports with zero cleanup credit, process proof and
removal receipts are summarized in
[cleanup-readback-v1.json](cleanup-readback-v1.json). Five separate Skim fault/evidence roots (2,166 files) remain byte-identical under
`artifacts/runner-readiness-next-twenty-project-pass/skim/retained-active-evidence/`;
the campaign `active/` directory is clear for the next project.

Skim remains unadmitted: private candidate archive repeats/calibrations, public
first-use and authoring, maintenance/diagnosis, relocation, delivered CI, and
final qualification are open. Known risks WIN-NAV-01 (directional navigation)
and OUTPUT-NUL-01 (exact NUL framing) remain open. Do not increment project or
current-candidate counters.

Next selected project is Git Town (project 9). Its pinned source/license/build
hook review is prepared in `../git-town/source-review-v1.json`; acquire and
verify the pin, then review the full materialized tree before any build or
execution. Keep late-transfer projects `ne`, `sc-im`, `btop`, and `htop`
unexposed until provisional candidate freeze.


5 November continuation: installed and byte-verified the exact rc.6 Windows runner archive. Recovered Skim?s pinned Windows target binary and build receipt from hosted source-development artifact 13324780409 (run 41831060729), verified the provider ZIP digest and target/source pin, and removed the redundant ZIP after extracting only those two files. Two local exact-candidate preflights failed before any target launch: Windows GetLongPathName returned Access Denied for the OneDrive workspace root; reports have zero scenario/cleanup credit in [candidate smoke attempts](candidate-native-smoke-attempts-v1.json). Use the standard hosted Windows runner, which already passed this source matrix, for exact-candidate cases. The retained target workspace is temporary pending hosted final-series execution and checked cleanup.

## 8 November 2026 continuation

Skim remains unadmitted and exact-candidate execution remains at zero. The final source-fault harness now requires the declared failure category for each of its three mutations (E02 unexpected exit; N01/N04 assertion timeout); baseline and restored controls still require full positive pass evidence. The previous Windows prelaunch plan is preserved and superseded because its declaration binding predates this stricter check. A second preparation attempt stopped before contract publication when it found an existing v1 contract root; its two hash-verified copies and zero-launch status are recorded in `final-series-preflight-supersession-v2.json`.

Fresh Windows plan generation v3 is prepared and independently reconstructed: 240/240 contracts verified, zero target launches. Planner tests pass 5/5, all declared harness SHA-256 bindings match, Python compilation and workflow YAML parsing pass. Storage observation is within limits: new raw 1,414,101,415 bytes; combined raw 3,322,809,987; combined retained 2,130,330,615; Skim project 49,835,465 bytes. Hosted Linux and Windows exact-rc.6 runs, 480 ordinary executions total and 18 fault phases, remain unstarted. The source-development matrix remains separate evidence and gives no candidate admission credit.

Next: finish review of the final workflow, commit and push the prepared scoped campaign state on `work/p0-p2-implementation`, monitor native runs and audit the complete artifacts. Then finish Skim's public first-use, authoring, maintenance, diagnosis, relocation, delivered-CI and cleanup gates before admitting it or advancing to the next selected project. Preserve the original ten requalification, all remaining projects, old migrations, final storage/accounting and independent closure gates.

## 8 November 2026 hosted prelaunch and corrected retry checkpoint

Run 42422136311 failed on both hosts before target source acquisition. Its exact workflow artifact ZIPs were retrieved and their SHA-256 digests independently match provider digests: Linux `4238ff8a631cd65f98243a56ed0aacb63715b27d400249bdf17256c9bc16961f`; Windows `6c8d1d1cbd204dbde51a342df6e440860367fb254f9b42d154a16568a9331dde`. Immutable helper events show both bounded acquisition wrapper processes were reaped, with no cleanup errors; no Skim source or candidate target was acquired, no target application/candidate case launched, and no qualification credit was earned. See [candidate-native-attempts-v1.json](candidate-native-attempts-v1.json).

The cause was workflow order: cache directories were placed under `active/skim` before `next20_acquire.py`, which correctly refuses a nonempty active root. The workflow now acquires and verifies the pinned source first. Cleanup now runs for every attempted acquisition and a checked no-case mode permits cleanup after acquisition/build failure only when the case-evidence tree is absent or empty; a new regression test rejects started or partial case evidence. Nine local planner/cleanup tests pass (the symlink test is skipped on Windows because that host disallows creating the test symlink).

The v5 plan was independently audited but remains zero-launch and is superseded after the cleanup gate changed. Fresh Windows plan v6 independently reconstructs all 240 exact contracts with zero target launches. All final-series harness SHA-256 bindings match. Latest storage observation: new raw 1,465,869,111 bytes; combined raw 3,374,577,683; combined retained 2,132,083,079; Skim project 51,214,697 bytes; no cap failures. Candidate status and project admission remain zero.

Next: push the corrected workflow and run Linux/Windows exact rc.6 acquisition, build, plan audit, 240 cases and nine fault phases per host. Preserve every failure, then complete Skim public authoring, maintenance, relocation, delivered-CI, cleanup and independent audit gates.

Latest follow-up: the corrected Skim and Git Town workflow changes are ready for another hosted run. Local combined controls pass 23 tests (one symlink capability skip). The exact-candidate attempt is not yet credited; the corrected workflows must complete on both native hosts and pass independent evidence audit.
