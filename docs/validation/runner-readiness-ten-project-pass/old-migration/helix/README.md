# Original Helix migration

Original MPL-2.0 pin: `ba40e547426b0f9896c8bdc699a4ab11f2b37dbc`.
The twelve original cases require native Windows and Linux execution.
The contributed `contrib/themes` convenience link is explicitly omitted;
all actual `runtime/themes` resources and the original archive remain intact.
The strict extraction refusal is retained before the reviewed retry.

Original Cargo manifests, lock and license match the prior qualification.
The 337-package lock uses only crates.io registry sources. A prerequisite-only
fetch using the read-only installed Rust/Cargo 1.97.1 downloaded and verified
272 locked archives for Windows/Linux and exposed 35 available build hooks.
Their entrypoints and applicable filesystem/process branches were reviewed
before target compilation; compiler probes/generation use Cargo `OUT_DIR`,
and pinned C sources use the installed compiler. No unstable compiler override,
wrapper or development `gen-tests` feature is enabled. Hook availability does
not establish that every conditional branch runs. This is not a complete
security audit of dependency implementations.

The original supported `HELIX_DISABLE_AUTO_GRAMMAR_BUILD` switch prevents grammar
downloads/builds. Pinned ordinary runtime resources are copied without grammars.
Original configuration disables LSP, formatting, auto-save, clipboard and mouse.
No syntax/grammar integration or user files are in scope.

The loader's Git probe is bounded at the owned target root. A real failed Git
lookup proves the enclosing Playtestr checkout is excluded; the supported
`HELIX_NIX_BUILD_REV` fallback binds the original Helix pin. The actual binary
version must independently contain that pin. Windows linking uses `/Brepro`,
with two build jobs and no LTO/debug/incremental artifacts, matching the earlier
private build profile. Rust prerequisites are read-only when the installed
version matches exactly; otherwise native setup installs the pinned toolchain
only into owned directories. New homes, caches, build output and temporary files
stay inside this campaign. The owned active stop is 3 GiB, below the 4 GiB ceiling.

Windows compilation is in progress using the existing exact compiler. Standard
hosted Linux validation is prepared with one job, a 45-minute maximum and an
expected 10–20 native minutes including cold build and fault rebuilds. Aggregate
application/harness job concurrency stays at four or fewer. No target qualification
or migration admission is recorded yet. All old-project checks remain separate
from new-project and final-archive credit.
