# Reviewing text snapshots

Snapshots protect the complete rendered terminal screen after the application reaches a positively identified state. They compare normalized text, not ANSI byte streams, colors, or styles.

## When a snapshot helps

Use `expect` for a small fact such as a prompt or confirmation. Add a snapshot when line order, spacing, a menu selection, or several visible values together form a useful reviewed interface contract.

A snapshot must follow a successful `expect` or `expect_not` since the most recent input or resize, or a successful `exit` assertion. This prevents quiet output from being mistaken for readiness.

## Create one baseline deliberately

```text
playtestr test --update --snapshot diagnostics.txt path/to/test.json
```

`--snapshot` requires `--update` and exactly one spec. Other snapshot steps still compare normally. Updates remain staged until every step and process cleanup succeeds, so a later failure does not commit a partial baseline change.

Review the resulting file before committing it. Confirm that it contains the intended screen and no secret, personal path, credential, or sensitive application output.

Then rerun without update:

```text
playtestr test path/to/test.json
```

## Read a mismatch

A changed snapshot exits 1, prints a bounded unified diff, and writes:

- `<spec>.actual.txt`, the rendered failure screen;
- `<spec>.diff.txt`, the expected/actual text diff.

The `-` lines are from the reviewed baseline and the `+` lines are from the current screen. Diagnose whether the application, test steps, starting state, or terminal rendering changed before accepting anything.

An old adjacent evidence file can remain after a later passing run. Use the latest command status or machine report as the current outcome, inspect old evidence for sensitive content, and remove it explicitly when it is no longer useful.

Screen normalization preserves leading spaces and internal blank lines while trimming trailing spaces and unused terminal rows. Precise grapheme, emoji, combining-mark, and East Asian wide-character layout is outside the current contract; see [Terminal compatibility](terminal-compatibility.md).
