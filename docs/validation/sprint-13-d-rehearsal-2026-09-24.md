# Sprint 13-D adversarial evidence and release rehearsal — 24 September 2026

## Conclusion

Sprint 13-D is complete on the pre-freeze Windows amd64 development path. The
current-source risk inventory passed, and an archive installed below a path
containing spaces ran a mixed v1/v2 suite with four passing cases and one
intentional snapshot mismatch. The runner returned exactly status 1 for the
mixed failure; recovery returned 0 with the reviewed baseline unchanged.

This is rehearsal evidence only. It does not identify or qualify the R6
candidate bytes.

## Adversarial matrix

`scripts/test-integrated-hardening.ps1` ran at source
`161fd937ec0cac1c10c3a8bf0d07eee3134bd2c9` on Windows amd64 and passed all 15
integrated commands, including uncached tests, vet, the Windows race suite,
focused native-gap tests, mixed v1/v2 contracts and HTML, deliberate failure,
and recovery. The focused tests cover hostile terminal/HTML text; missing,
oversized, per-file, aggregate and generated evidence; traversal, absolute and
remote references; aliases; escaping links and Windows junctions; stale
evidence; cancelled staged snapshot updates; report/artifact write failures;
applicable permission failures; bounded cancellation, flood and cleanup; and
secret canaries.

The privacy boundary is unchanged: environment or typed canaries that the
target does not render are absent from retained results, but target-rendered
text is evidence and can contain secrets. Playtestr does not redact it
automatically and is not a sandbox.

The first baseline invocation ran tests and vet concurrently and encountered a
shared global Go-cache access error. It is retained as an operator/harness
failure. Sequential uncached `go test -count=1 ./...`, `go vet ./...`, and
`scripts/test-race.ps1` all passed without changing product limits.

## Manual archive rehearsal

The accepted rehearsal used embedded version `v0.4.0-rc.1-rehearsal`, build
flags `-trimpath -ldflags "-s -w -X
github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=$VERSION"`, and a
Windows amd64 ZIP containing only the executable, README, license, and third
party notices. The archive was extracted under `installation path with spaces`
and the extracted executable hash matched the pre-package executable.

The mixed suite contained:

- v1 menu pass;
- v1 clean exit pass;
- v1 exact expected target exit 7 pass;
- v2 fresh workspace pass with no retained `state.txt`;
- v1 intentional snapshot mismatch using the unchanged reviewed baseline.

The mixed report and offline HTML were generated, failure category was
`snapshot_mismatch`, suite status was exactly 1, and recovery passed 4/4 with
status 0. Baseline SHA-256 remained
`96bbce2386a3ab5e113225d126bbedbd674e1bcc28f33c657c4d621604aa3eb4`.

An earlier rehearsal attempt accidentally packaged a stale `dev` binary after
PowerShell treated a non-fatal Go cache warning as terminating. Its v2 decode
failure is preserved in private rehearsal artifacts and is not counted. The
accepted procedure asserts `--version` before packaging and again after
extraction.

## Candidate handoff

The selected candidate is `v0.4.0-rc.1`. Remote tags and releases were checked
before selection; the newest existing version is `v0.3.0-rc.1`, and no
`v0.4.0-rc.1` tag or release exists. A new minor prerelease is appropriate
because the batch adds opt-in spec/report v2 workspaces and setup/action and
corpus hardening after the v0.3 report prerelease. It is not labeled stable
before frozen-byte qualification.

V1 specs remain the downgrade-compatible contract. V2 specs and reports may be
rejected by older runners/readers, so downgrade requires retaining or converting
tests to v1 and preserving v2 evidence for a current reader. No baseline rewrite
is part of migration.

[`release/candidate-config.json`](../../release/candidate-config.json) freezes
the version, Go toolchain, commands, targets, contracts, inputs, reviewed
baselines and support exclusions. R6-F next records the clean source commit and
the three native executable/archive identities. No tag, release or action
revision was published.
