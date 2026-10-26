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
CLI build uses locked offline dependencies, owned caches and read-only installed
Rust/MSVC prerequisites. Its actual completion and version check remain pending.

No first-use success, scenario, fault, native-cell or project admission is claimed
yet. The campaign remains at four new admissions. Human usability is unmeasured.
