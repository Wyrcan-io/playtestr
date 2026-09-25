# Release story: catch a wrong selection

This 45–60 second editorial story uses the repository-owned selector fixture and
the qualified native runner. Its complete, uncut automation is
[`release/stories/run.sh`](https://github.com/Wyrcan-io/playtestr/blob/main/release/stories/run.sh); no wait is accelerated
and the Actions log plus JSON/text evidence are the capture record.

1. Build the normal selector and run [`hero.json`](https://github.com/Wyrcan-io/playtestr/blob/main/release/stories/hero.json).
   The file oracle must contain exactly `Beta`.
2. Build the same target with `competitive_bad`. This reviewed target defect
   selects `Alpha`; the spec is unchanged, exits 1, and reports
   `unexpected_exit` rather than a fabricated success.
3. Inspect `hero-defect.json` and its retained focused evidence, restore the
   normal target, and rerun. The file oracle again contains `Beta`.

Run all three stories with an executable extracted from the matching candidate
archive:

```sh
bash release/stories/run.sh /absolute/path/to/playtestr artifacts/release-stories
```

The script records runner, target, and spec SHA-256 values, outcomes, cleanup,
postconditions, commands, and disclosure in `summary.json` and `hashes.txt`.
The spec is the reviewed interaction baseline; this story has no snapshot file
to update.

For a properly attributed third-party variant, use the
[Charm Gum v0.17.0 selector recipe](https://wyrcan-io.github.io/playtestr/docs/recipes/selector/). Gum is an MIT-licensed
Charmbracelet project. Playtestr's operator-run recipe does not imply its
maintainers' endorsement.
