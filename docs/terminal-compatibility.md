# Terminal compatibility

Status: evaluated for the Sprint 3 MVP fixtures on Windows, September 6, 2026.

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

vt10x models one Go rune as one terminal cell. It does not provide complete `wcwidth`, grapheme-cluster, combining-mark, emoji-sequence, or East Asian wide-character layout. Snapshots containing those characters may have incorrect column alignment even when the text survives. Basic Unicode code points are supported by the exercised contract; precise complex-Unicode layout is not yet supported.

The fixtures do not establish support for every VT control sequence, device query, mouse protocol, hyperlink, image protocol, color, style, or application-specific terminal extension. Snapshot comparison is text-only. Compatibility with a particular TUI requires exercising that application on the claimed operating system; cross-compilation alone is not runtime evidence.
