# Helix scope declared before application acquisition

Immutable selection: `helix-editor/helix` at
`ba40e547426b0f9896c8bdc699a4ab11f2b37dbc`, MPL-2.0. This declaration uses
the screened README and read-only pinned Cargo/build/runtime metadata;
no Helix source checkout or application runtime has been acquired yet.
Linux and Windows are provisional native hosts until successful execution.

The maintainer journey is regression testing useful, local plain-text editing
through the ordinary `hx` binary. Fixtures contain synthetic UTF-8 text,
protected neighboring files, nested paths and names with spaces. Managed home,
temporary directories and explicit configuration keep sessions independent of
the operator's real project, settings, language servers and clipboard.

| Intended useful normal workflow | Independent evidence |
| --- | --- |
| Insert and save Unicode text in an existing file | Exact complete saved bytes, preserved neighbor, meaningful live screen |
| Open and switch between two noninitial buffers | Correct active content/path transitions; exact saved state of both files |
| Search for a noninitial line and continue editing | Specific selected/result position, retained neighboring content and exact final bytes |
| Replace an explicit selection and save | Exact replaced region and unchanged surrounding lines |
| Undo and redo a real change before saving | Visible change/restoration plus exact final saved contents |
| Create and save a new file with a spaced Unicode name | Exact path/content and unchanged original fixtures |

| Intended distinct edge workflow | Required behavior/evidence |
| --- | --- |
| Reject an ordinary quit with unsaved changes; explicitly discard | Actual refusal, recoverable session, original disk bytes unchanged |
| Search with no match and recover to useful editing | Specific failure/recovery transitions; no unintended edits |
| Invalid command and recovery | Visible accurate error followed by successful useful action |
| Cancel partially typed command/search input | No canceled operation applied; exact protected state |
| Repeated resize and navigation in a long Unicode file | Fresh meaningful viewport/cursor evidence; bounded execution and exact saved bytes |
| Save failure at an invalid/occupied destination and recovery | Actual application error, original data intact and explicit subsequent save |

These are intentions, not credits. Actual pinned behavior, commands and captions
must be explored before contracts are exported. Undefined actions will be
replaced by explicit supported cases with the rationale retained; no fabricated
assertions or baseline updates may hide a defect. At least five distinct normal
and five distinct edge cases must survive independent review and native runs.

The supported upstream build hook `HELIX_DISABLE_AUTO_GRAMMAR_BUILD=1` avoids
fetching many grammar repositories. The admitted files require no grammar,
syntax highlighting or language server. Runtime lookup ordinarily includes
`runtime` beside the executable; only pinned ordinary runtime resources are
copied into that owned location. The compiler is exact Rust 1.97.1, with private
Rustup/Cargo/build caches, locked dependencies, two compilation jobs, release
optimization, no LTO/debug/incremental artifacts and bounded installation/build
commands. Windows requires the pre-existing MSVC toolchain and SDK; native
GitHub-hosted Windows has to verify that actual build path. These choices do
not change target source semantics or add a Rust implementation to Playtestr.

Two minimal actual source faults must change different tested behavior/outcome
and recover after exact restoration without changing specs or baselines.
Persisted corruption must leave a meaningful terminal success-looking state
while a bounded independent file probe rejects actual wrong saved bytes.
Mutation rebuilds must invalidate Cargo artifacts of the affected package so
restored source mtimes cannot accidentally reuse a mutated binary.

No promise covers LSP/debug adapters, grammar acquisition/highlighting fidelity,
system clipboard, external commands/formatters, network remotes, style/mouse or
complete grapheme behavior, concurrent real-file editors, all Helix features,
beginner usability or launch readiness. No native coverage is claimed by this
scope declaration. Fresh fixtures, explicit checkpoints, positive state probes,
first-failure evidence and verified owned teardown remain mandatory.
