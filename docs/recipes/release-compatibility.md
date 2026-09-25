# Release story: preserve modal state across resize

This 60–90 second editorial story opens a help modal, resizes from `60x12` to
`80x20`, redraws, closes the modal, and exits. The independent result file must
be exactly `size=80x20 modal=false`.

The reviewed `release_story_bad` target reports a stale `60x12` viewport. The
unchanged [`compatibility.json`](https://github.com/Wyrcan-io/playtestr/blob/main/release/stories/compatibility.json)
rejects it with `assertion_timeout`; forced cleanup is confirmed and no result
file is accepted. Restoring the target passes the same spec and file oracle.

Run the shared command in the [hero recipe](https://wyrcan-io.github.io/playtestr/docs/recipes/release-hero/). The claim is only
for this fixture, behavior, candidate hash, and the Windows amd64, Linux amd64,
and macOS arm64 jobs in run 36108031093. It is not a universal terminal,
Unicode, or third-party-framework claim. No recording was edited and no wait
was accelerated.
