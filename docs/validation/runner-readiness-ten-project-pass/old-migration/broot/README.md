# Original Broot migration

Pin `41cb4c78d9d7736dfe83c65f8a393fc962e50662`, MIT, Rust 1.97.1. Thirteen original canonical workflows declare native Linux amd64 and macOS arm64 cells. No Broot target has been built or executed in this migration yet.

The original large-tree case requires 527 state checks and 15,192 expected file bytes. Public rc.4 rejects it before launch (`e887ee7efc5545cd8b890555981ed02e`). R3-12 removes the independent count ceiling while retaining 1,000 total steps, aggregate/per-file/path/entry bounds and deadlines. The real-PTY regression observes 527 files in one invocation, rejects corruption of the last file and proves recovery. A new private candidate must pass native validation and be independently frozen before Broot execution. rc.4 bytes and all historical evidence remain unchanged.

Original archive/Cargo/license/source review passed `5c29f33dc9344aca8cebfa5ea6d21a4c`. Source-only dependency fetch `94022652b94b4c39ba26e86edf877f43` verified 411 locked archives for Linux/macOS without compilation. Hook review `7324a94802ea4086b4dd721e86cbcf40` binds 45 hooks. The source archive is retained once under the owned campaign root; source-only checked removal `791cc03bc6094a3b8effe18284437aba` preserves shared installed Rust prerequisites.

Prepared native tooling preserves all original actions, fixtures and snapshots; the large-tree checks remain in the same public execution. Fault calibration will compile the original copy verb with the original wrong-source mutation, require terminal-only success and public saved-state failure, then restore exact source and compiled bytes. These are declarations, with zero Broot runtime, migration-admission or final-archive credit so far.
