# Support and compatibility

Start with the public [documentation](https://wyrcan-io.github.io/playtestr/docs/),
[troubleshooting guide](https://wyrcan-io.github.io/playtestr/docs/troubleshooting/),
and [compatibility overview](https://wyrcan-io.github.io/playtestr/docs/compatibility/).
The reporting routes and detailed policy remain below.

## Supported v0.1.0 downloads

Playtestr v0.1.0 publishes native archives for Linux x86-64 (`amd64`), Apple
silicon macOS (`arm64`), and Windows x86-64 (`amd64`). Support means the exact archive passed its native package and
public-install workflows. It is not a claim for other architectures, every OS
release or Linux distribution, or every terminal application.

The standalone runner needs no Go installation. The target command and any
runtime it needs remain the user's responsibility. Only run explicitly trusted
targets: Playtestr is not a sandbox.

## Contract policy

v0.1.x accepts test specification version 1 and emits machine report version 1.
Patch releases preserve the meaning of existing valid v1 specs, CLI exit codes,
and existing report fields. A patch may add an optional action or report field,
fix behavior that contradicts the documented contract, or narrow an unsafe
claim. Consumers must ignore no unknown data silently: validate `version` or
`report_version` and upgrade deliberately when using an addition.

An incompatible test or report meaning requires a new explicit format version
and migration notes. Pre-1.0 minor releases may add functionality, but published
v1 inputs are not reinterpreted silently. Published tags and assets are never
overwritten; a corrected release receives a new version.

No support lifetime or response-time SLA is promised. Current evidence and
limitations are listed in [`docs/platform-support.md`](docs/platform-support.md)
and [`docs/terminal-compatibility.md`](docs/terminal-compatibility.md).

## Reporting a bug

Use the [bug report form](https://github.com/Wyrcan-io/playtestr/issues/new?template=bug-report.yml)
for information safe to publish. Include:

- `playtestr --version`, the archive name, and its observed SHA-256;
- host OS/version/architecture and target application/version;
- the smallest spec and reset steps that reproduce the result;
- expected and actual exit status and failure category; and
- sanitized report, screen, and diff evidence when relevant.

Remove credentials, tokens, private source, personal paths, command arguments,
typed values, and sensitive terminal output before posting. Do not accept new
snapshot baselines merely to make a failing report pass.

Release blockers are false passes, surviving managed processes, baseline or
unrelated-file loss, sensitive data persisted by Playtestr itself, corrupt or
uninstallable advertised assets, and a stable contract contradiction.

For a sensitive security report, use GitHub's
[private vulnerability report](https://github.com/Wyrcan-io/playtestr/security/advisories/new).
Do not put a vulnerability, exploit, credential, or unsanitized evidence in a
public issue. Private reports are reviewed by the repository owner; no response
time is guaranteed.
