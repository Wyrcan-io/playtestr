# Sprint 13-B setup-action engineering — 21 September 2026

Status: locally verified on Windows amd64; the final exact-commit three-host
source-action run is pending. No tag, release, Marketplace listing, or immutable
public action revision was created.

## User-visible result

The setup action continues to install one exact runner version from the native
release mapping, and now also returns the installed executable's SHA-256. The
installer compares the staged and final executable hashes before writing any
successful output. A test-only target override that names another supported but
non-native platform is rejected before download with the native and requested
targets in the diagnostic.

Runner and action pins remain independent: `version` selects runner release
bytes, while a future immutable action commit selects installer code. This
checkpoint prepares source evidence only and does not publish either identity.

## Regression-first evidence

On base commit `1a098bd`, the new focused tests failed before the installer
change for the intended reasons:

- `binary-sha256` was absent; and
- a supported non-native target attempted to find the wrong archive instead of
  rejecting the platform mismatch.

The implementation adds the output and native match check without changing
archive names, supported host mapping, runner version syntax, or report/spec
contracts.

## Covered setup paths

`go test -count=1 ./internal/setupaction` now covers:

- exact version, archive SHA-256, executable SHA-256, archive layout/member,
  native OS/architecture mapping, spaced install paths, and PATH precedence;
- local verified-archive injection and successful HTTP archive download;
- execution by absolute path after the HTTP server is closed, establishing the
  installed step is offline;
- corrupt checksum, malformed archive with matching checksum, escaping and
  missing members, unsupported and supported-but-non-native platforms;
- truncated response, oversized response, bounded request timeout, failed
  extraction, and missing release;
- empty bounded cleanup and no output/PATH exposure for every failed install;
- rollback of the final installed directory and action environment files when
  either output destination rejects publication.

The installer still uses a fixed public GitHub release origin in production.
`DownloadDirectory`, `DownloadBaseUrl`, target overrides, timeouts, and attempt
counts remain non-action test seams, not untrusted action inputs.

## Local result

Windows build `10.0.26200` amd64, Go `1.27.0`, and Windows PowerShell `5.1`
passed the final full uncached suite in 32.5 seconds, vet in 0.6 seconds, race
suite in 93.6 seconds, and focused native gate in 55.2 seconds. The real-PTY
mixed-contract, deliberate-failure, HTML, and recovery rows also passed and are
recorded under ignored local artifacts. One first full
rehearsal encountered a sandbox-denied global Go cache and one non-repeating
race-instrumented resize/output-limit failure; the harness now sets a bounded
project-local Go cache before every Go command, and an immediate uncached race
rerun passed all packages without changing product limits.

## Native and publication gate

The final commit must produce six required installer test passes, zero
unexpected skips, and successful integrated rows on Windows amd64, Linux amd64,
and macOS arm64. The handoff records that run and its three artifact names.
Preparing source and hashes is not evidence for an immutable public action
reference. Public action verification remains after explicit publication
approval in R6-P/V, and no successful upgrade claim is made without two actual
published runner pins.
