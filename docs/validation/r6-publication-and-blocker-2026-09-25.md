# R6-P publication and R6-V blocker — 25 September 2026

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

## R6-V blocking result

[Public install run 36168381776](https://github.com/Wyrcan-io/playtestr/actions/runs/36168381776)
completed with failure on Windows amd64, macOS arm64, and Linux amd64. The
setup action at the selected source identity requests
`<archive-name>.sha256`; each request returned HTTP 404 because the reviewed
release asset contract publishes the single aggregate
`checksums-v0.4.0-rc.1.txt` file. Every job stopped in installation. The
pass/failure/recovery step was not run, and no successful action outputs or
PATH entry were published.

This is a broken advertised installation route and blocks R6-V. The release
remains available by direct archive, with the limitation stated in public
guidance. Website deployment, announcements, maintainer recruitment, the
manual screen-reader session, A1, and A2 did not proceed. A new immutable
action revision or a new release/version decision requires maintainer review;
the published tag and four assets must remain unchanged.
