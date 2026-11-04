# Git Town project package: pinned source and development review

Git Town is selected application 9 (`git-town/git-town`), pinned to
`8d039892574d4852e1843020c31d423234042e78`. The pin is MIT licensed and uses
Go with Bubble Tea. Pinned release and CI files support Linux and Windows.

The 5,504,823-byte archive materialized 4,533 primary Git files (29,389,387
expanded bytes). Every file matches the pinned Git tree; 4 entries are executable
and 4,529 are regular. No archive links were present. The initial extraction
refused an inaccurate link policy while retaining the archive; the corrected
empty-link policy resumed the same bytes. Review
[`source-review-v4.json`](source-review-v4.json),
[`source-audit-v2.json`](source-audit-v2.json), and
[`source-provenance.json`](source-provenance.json) for source, build hooks and
integrity details.

The source uses Go 1.26.9 and vendors 73 modules. A native Windows/amd64 build
passed with local Go 1.27.0 using the pinned `go.work` workspace vendor. The
executable SHA-256 is
`e16a0c20bf8c36ef93e01488f50469ddc793e826d93caf6337a075fe8da2163b`; its
`--version` output is `Git Town 24.1.0`. The reviewed build path is
`go build -mod=vendor -trimpath -o <owned-bin>/git-town.exe .`, with network
module resolution and automatic toolchain downloads disabled. Upstream Makefile
installation/release helpers use `run-that-app` and can fetch tools; those targets
are excluded. The upstream Linux Cucumber workflow installs Spanish language
packages and the Windows workflow uses its smoke target. Campaign runs use direct
Go builds and locally owned synthetic repositories.

Twenty distinct public spec v3 development cases passed once each on native
Windows. They cover branch creation and stacking, parent and hierarchy views,
branch classifications and rename, visual selection/filter/cancel, viewport
resize and redraw, Unicode and slash-qualified branch names, invalid/duplicate
branch refusal, empty selection, offline status and configuration review. Each
case asserts positive terminal or exit evidence and a same-run state result;
the detailed hashes and every earlier failure are in
[`development-readback-v2.json`](development-readback-v2.json). The frozen
declarations are in [`scenario-catalog-v1.json`](scenario-catalog-v1.json).

Two exploratory operations, `observe` and `contribute`, were attempted with the
no-remote fixture and correctly refused because those workflows require a remote
branch. Those attempts remain preserved and are not in the frozen 20-case suite.
Each scenario starts from a synthetic local repository with no external remote;
forge tokens and user Git configuration are excluded. Managed workspaces are not
security sandboxes.

The 20 passes are development evidence only. Final repetitions, hosted Linux and
Windows cells, three safe source faults, calibration, public recorder/maintenance
work, current-candidate qualification and cleanup audit remain open. Git Town has
no admission, native-cell, fault-detection or candidate credit.
