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

The v5 source-development checkpoint supersedes the earlier pending statements:
the Linux runner/VT package checks, race checks, and exact twenty-case source
matrix passed. Three genuine source faults are now predeclared in
[`fault-declaration-v1.json`](fault-declaration-v1.json), and the hosted workflow
will test their baseline, corrupted, and restored/rebuilt phases on Ubuntu and
Windows. These fault phases and the v5 scenario matrix remain development
evidence until independently audited and rerun on the exact final candidate.
The public recorder/maintenance/relocation journey and all final qualification
gates remain open.

The first exact RC6 final-series workflow, run `41953084178`, installed the
frozen candidate and built the pinned target on both native hosts. The final
command was refused before target tests because its 3,300-second wrapper budget
exceeded the campaign helper's 1,200-second maximum. This is a harness
configuration failure with zero candidate executions; the dependent report-based
cleanup proof also could not run. Both first-attempt packets are retained and
audited in [`final-series-attempts-v1.json`](final-series-attempts-v1.json).
Declaration v2 fixes the wrapper bound while preserving v1 and all failed
attempts. Git Town remains unadmitted until the fresh exact-candidate series,
fault recovery, independent audit and checked cleanup pass.

The next run (`41954388734`) reached the final harness verification on both
hosts, then refused before candidate execution because raw source hashes varied
with Linux LF and Windows CRLF checkouts. Its complete packets and exact
failure dispositions are in [`final-series-attempts-v2.json`](final-series-attempts-v2.json).
Declaration v3 hashes normalized text harness bytes and binds the corrected
cross-platform policy. Both first attempts remain preserved and receive zero
candidate credit.

The third attempt (`41955366681`) passed the corrected timeout gate, then found
that v3 hashes were generated from a modified local `readiness_evidence.py` that
was not present in the pushed commit. Both hosts rejected that mismatch before
candidate tests; their artifacts and dispositions are in
[`final-series-attempts-v3.json`](final-series-attempts-v3.json). Declaration v4
derives normalized text hashes from staged Git blobs so it binds the exact
commit contents while ignoring checkout-only CRLF conversion.

The fourth exact-candidate attempt (`41956408435`) passed the declaration gate
and reached target scenarios. Linux's first cold case exceeded the implicit
3-second checkpoint before emitting screen bytes; Windows passed twelve cases
before the Unicode creation case failed its exact `.git/HEAD` state check.
Both host packets and the two failure dispositions are retained in
[`final-series-attempts-v4.json`](final-series-attempts-v4.json). The jobs also
found that the pinned source archive was missing from the checkout-based cleanup
path, so source/runtime removal was not verified. V5 froze a 10-second N01
checkpoint and a separate Unicode switcher case with a host-generated fixture.
The fifth attempt (`41960284415`) stopped during source preparation on both
hosts because downloaded codeload bytes differed from the historical archive
digest. No build or candidate test started; both packets are retained in
[`final-series-attempts-v5.json`](final-series-attempts-v5.json). V6 generates
a deterministic archive from the verified pinned checkout and verifies every
member against the source manifest before continuing. All attempts remain
zero-credit until complete native execution, independent audit, and checked
cleanup pass.

The sixth final attempt (`41962045773`) built the pinned source, generated and
verified the deterministic archive on both hosts, and installed the candidate,
but the final journal refused before launching any case because its generic
`scenarios.json` input alias was absent. The archive, source, runtime, and
candidate evidence are retained in [`final-series-attempts-v6.json`](final-series-attempts-v6.json).
The separate source-development dispatch (`41962045862`) also stopped before
target launch because its historical v3 catalog still expected the earlier
N01 bytes. V7 materializes and hashes the alias from the frozen v2 case list,
binds final fault calibration to a new declaration for catalog v4. The stale
source-development push trigger is disabled until its historical v3 contracts
are re-versioned; manual dispatch remains available but is not evidence of a
pass. No v6 candidate or cleanup credit is awarded.

The seventh final attempt (`41964820652`) verified the archive, installed RC6,
and launched 15 cases: 13 passed and two failed. Linux N02 exceeded the implicit
3-second readiness timeout; Windows N15 showed the Unicode branch but selected
the default row because the case omitted `Down`. All 13 Windows workspaces were
cleaned and Linux source/runtime deletion was verified. Windows source/runtime
removal stopped because the isolated PowerShell environment did not expose
`Get-FileHash`. The complete host packets and inventories are preserved in
[`final-series-attempts-v7.json`](final-series-attempts-v7.json). The separate
three-host readiness harness run (`41964820676`) passed helper checks on Ubuntu,
Windows and macOS; it does not count as final-series evidence. V8 raises N02's
bounded timeout to 10 seconds, selects the visible Unicode row, and calculates
SHA-256 in process during cleanup. The cumulative final-attempt count is 29
target cases (25 passed, 4 failed); no batch, calibration, or admission credit
has been earned.

The eighth exact-candidate attempt (`41967210773`) passed N02 on both hosts
and retained its v8 failure artifacts. Linux passed N01 and N02, then N03 hit
the implicit 3-second readiness limit. Windows passed fourteen launched cases,
but N15 was rejected before launch because `Down` is not a supported key name;
the contract needs `ArrowDown`. Linux checked source/runtime removal. Windows
cleanup correctly refused to delete the owned source after the invalid-spec
report lacked positive cleanup evidence. The provider packets and extracted
inventories are in [`final-series-attempts-v8.json`](final-series-attempts-v8.json).
Across v4, v7 and v8, 46 target cases were launched: 41 passed and five failed.
No complete batch, calibration or candidate admission credit is earned. V9
freezes the 10-second N03 checkpoint and supported N15 key name.

The ninth exact-candidate attempt (`41968702601`) confirmed those corrections:
Windows passed 80 cases across four complete batches, including N04 and Unicode
selection. Linux passed N01-N03, then N04 timed out at its implicit 3-second
readiness bound. Windows stopped before batch 5 because the general viewport
transform assumed explicit `width` and `height`; v3 defaults these omitted
fields to 80 by 24. Both hosts restored and removed the owned source/runtime.
Packets and inventories are preserved in
[`final-series-attempts-v9.json`](final-series-attempts-v9.json). The run adds
84 launched cases (83 pass, one fail); no ordinary or calibration qualification
credit is earned. V10 sets the bounded 10-second step deadline for all frozen
scenarios and makes the viewport transform honor v3 defaults.


Tenth exact-candidate attempt (`41970500610`): Windows completed all 12 batches (240/240 ordinary passes), all nine source-fault phases (three baselines, three detections, three restored recoveries), process proof, source restoration, checked removal, and artifact upload. Linux completed nine full batches (180 passes) and 11 more cases in batch 9 before N14 was cancelled after 3.65 seconds; total 191 passes and one cancelled launch. Both packets and inventories are retained in [`final-series-attempts-v10.json`](final-series-attempts-v10.json). The run adds 432 launches, 431 passing outcomes, and one cancellation. Windows-only execution and fault observations earn zero cell/calibration/admission credit because the complete two-host cell did not finish. V11 widens every case to a 20-second step bound and 60-second process bound; independent audit remains required.

V11 declaration note: the first immutable v11 declaration was superseded before dispatch because its revision-summary labels were inconsistent and its generator bytes changed during correction; no target ran under that declaration. V12 binds corrected labels and final staged harness hashes to the same v8 scenarios, then reruns the complete two-host series.


Eleventh hosted attempt `41974745060` refused before launching any Git Town test cases: the journal preflight still referenced scenario alias v5 after the freeze advanced to v6. Both artifacts are preserved with full inventories in [`final-series-attempts-v11.json`](final-series-attempts-v11.json). Candidate case counters do not change. Windows process proof found no target process, but both cleanup jobs refused source/runtime deletion because no case-report cleanup proof existed; ephemeral runner teardown followed. V13 shares and tests the scenario-alias validator, and a fresh complete run must re-establish cleanup evidence.


Twelfth exact-candidate attempt (`41975837578`): Windows completed 240/240 cases, all nine source-fault phases, and checked cleanup. Linux passed 195 cases; the outer `next20_check.py` deadline fired at exactly 1,200 seconds during N18 in batch 9, cancelling one target case. Its workspace/process cleanup and the host source/runtime removal passed. Both packets and inventory hashes are preserved in [`final-series-attempts-v12.json`](final-series-attempts-v12.json). The run adds 436 target launches (435 pass, one cancelled) and zero candidate credit. V14 raises the bounded outer series deadline to 2,400 seconds and binds the workflow file.


Fourteenth hosted workflow `41978773971` refused before target launch on both platforms: the workflow requested 2,400 seconds, but `next20_check.py` still capped its parser at 1,200. Cleanup refused source/runtime deletion without target reports; the runner VMs were ephemeral and ended with their jobs, but no checked removal is claimed. Both packets and inventories are in [`final-series-attempts-v13.json`](final-series-attempts-v13.json). Case totals and qualification credit do not change. V15 raises the adapter's checked maximum to 2,400 seconds and adds numeric-boundary tests.


Fifteenth hosted attempt `41980469906` (`v15`): Windows completed 240 ordinary cases, all nine source-fault phases, process-tree proof, source restoration, and checked removal. Linux completed batches 0-10 (220 passes), then its first batch-11 N01 attempt failed at the declared 2,000 ms startup boundary before any action step; the target exited 130 and process/workspace/source cleanup passed. No retry or qualification credit is counted. Both complete packets and canonical inventories are retained in [`final-series-attempts-v14.json`](final-series-attempts-v14.json). The exact N01 report records `assertion_timeout` waiting for first output at startup. V16 will preserve this result and adjust only Linux batch-11 startup to a bounded 5,000 ms, leaving the Windows 2,000 ms boundary and ordinary test deadlines unchanged.


Seventeenth hosted workflow `41984301547` (`v16`) repeated the same effective Linux N01 failure: Windows completed 240 ordinary cases, nine fault phases and checked cleanup; Linux completed 220 cases then timed out on N01 at 2,000 ms. The packet?s generated N01 contract confirms 2,000 ms, although the v16 declaration specified 5,000 ms for Linux. Root cause: the top-level Git Town wrapper checked v16, while the shared batch runner read the legacy v1 startup profile. Preserve both packets and the exact report in [`final-series-attempts-v16.json`](final-series-attempts-v16.json); no retry or qualification credit. A duplicate queued dispatch `41984332161` was cancelled before any jobs started and is separately recorded in [`final-series-attempts-v15.json`](final-series-attempts-v15.json). V17 threads the explicit per-host startup profile to the batch runner and adds an override regression test.
