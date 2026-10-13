# Broot scope declared before application acquisition

Pinned MIT source: `Canop/broot` at
`41cb4c78d9d7736dfe83c65f8a393fc962e50662`. Linux and macOS are provisional
native hosts. No Broot checkout or executable has been acquired. Read-only
review of pinned Cargo metadata and `build.rs` established Rust 1.85 minimum,
an ordinary `broot` binary, disabled optional clipboard/sixel features, and a
build hook generating completions exclusively under Cargo `OUT_DIR`.
The existing owned Rust 1.97.1 recipe is the proposed build route.

Act as a maintainer testing local tree navigation and useful file operations.
Use synthetic files, an explicit reviewed configuration, temporary home/temp,
and no shell-function installation into real user settings. Verify the actual
configuration/install-state behavior before recording; the pinned CLI offers
explicit configuration paths and install-state options, whose execution
semantics must be observed rather than assumed.

| Useful normal intention | Positive and independent evidence |
| --- | --- |
| Find and navigate into a noninitial nested directory | Actual selected path/file transition and preserved neighbors |
| Filter to a spaced Unicode filename and inspect it | Distinct result identity/content and exact original bytes |
| Copy one real file to a new destination | New path with exact bytes, source and neighbors unchanged |
| Rename or move a selected file | Exact new path/content and original-path absence |
| Create a nested directory through a supported internal verb | Actual directory state and preserved existing files |
| Open a second panel/root and perform a local operation | Correct pane/context transition and independent resulting filesystem state |

| Distinct boundary intention | Required evidence |
| --- | --- |
| Empty directory | Accurate empty state and bounded natural quit |
| Filter with no match and recover | Positive empty-result state and subsequent useful selection |
| Cancel a partially typed operation | No filesystem operation applied; protected state intact |
| Invalid verb or destination and recovery | Accurate refusal followed by a successful supported action |
| Occupied/conflicting destination | Explicit overwrite/refusal behavior, no silent data loss |
| Repeated narrow/wide resize and long nested names | Fresh viewport/selection evidence and unchanged disk data |

These are intentions, not credits. Replace an unsupported intention only with
a different useful supported operation, preserving the reason and failures.
Do not turn cosmetic variations into distinct workflows. Retain meaningful
tree, selection and preview evidence; exclude only justified host paths,
relative age/duration labels or metadata outside the admitted text contract.

Two different actual owned-source regressions must fail unchanged contracts.
A state-corruption control must preserve terminal green while the independent
file/path oracle rejects it. Restore exact source and reproducible target
binary hashes before ordinary/state recovery. Keep licensed minimal patches;
do not qualify a patched upstream target. Check Rust mutation package ownership
before deciding which Cargo package needs rebuilding and cleaning.

Assess the public first-use route, suffix rerecord, a meaningful manual spec
edit, actual failure/HTML diagnosis, named baseline update, spaced Unicode
relocation and generated workflow. Native jobs run workflow-equivalent commands
and independent checks; configured jobs or template previews are not execution.

Use the campaign's twenty-minute prerequisite, 120-second case, thirty-second
negative-probe, ten-second independent-probe, four-GiB target, 64-MiB fixture
and 128-MiB evidence bounds. One application repository remains active at a
time: acquire Broot only after Glow's required native qualification and verified
owned teardown. Source/runtime/dependency caches are removed after verification.
No network navigation, external editor, clipboard, graphics, real shell/home
modification, full application coverage or beginner usability is claimed.
