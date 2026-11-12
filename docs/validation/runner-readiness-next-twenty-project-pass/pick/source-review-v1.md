# Pick pinned-source review v1

## Identity and primary evidence

- Canonical upstream: [`mptre/pick`](https://github.com/mptre/pick)
- Reviewed source pin: `caae95938359b2e814b3e7406f396f486c9d99fb`
- Language and terminal stack: C with curses/terminfo; fuzzy list selection reads choices from standard input and returns the selected line on standard output.
- License: MIT, verified from [`LICENSE` at the pinned source](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/LICENSE).
- Primary behavior and install docs: [`README.md` at the pinned source](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/README.md) and [`pick(1)`](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/pick.1).
- Build/test sources reviewed: [`Makefile`](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/Makefile), [`configure`](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/configure), [`tests/t.sh`](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/tests/t.sh), and [`tests/pty.c`](https://github.com/mptre/pick/blob/caae95938359b2e814b3e7406f396f486c9d99fb/pty.c).

## Build and execution boundary

The documented build is `./configure` then `make`; the tracked `GNUmakefile` provides GNU make compatibility for the BSD-style makefile. `configure` performs bounded compiler/link probes for curses, optional compatibility APIs, and writes only `config.h`, `config.mk`, and `config.log` in the source tree. It uses `mktemp` for one temporary probe. The reviewed build has no download, package-install, privilege, or service hook. The pinned application requires a working C compiler, GNU make, and a native curses/terminfo development library.

The upstream test target builds `pick` and a PTY test helper, then runs the pinned shell test cases. The helper opens a real PTY, makes it the child controlling terminal, feeds reviewed key sequences, and waits for the child. Tests create temporary files with `mktemp`, compare output, and remove their own paths. Campaign runs will direct `TMPDIR` to an owned campaign directory, cap process time/output, and retain exact test logs. The target has no network or live-service requirement.

The public usage intentionally supplies choices as a data stream and uses the controlling terminal for interactive keys. In scenarios the launch adapter will use the documented shell redirection form (`exec pick < choices.txt`) so `pick` itself replaces the shell and reads a frozen workspace fixture on standard input while obtaining keystrokes from its controlling PTY. The shell performs only this ordinary stream-redirection plumbing; it contains no assertions or target behavior. The test oracle is the selected line visibly emitted by `pick` on the PTY after curses teardown. Pick does not persist application state, so it contributes no saved-file-state coverage.

Linux and macOS are selected native hosts according to the screening and compatibility declarations. The exact archive, actual native build dependencies, and target runtime identities are recorded after acquisition; this review does not claim that either host has built or run yet.
