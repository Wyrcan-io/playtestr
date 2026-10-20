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

Local Windows and hosted Linux run `39388692279` now pass all twelve original
scenarios and the real compiled save corruption: the terminal-only contract
passes the wrong saved bytes, the public v3 assertion rejects them in that same
execution, and exact source plus compiled-binary restoration passes unchanged
expectations. Independent [Windows](verified-windows.json) and
[Linux](verified-linux.json) audits bind actual public commands, compiler/Cargo
hashes, original runtime resources, invocation/workspace identity and cleanup.

The [admission](migration-admission.json) records twelve canonical scenarios,
two native cells, 24 qualified primary and six calibration executions. All 45
observed ordinary executions retain the first Linux run whose tests passed but
source retention correctly refused the checklist's wrong resource path; see
[its disposition](first-native-disposition.md). No earlier failure is erased.

Owned local source, build output and dependency caches are removed; the installed
compiler is preserved. Both native packets are locally retained in verified
compressed archives (2,185,865 first-run bytes; 2,372,894 corrected-run bytes),
with selected restoration and explicit canonical-source checks. Expanded copies
are removed. The selected project retains 9,157,433 bytes, under its 32 MiB cap.
Campaign harness runs are serialized with at most two jobs alongside at most
two application jobs. New-project and final-archive credit remain zero here.
