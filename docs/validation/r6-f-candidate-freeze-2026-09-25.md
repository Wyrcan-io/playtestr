# R6-F immutable candidate freeze — 25 September 2026

Status: complete. Candidate `v0.4.0-rc.1` is frozen, not published. Sprint 13-D's
separate pre-freeze rehearsal is recorded in
[its dated report](sprint-13-d-rehearsal-2026-09-24.md).

## Selection and identity

The feature boundary since `v0.3.0-rc.1` is coherent: exact-version setup,
fresh bounded spec-v2 workspaces, report v2 for mixed/v2 suites, and the
associated hardening and recipes. That is a minor prerelease rather than a
patch. Remote tags and releases were checked before freeze and again on 25
September; neither contained `v0.4.0-rc.1`.

- Frozen source: `f6ffeb76a7ec3b826052690ab53071dcdf0e565f`
- Native build run: [36103641387](https://github.com/Wyrcan-io/playtestr/actions/runs/36103641387)
- Toolchain: Go 1.25.0, `-trimpath`, `-s -w`, exact embedded version linker flag
- Machine record: [`release/candidate-manifest.json`](../../release/candidate-manifest.json)
- Candidate checksums: [`release/checksums-v0.4.0-rc.1.txt`](../../release/checksums-v0.4.0-rc.1.txt)

| Native target | Image | Executable SHA-256 | Archive SHA-256 |
| --- | --- | --- | --- |
| macOS arm64 | macos26 `20260907.0351.1` | `a2a662c53d948795cae12ee931d3d4e761a4baf9e54d7ddfe76ae2cd1fa524f8` | `d6425d4c68f67e18214706c250ee4f1452f65259747b3ba85edca7741e8371d8` |
| Linux amd64 | ubuntu24 `20260920.314.1` | `2ed5c7f06d9117a4450079312ffd00001205f893bbca36fbc0ab551338171d0b` | `f7a4dd825fc066449265f90642a79dff0fc0318e4c1bc0918c139f699d461964` |
| Windows amd64 | win25-vs2026 `20260922.246.2` | `7a73b598613d34e8a05831d12f2ab26d4abae3e6ce05e63c7d80c316bcc80fc2` | `c33f02cff972edcd40109690a2909ffc834da86f7fdbfe95f881b344feb4ba2d` |

Every archive has exactly one target-named root containing `LICENSE`,
`README.md`, `THIRD_PARTY_NOTICES.md`, and the native `playtestr` executable.
Each native job extracted into `release verification`, matched the executable
hash, printed `playtestr v0.4.0-rc.1`, and passed its packaged smoke. Exit was 0.
The final action-source install repeated this from the exact Windows archive
into a spaced path and reported both matching archive and executable hashes.

V1 specs/reports remain the downgrade-compatible format. V2 workspaces and v2
or mixed reports require this candidate; an old runner/reader can reject them.
Downgrade therefore means retaining v1 inputs/reports or converting reviewed
v2 material, never silently removing workspace behavior.

## Applied invalidation rule

Executable SHA-256, not `main`, is the identity. A source, dependency,
compiler, linker/build flag, or embedded-version change invalidates affected
executable evidence. Earlier builds 36053895808 and 36102736072 and preflight
runs 36050780383, 36054220190, and 36102917904 remain historical and were not
counted after source/corpus repairs. Later release-story and documentation-only
commits retained qualification because all three executable hashes stayed
identical. An archive/layout/install change would still require those checks
again.

Supported runner hosts are Windows amd64, Linux amd64, and macOS arm64. This is
not a claim that every third-party target runs natively on all three hosts, or
that a PTY is a security sandbox.
