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

The hosted v1 matrix is preserved in `hosted-development-attempts-v1.json`. Native
Windows passed all twenty v1 cases twice, with 40 cleaned workspaces and exact
4,533-file source verification. Six Linux v1 jobs attempted all 120 scenarios;
all timed out before visible screen text, and their reports confirm process cleanup.
A separate bounded Linux PTY probe of the same binary emitted 195 bytes containing
the expected branch result, while Playtestr's rendered screen stayed blank. The
Linux mismatch remains open. Windows checkout initially converted source line
endings; restoration now reads raw blobs from the pinned Git archive and verifies
them against provenance before build.

Catalog v2 preserves all v1 specs and attempts. It declares the isolated Git,
pager, and terminal environment explicitly because the public runner's default
allowlist omits those values. Hosted run `41875535290` verified and built the
source on both hosts. Linux again failed all 20 screen assertions with a blank
rendered screen, despite a bounded raw PTY probe emitting the expected 195 bytes.
Windows passed all 20 exact catalog-v3 cases. The earlier v2 Windows 19/20
result came from a hosted N15 spec blob with U+FFFD instead of U+00E9; the
direct target probe and exact v3 bytes confirm the pinned app handles the
intended branch name. See hosted-development-attempts-v2-correction.json.
Hosted v3 run `41879628387` passed the exact-spec hash gate and all 20
Windows scenarios. Linux again failed 20/20 first-screen assertions with a
blank screen and confirmed process cleanup, despite a direct native PTY probe
capturing 195 expected output bytes and exit 0. Exact attempts and artifacts
are in [`hosted-development-attempts-v3.json`](hosted-development-attempts-v3.json).
The Linux launch mismatch remains open. A bounded follow-up probe compares
PTY startup with and without a controlling terminal before runner changes.
repetitions, three safe source faults, calibration, public recorder/maintenance
work, current-candidate qualification and cleanup audit remain open. Git Town
has no admission, native-cell, fault-detection or candidate credit.

Catalog v3 retains the intended v2 scenario hashes and adds an exact-byte
prelaunch verifier. See [`scenario-catalog-v3.json`](scenario-catalog-v3.json),
[`hosted-development-attempts-v2-correction.json`](hosted-development-attempts-v2-correction.json),
and [`next20_git_town_catalog.py`](../../../../scripts/acceptance/next20_git_town_catalog.py).
The Linux diagnostic workflow also runs the bounded
[`next20_git_town_controlling_tty_probe.py`](../../../../scripts/acceptance/next20_git_town_controlling_tty_probe.py)
and retains its owned evidence directory.


The controlling-terminal diagnostic on run `41881662967` narrowed the Linux
startup wait to the first `OSC 11;?` and `CSI 6 n` exchanges: the raw PTY launch
without a controlling terminal exited 0 with 195 expected output bytes, while
the controlling-TTY launch timed out after 12 query bytes and confirmed process
group cleanup. Playtestr's emulator already creates color and cursor replies,
but its Unix bridge discarded them. A bounded source fix and mixed-query real
PTY regression are prepared; the next hosted workflow runs ordinary and race
checks before retrying the frozen cases. Until that run is read back, Git Town
remains development-only with zero admission or native-cell credit.


Hosted follow-up run `41897622026` verified the exact catalog and built the source
on Ubuntu and Windows. Windows passed all 20 cases. Linux stopped before any
scenario: the expanded real-PTY regression exposed a stale transport-error test
injection that checked only a batch prefix while mixed replies now share one
write. The first run remains preserved with artifacts in
[`hosted-development-attempts-v4.json`](hosted-development-attempts-v4.json).
The injection now detects the DA bytes anywhere in a combined batch; Linux
ordinary/race checks and the 20-case rerun are pending. No admission or native
cell credit.

The corrected run `41898559438` passed the runner/VT package suites on Ubuntu
both ordinarily and with `-race`, then passed all 20 exact v3 cases on both
Ubuntu 24.04 and Windows 2025. Each logged case completed with runner exit 0;
the direct PTY diagnostic exited with 195 expected bytes and the controlling-TTY
diagnostic retained the 12-byte startup query while confirming process-group
cleanup. Artifacts, per-case report hashes, and the v4 failure are preserved in
[`hosted-development-attempts-v5.json`](hosted-development-attempts-v5.json).
This closes Git Town source-development only. Qualification, fault detection,
public authoring/maintenance, relocation, exact-candidate repetition and cleanup
audit remain open; no admission or native-cell credit is added.


The v5 source-development checkpoint supersedes the earlier pending statements: the Linux runner/VT package checks, race checks, and exact twenty-case source matrix passed. Three genuine source faults are predeclared in [fault-declaration-v1.json](fault-declaration-v1.json); the hosted workflow runs baseline, corrupted, and restored/rebuilt phases on Ubuntu and Windows. Those results and the v5 matrix remain development evidence until independently audited and rerun on the exact final candidate. The public authoring, maintenance, relocation, and final qualification gates remain open.
