# Helix development validation - in progress

Pinned MPL-2.0 source: `helix-editor/helix` at
`ba40e547426b0f9896c8bdc699a4ab11f2b37dbc`.
[Scope](scope.md) preceded application acquisition. Rust 1.97.1, locked Cargo
inputs and exclusively owned runtime/dependency caches build the ordinary `hx`
binary. The upstream supported hook disables grammar acquisition for the
admitted plain-text scope. Explicit configuration disables LSP, auto-format,
auto-save, system clipboard and mouse; no real user home or files are used.

Six normal and six edge contracts have been recorded, replayed and independently
checked on local Windows. WSL passed all twelve current reviewed-screen/exact
file-state probes and ordinary checks; the revised search case passed its fresh
public recorder replay. Neither environment alone qualifies hosted native Linux
or the final frozen campaign. Native Linux/Windows development qualification,
Linux qualification and local teardown remain pending. Hosted Windows run
`38324763718` passed all twelve workflows, 120 ordinary repetitions, 120
separate file-state probes, actual source faults, restoration and owned deletion.
The same run passed core/race checks on all three native operating systems;
standard CI `38324763722` also passed.

Hosted Linux failed the directory-save checkpoint: its real screen said
`Is a directory (os error 21)` instead of the expected Windows mtime refusal.
[Retained native evidence](../native/38324763718/manifest.json) preserves the
failure and successful Windows results. A first local attempt to merely change
the expected string also failed because directory mtimes can trigger the earlier
refusal. The reviewed Linux variant explicitly uses `:write! occupied` to reach
the actual filesystem directory-write rejection, then saves to `main.txt` and
checks every protected fixture byte. This bypasses no filesystem refusal. Its
public recording, reviewed rows and ordinary replay passed; it is one scenario,
not extra scenario credit. The Windows contract remains unchanged.

Normal cases save a complete Unicode document, switch/save/return across
buffers, open/edit a nested spaced Unicode path, replace one selected word,
undo/redo before saving and create a new spaced Unicode filename. Edge cases
reject unsaved quit then explicitly discard, recover from an unknown command,
cancel a partial destructive command, recover from a no-match search, reject an
occupied save destination then explicitly recover, and repeatedly resize and
navigate a long Unicode document. All eight fixture files are checked exactly;
protected neighbors and occupied-directory contents must remain unchanged.

Row snapshots retain rows 1?29: document contents, buffer identities, mode and
cursor position. Only transient bottom command/status messages are excluded;
explicit error/write checkpoints and exact independent saved bytes complement
those rows. One nested-path case has an explicitly reviewed Unix baseline for
native slash spelling; variants do not count as additional scenarios.

[Original failures](first-failures/manifest.json) retain authoring and setup
mistakes. A full-selection change retains the buffer's final newline; inserting
an additional final LF created a genuine extra blank line rejected by the file
probe. Literal LF did not perform logical Enter in the Windows target input
path, so the revised contract explicitly sends Enter between lines. Raw control
byte delivery remains the existing product contract; no automatic newline
normalization was introduced. Escape followed immediately by another command
was parsed as a combined sequence on Unix. Explicit INS/NOR readiness and
observed error-message disappearance make editor transitions measurable without
input sleeps. Already visible neighboring text could not prove cursor movement;
the cancellation case asserts its fresh actual `2:1` position instead.

[Historical contracts](historical-native-newline/normal-project.json) and the
original search-Escape contract remain preserved. The intended saved bytes were
not weakened to accept extra blank lines or dropped line breaks. Pristine
source is not modified to make authoring mistakes pass.

[Setup failures](setup-first-failures.json) show private Rustup self-update
failure and Cargo selecting system Rust 1.75 despite a direct Rustup 1.97.1
version check. The recipe disables self-update and binds Cargo to the canonical
owned compiler executable. MSVC's ordinary PE header carried wall-clock time;
`/Brepro` enables deterministic linking. The first actual Windows source-fault
control detected diverted write behavior, then restored exact source and binary
hashes with unchanged contracts and ordinary/state recovery. All three actual
controls subsequently passed on Windows and WSL: diverted write, ordinary quit
that discards unsaved edits, and saved corruption that preserves terminal green
but fails the independent file probe. [Compact local fault evidence](local-fault-evidence/manifest.json)
retains actual reports, screens, state errors and unchanged-contract identities.

Manual maintenance changes one intended title input and its explicitly selected
associated checkpoint in a separate copied spec. Ordinary snapshot mismatch,
HTML diagnosis, named update, ordinary recovery, relocation and workflow preview
passed while all primary bytes stayed unchanged. Suffix rerecord passed. The
prepared public operator route used four commands and twenty recorder controls
with no manual JSON edits; its four seconds excludes acquisition, fixture
engineering and earlier authoring corrections. This is an automated warm-cache
operator assessment, not beginner authoring time. All twelve current ordinary
and separate state cases then passed again on the pristine restored Windows
target. Hosted Linux/Windows repetitions and owned teardown remain required.

No syntax/LSP/grammar/style/mouse fidelity, external formatter/clipboard,
arbitrary concurrent real-file editor, full Helix coverage, beginner usability,
final campaign acceptance or commercial-readiness claim is made.
