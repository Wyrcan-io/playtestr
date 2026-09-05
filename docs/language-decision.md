# ADR 001: Go for the local runner

Status: selected for the MVP, September 5, 2026.

## Decision

Use Go for the terminal engine, CLI, fixtures, and local report generation. Keep JSON as the initial test format. Do not introduce an additional implementation language or a runtime bridge for the MVP. The language of the application under test is independent of the runner's language.

## Alternatives

| Choice | Benefits for this project | Costs and decision |
| --- | --- | --- |
| Go | Compiled CLI, integrated testing/profiling, straightforward concurrent process I/O; existing working Windows prototype. | Garbage-collected runtime; terminal library behavior still needs verification. Best balance for our iterative development and distribution goals. |
| Rust | Fine control over allocation and resource ownership without a garbage collector; credible choice for a terminal engine. | A rewrite would not itself resolve terminal compatibility. Choose if measured resource or latency requirements justify the added engineering work; no such evidence exists yet. |
| TypeScript | Most direct reuse of gametestr; node-pty and xterm already underpin that implementation. | Node runtime plus native PTY dependency complicate standalone distribution. Strongest alternative if rapid reuse becomes more important than a standalone Go tool. |
| Python | Concise test scripting and automation. | Standard-library PTY support is Unix-only, requiring another Windows backend. Adds a runtime without reusing the TypeScript implementation. Not selected for the core. |
| Combination | Could eventually offer language-specific SDKs or a web UI. | Multiple toolchains, cross-language failures, and versioned integration contracts would expand the MVP unnecessarily. Defer until a concrete consumer needs it. |

## Performance and longevity

No comparative benchmark has been run. We expect process startup, target rendering, output volume, and assertion waiting to dominate normal interactive tests; this is a hypothesis, not a measured language ranking. First measure launch-to-ready time, runner CPU/memory under output load, and repeated-session cleanup. Separate intentional waits from runner overhead.

Long-term reliability depends on terminal fidelity, bounded I/O, lifecycle handling, stable file formats, and reproducible evidence. Language speed cannot compensate for a false assertion or a leaked process. Keep PTY access and screen emulation behind small internal boundaries so either library can be replaced without changing the test format.

Charm's xpty is in its experimental package collection, and the current vt10x dependency is an older implementation. Both are provisional dependencies. Validate redraws, split escape sequences, Unicode, alternate screens, resize, and exit behavior before claiming compatibility. A failed dependency evaluation should first trigger a library investigation, not an automatic language rewrite.

The gametestr implementation remains a design and fixture reference. We will not port its entire autonomous exploration system into this MVP.

## Primary references

- Go compilation, concurrency, runtime, and engineering goals: https://go.dev/doc/faq
- Rust memory/runtime model: https://rust-lang.org/
- Node PTY implementation and platform build requirements: https://github.com/microsoft/node-pty
- Python PTY availability: https://docs.python.org/3/library/pty.html
- Charm experimental packages: https://github.com/charmbracelet/x
