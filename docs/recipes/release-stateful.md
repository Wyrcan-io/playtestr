# Release story: prove persisted state

This 60–90 second editorial story uses a fresh file path and the qualified
native runner. The target is repository-owned and the independent adapter reads
the file after the TUI exits; screen text is not accepted as the state oracle.

- Normal pass: invalid input is rejected, `4242` is accepted, and the file is
  exactly `port=4242`.
- Cancellation: Ctrl-C exits 130 and the declared file does not exist.
- Reviewed defect: `competitive_bad` writes `port=8080`; the unchanged
  [`stateful.json`](https://github.com/Wyrcan-io/playtestr/blob/main/release/stories/stateful.json) exits 1 because the
  adapter returns 90.
- Recovery: restore the target and verify `port=4242` again.

Run the shared command in the [hero recipe](https://wyrcan-io.github.io/playtestr/docs/recipes/release-hero/). Exact logs,
reports, target/spec hashes, filesystem checks, and cleanup outcomes are kept.
There is no video editing or accelerated wait. The environment path points only
inside the selected output directory.
