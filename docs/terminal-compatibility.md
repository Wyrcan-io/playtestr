# Terminal compatibility

Status: evaluated with MVP fixtures and the September 2026 real-application trial.

Playtestr compares normalized text from a fixed terminal viewport. It preserves leading spaces and internal blank lines, trims trailing spaces and unused rows, and deliberately excludes colors and other cell styles from snapshots.

## Exercised behavior

The focused parser and real-PTY fixtures cover:

- carriage-return redraws, cursor movement, screen clearing, and line erasing;
- ANSI control sequences divided across multiple writes;
- valid UTF-8 code points divided across PTY reads;
- basic non-ASCII text;
- alternate-screen entry, rendering, exit, and main-screen restoration;
- viewport growth and shrinkage propagated to both the PTY and emulator.

The current vt10x emulator retains control-sequence parser state between writes. Its direct `Write` API does not retain an incomplete UTF-8 rune, so Playtestr supplies that missing buffering at the internal emulator boundary. These fixtures make the current dependency sufficient for the MVP screen contract, while the dependency remains replaceable behind the terminal session.

## Known limits

The [historical E3 investigation](validation/e3-fidelity-boundary-2026-09-27.md)
records the old wide/combining cursor gaps retained in rc.2. Verified
[v0.4.0-rc.3](releases/v0.4.0-rc.3.md) corrects the selected East Asian
Wide/Fullwidth two-column cells behind a locally maintained vt10x adapter.
[Release evidence](validation/wide-character-release-2026-10-01.md) covers the
original MICRO-08 rendered interaction and independent saved-file oracle,
cursor addressing, paired overwrite/erase, wrapping, split UTF-8, resize
cropping and alternate-screen behavior on the three recorded native hosts.
Three affected television baselines were individually reviewed; old evidence
and published rc.2 bytes remain unchanged.

Ambiguous characters remain one column; resize does not reflow text. Combining
clusters, variation selectors, emoji/ZWJ sequences and terminal-specific width
settings remain unsupported. Terminal replies are discarded; query-dependent
tasks and bracketed-paste behavior remain outside the supported contract.
Selected two-column evidence is not general grapheme or universal Unicode support.

Current source synchronizes Windows resize with ConPTY's matching
`CSI 8;height;width t` output before sending the next input. The wait shares the
step deadline. A console backend that does not emit this confirmation produces
a bounded resize failure; older Windows implementations have not been qualified
for this new path. This transport observation does not answer terminal queries
or enable application-directed window manipulation.

The fixtures do not establish support for every VT control sequence, device query, mouse protocol, hyperlink, image protocol, color, style, or application-specific terminal extension. Snapshot comparison is text-only. Compatibility with a particular TUI requires exercising that application on the claimed operating system; cross-compilation alone is not runtime evidence.

The real-application trial added a Unix requirement that the fixture suite had missed: some TUIs open `/dev/tty` instead of using only inherited standard streams. Current source starts the target in a new session and assigns the PTY slave as its controlling terminal. The published `v0.1.0-rc.1` Linux asset predates that fix. The stable v0.1.0 Linux and macOS archives passed the real `/dev/tty` package gate and the post-publication downloaded-asset install smoke. Every later stable archive must pass the same gates before support is recorded.
