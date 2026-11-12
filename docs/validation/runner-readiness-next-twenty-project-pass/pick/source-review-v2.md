# Pick pinned-source review v2: CRLF behavior

This supplement preserves [`source-review-v1.md`](source-review-v1.md) and its time-specific account of earlier attempts. It records one additional exact-source finding for immutable scenario contracts v6 and v7.

- Identity: `mptre/pick` commit `caae95938359b2e814b3e7406f396f486c9d99fb`; source archive SHA-256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`.
- The acquired, hash-verified `pick.c` reads input into a buffer and splits choices at `\n` (`get_choices`, pinned source line 226). It does not remove a preceding `\r`; choice length includes that byte.
- `print_line` writes the choice's bytes to curses output. A retained carriage return moves the terminal cursor to the beginning of the row, so the choice text can overwrite its own prefix. In hosted Linux v6 attempt `43322068022`, the CRLF fixture with `beta\r\n` and query `bet` rendered `eta`, not `beta`; the runner correctly timed out when the v6 contract asserted `beta`.
- Scenario v7 renames E07 to “Expose carriage-return effects in CRLF choice input” and asserts the pinned program's observed `eta` result. This is a target limitation, not evidence that Pick normalizes CRLF. The original timeout remains an immutable failed attempt and gets no admission credit.
- This is source analysis and local replay of retained source only. No upstream modification is made. Native confirmation under v7 is still required on both Linux and macOS before any qualification claim.
