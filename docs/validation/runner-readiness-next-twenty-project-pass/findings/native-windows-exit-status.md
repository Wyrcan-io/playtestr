# Native Windows status and HTML failure evidence

Status: general production fix implemented; local native regressions, full Go
suite and vet passed. Replacement archive/native qualification remains open.

The real source-built cargo-generate CLI terminated with Windows native status
`3221225786` (`0xC000013A`) when Ctrl-C was sent at its first prompt and later
selector. The rc.5 runner accurately observed that status, but spec validation
allowed only `0` through `255`; a corrected exact expectation was rejected before
launch. The HTML reader also rejected a report containing the captured status.
This is a general runner/report boundary, not an upstream substitution reason.

Both before-fix regressions failed as expected: a real ConPTY target could not
declare statuses above 255, and HTML rejected native-status failure evidence.
The repair extends spec v3 assertions to unsigned native 32-bit values and lets
all report readers/schemas retain those captured values. V1/v2 assertion limits
remain unchanged. No exit truncation, signal remapping, target-name condition or
target source patch is introduced. Negative and overflowing values are rejected.

Local-only command evidence under the new ignored campaign root:

- Before-fix real native regression: `core/2d95f0128f8d408a8e2e791a43b4f9a5`.
- Before-fix HTML rejection: `core/7c6ac9cf64034606bdef8665874e7e78`.
- After-fix native/HTML regressions: `core/e929f810e71748dc99f2607a545b9c50`.
- V1/v2/v3 bounds plus native/HTML: `core/88afaa0afc6a451aac03e692d9878b13`.
- Full Go regression: `core/3295052a0d6e483394c6b74875ae9790` (192.797 seconds).
- Go vet: `core/42ca46bdcc8544ce946b4e310c1ae070`.

The first full cargo-generate development series is retained at local-only
`cargo-generate/development/6579be4e7db242b3b9ff20d72f2bdcd8`; all earlier
inputs, mismatches and prelaunch refusals remain separate. Exact inputs were
preserved before authoring corrections. Source-fault selection has not begun.

Build a distinct private candidate after source-matched native checks. The ten
first-batch projects and four new rc.5 admissions must be requalified on those
exact replacement bytes. Preserve their historical immutable receipts; do not
call rc.5 execution a replacement-candidate pass. Required old migrations,
whole controls, delivered-CI triplets, archive routes and fresh-checkout closure
also need honest replacement-candidate dispositions.

See the [pending migration](../../../migration-v0.4.0-rc.6.md). Microsoft's
[GetExitCodeProcess contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess)
describes the native DWORD application/exception status.
