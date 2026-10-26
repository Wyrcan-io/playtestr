# cargo-generate: qualification in progress

Pinned upstream `cargo-generate/cargo-generate` at
`9c0c27568113cfc9caefac50336b5d4b92c055a9` (version 0.25.1), licensed
MIT OR Apache-2.0. All 167 primary Git blobs match the acquired source.

The selected workflow generates a project from a small synthetic local template,
using the real dialoguer prompts and Liquid expansion. Planned checks compare
generated files with independently declared bytes and preserve unrelated data.
Remote templates, credentials, external editors and template shell commands are
outside this package's scope.

The source review and dependency hook review are complete. The fetch executed no
build hooks or target code: 369 archives match Cargo.lock checksums and all 16,222
unpacked source files match their archive members. The ordinary default-feature
CLI build succeeded using locked offline dependencies, owned caches and read-only
Rust/MSVC prerequisites. A physically shorter, independently verified registry
copy resolved MSVC include failures; both original failures remain retained. The
version command succeeded; a wrong banner check in the outer helper is separately
preserved and corrected by readback of the original execution.

The repaired public route passed with exact generated-file/sentinel checks,
three shell calls and twenty recorder controls. The initial missing synthetic
USERNAME and volatile full-screen snapshot misses remain preserved. Public row
selection excludes the temporary destination line; no blanket normalization is
used. Across the initial and repaired windows there were nine Playtestr shell
calls and 65 requested controls, so this is not an initial usability-target pass.

The first complete development run passed 17/20. Windows Ctrl-C exposed the
[general native-status defect](../findings/native-windows-exit-status.md).
An undefined Liquid variable rendered empty; the mistaken error expectation was
retained and replaced with genuinely malformed syntax. Two separate authoring
prelaunch refusals (unsupported key and wider exit value) are also preserved.
No twenty-case freeze, source fault, qualified native cell or project admission
exists yet. The campaign remains at four new rc.5 admissions. Human usability is
unmeasured. Continue against the distinct replacement candidate after its build.
