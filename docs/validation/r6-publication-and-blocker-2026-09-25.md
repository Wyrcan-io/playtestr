# R6-P publication, R6-V repair and verification — 25–26 September 2026

## Published identity

- Release: [Playtestr v0.4.0-rc.1](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.4.0-rc.1)
- Annotated tag object: `35bb302d2cfddaf2c094cf492ecf50d4e973c6b9`
- Peeled runner source: `f6ffeb76a7ec3b826052690ab53071dcdf0e565f`
- Prerelease: yes; draft: no; published 2026-09-25T17:36:24Z
- Assets: exactly the three qualified archives plus
  `checksums-v0.4.0-rc.1.txt`

GitHub recorded the qualified archive SHA-256 values without mismatch:

| Target | Public archive SHA-256 | Size |
| --- | --- | ---: |
| macOS arm64 | `d6425d4c68f67e18214706c250ee4f1452f65259747b3ba85edca7741e8371d8` | 1,739,109 |
| Linux amd64 | `f7a4dd825fc066449265f90642a79dff0fc0318e4c1bc0918c139f699d461964` | 1,862,393 |
| Windows amd64 | `c33f02cff972edcd40109690a2909ffc834da86f7fdbfe95f881b344feb4ba2d` | 2,003,822 |

No tag or release asset was moved, renamed, rebuilt, added, or replaced after
publication.

## R6-V detected blocker

[Public install run 36168381776](https://github.com/Wyrcan-io/playtestr/actions/runs/36168381776)
completed with failure on Windows amd64, macOS arm64, and Linux amd64. The
setup action at the selected source identity requests
`<archive-name>.sha256`; each request returned HTTP 404 because the reviewed
release asset contract publishes the single aggregate
`checksums-v0.4.0-rc.1.txt` file. Every job stopped in installation. The
pass/failure/recovery step was not run, and no successful action outputs or
PATH entry were published.

This was a broken advertised installation route and initially blocked R6-V.
The release remained available by direct archive while the limitation was
stated in public guidance. The failed run is retained as the regression and
must not be reclassified as passing.

## Narrow repair

The action installer was changed to accept the release's aggregate
`checksums-<version>.txt` manifest when the older per-archive checksum asset is
absent. It still accepts the older asset contract, requires exactly one valid
entry for the requested archive, and rejects duplicate or malformed entries.
No runner archive, checksum, tag, or release asset changed.

- Repair commit and immutable action revision:
  `1c03904075512e67f53b0c94a13daa17f0383f1d`
- The focused installer integration suite, uncached repository tests, vet,
  race suite, and a real Windows public install passed before publication of
  the new pin.
- [Published-install run 36172240134](https://github.com/Wyrcan-io/playtestr/actions/runs/36172240134)
  passed on Windows amd64, Linux amd64, and macOS arm64. It verified the
  release/archive and executable identities, PATH and outputs, pass,
  intentional failure, recovery, reports, stale-PATH resistance, controlling
  terminal behavior, and execution without Go.

## R6-V closure

[Public verification run 36173075209](https://github.com/Wyrcan-io/playtestr/actions/runs/36173075209)
passed all six jobs on 26 September 2026:

- public bytes on Windows amd64, Linux amd64, and macOS arm64 matched the
  qualified archive and executable SHA-256 values;
- spaced-path extraction, version identity, pass/defect/recovery,
  cancellation/cleanup, controlling-terminal behavior, v1/v2/mixed suites,
  expected nonzero exits, and report v1/v2 completed on every host; and
- the same immutable action revision installed public `v0.3.0-rc.1` and
  `v0.4.0-rc.1` into separate directories on every host. The unchanged v1
  pass/failure/recovery flow worked on both, v2 worked only on the new runner,
  PATH changed as expected, and the reviewed baseline hash did not change.

The first attempt at that expanded workflow,
[36172618578](https://github.com/Wyrcan-io/playtestr/actions/runs/36172618578),
is also preserved. Its Windows public-behavior job failed in a redundant
workflow assertion because a PowerShell action output used a Windows path in
Git Bash. The installer and the Windows upgrade job had succeeded. Commit
`22118a3af7f07f26a2e519dafbac518bbc8d98c6` normalized that assertion with
`cygpath`; the complete rerun above then passed.

R6-V is complete. The immutable runner tag and its four release assets remain
unchanged. Manual interactive screen-reader evidence remains a separately
declared presentation gap and does not become a pass from automated checks.
