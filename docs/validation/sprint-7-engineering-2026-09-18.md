# Sprint 7 engineering validation — 18 September 2026

Status: engineering acceptance and published-release verification complete for
the `v0.3.0-rc.1` prerelease on Linux amd64, macOS arm64, and Windows amd64.
Independent maintainer adoption and outside usability feedback are deliberately
deferred until after Sprint 10 by product decision.

## Frozen presentation and sources

The renderer uses report v1 without changing its schema. Every ordinary-view
fact comes from one of these captured fields:

| Displayed fact | Captured source |
| --- | --- |
| Totals | `summary` after consistency validation against `results` |
| Stable test identity and name | `results[].spec_path` and `name` |
| Status, duration, viewport | matching result fields |
| First failing step/action/category | first `steps[]` entry with `status=failed` |
| Primary category/message | `results[].failure` |
| Terminal and unified diff | admitted `evidence.screen_path` / `diff_path` files |
| Target exit | `target` |
| Cleanup | `cleanup` |
| Evidence-write outcome | `evidence.failures` |

Expected assertion text, typed input, commands, environment, event history, and
root cause are not reconstructed. The timeout view explicitly labels its
expected expression unavailable in report v1. A readable artifact is described
as embedded evidence, not cryptographically verified capture.

Relative references resolve from the report command's working directory and
must remain within the explicit evidence root. Absolute, traversal, URI,
network, symlink, and Windows junction escapes are rejected. Report input,
evidence, and output aliasing are rejected. Screen/diff pairs must retain one
report-v1 artifact prefix, and evidence cannot be assigned to two results.

Limits are 8 MiB report input, 1,000 results, 10,000 aggregate steps, 256 KiB
per evidence file, 24 MiB aggregate evidence, and 32 MiB generated HTML. Reads
and rendering enforce the limits. Output is atomic and an existing file remains
unchanged after admission or write failure.

## Actual diagnosis cases

The checkout-built Windows binary produced and rendered both required cases:

- `examples/snapshot-mismatch.json` exited 1 with `snapshot_mismatch` at step 4,
  a 64×16 screen, unified diff, clean confirmed Windows Job Object cleanup, and
  successful offline HTML export.
- `examples/assertion-timeout.json` exited 1 with `assertion_timeout` at step 2,
  a 60×10 screen, no invented diff or expected expression, forced confirmed
  Windows Job Object cleanup, and successful offline HTML export.

A real mixed invocation of `examples/menu.json`, the snapshot mismatch, and the
timeout reported `total=3 passed=1 failed=2 cancelled=0 not_run=0`. Its HTML put
the two failures before the passing test while retaining original stable
identities and step records.

Unit and CLI tests additionally cover one result, duplicate display names,
cancelled/not-run results, missing screens and diffs, cleanup failures, evidence
write failures, malformed/truncated/unknown-field/wrong-version reports,
inconsistent summaries and artifact pairs, shared paths and hard-linked
evidence, traversal, absolute/remote/network paths, an escaping Windows
junction, input/evidence
output aliases (including a missing referenced path), invalid UTF-8, unusual
Unicode, HTML and OSC text, per-file/aggregate/generated-output limits,
unwritable output, and preservation of prior inputs and output.

## Browser review

The exact generated mixed report and the controlled-regression report were
opened from `file:` in installed Microsoft Edge using the Chrome DevTools
Protocol. Automated inspection at 375×812 and 1440×1000 verified:

- one heading, failure-first navigation, a visible first failing step, and no
  page-level horizontal overflow;
- keyboard focus begins at the skip link and Enter reaches the main report;
- terminal text uses a preformatted monospace pane with internal scrolling;
- added and removed diff rows exist and body/diff contrast is at least 4.5:1;
- the complete diagnosis remains available with JavaScript disabled;
- accessibility-tree links have names; and
- no HTTP(S) request, script, external font, image, or stylesheet is present.

Long lines remain inside their pane. On the narrow viewport, facts, evidence,
and separate outcomes collapse to one column. Hostile HTML remains text and OSC
content does not become a link.

This is operator engineering review, not independent usability evidence. No
outside reviewer, assistance time, or adoption preference is invented. The
prepared workflow and questions remain open for the post-Sprint-10 session.

## Demo and verification

The demo used the unchanged `examples/menu.json` spec and reviewed
`diagnostics.txt` baseline for all three runs. The normal target passed 6/6. A
demo binary built with the explicit linker fixture
`-X=main.diagnosticsSuffix=_REGRESSION` failed at snapshot step 6, and the same
user-facing HTML showed the final screen and focused added suffix. Rebuilding
the normal target restored a 6/6 pass. The bad run evidence remains under the
ignored local `artifacts/sprint7-demo` tree for inspection.

The following checks passed:

```text
go test ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\site.ps1
node scripts/check-site.mjs public
node scripts/report-browser-check.mjs http://127.0.0.1:9223 artifacts/sprint7-demo-bad.html
```

The race run included the runner and report packages and exited 0. Website
validation included the new offline-report documentation route. Go emitted
non-fatal module stat-cache access warnings during local builds; the requested
binaries and all recorded product outcomes completed successfully using the
project-local build cache.

## Published release evidence

The release source is commit `7cf64afc105decfdbbe37141d45ab5b15e32c3d6`
and the published prerelease is
[`v0.3.0-rc.1`](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.3.0-rc.1).
The replacement [terminal matrix run
35288077080](https://github.com/Wyrcan-io/playtestr/actions/runs/35288077080)
passed tests, vet, real PTY acceptance, deliberate failure HTML export, and
artifact upload on all three advertised hosts.

The first pushed matrix run `35287731727` failed on macOS and Windows because
the evidence root was canonicalized while aliased system temporary directories
were not. No release existed at that point. The regression was reproduced with
a Windows working-directory junction; platform-native final-path resolution and
a focused test fixed it before the successful replacement run.

[Native release run
35288218202](https://github.com/Wyrcan-io/playtestr/actions/runs/35288218202)
built, packaged, checksum-verified, extracted, and exercised all three archives,
including `playtestr report` against isolated snapshot-mismatch evidence. The
downloaded workflow archives matched their adjacent checksum files:

| Target | Archive SHA-256 |
| --- | --- |
| Linux amd64 | `dc8c3c2142219bc47a995b09bc8130b39fe6b8a5392e2b7f3bc4d999120ed881` |
| macOS arm64 | `498c163483b071f353ba3d4342a9680594e1ff1dc7f3139317b4979a34a07e1f` |
| Windows amd64 | `3ed1f69faa0abf970ee6cf1f17b59bd3d72f89e305ac2cf7b9687833a6a457f6` |

[Published-install run
35288555826](https://github.com/Wyrcan-io/playtestr/actions/runs/35288555826)
downloaded those public assets and passed checksum rejection, no-Go execution,
good/failure/recovery, invalid input, report-write failure, and applicable
controlling-terminal checks on all three hosts. Each downloaded binary also
rendered the intentional assertion-timeout evidence to HTML. Auditing all three
workflow artifacts found the expected `assertion_timeout`, captured greeting,
version, host, and archive hash.

## Deferred adoption gate

- Independent usability and maintainer adoption remain explicitly open until
  after Sprint 10. This follows the product decision and does not weaken or
  fabricate the technical acceptance above.
