# Small runnable examples

The menu examples exercise the demo's terminal interaction. `saved-state.json`
adds exact binary output, absence and directory-entry assertions in the same
managed execution; see [spec v3](../docs/spec-v3.md) for its fixture command.

Keep the same readiness/exit checkpoints when extending that example with
additional explicitly selected files. Terminal and state actions share a
1,000-total-step limit, with at most 512 KiB of expected file bytes in aggregate
and 64 KiB per file. A larger checkpoint observes all its selected files in that
same invocation. Earlier private rc.4 binaries reject more than 100 state actions;
use the rebuilt source candidate for expanded checkpoints. Screen updates never
approve file bytes, and extra replays cannot substitute for same-run assertions.
