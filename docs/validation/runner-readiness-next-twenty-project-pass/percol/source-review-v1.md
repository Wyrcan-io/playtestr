# Percol pinned-source screening review v1

## Identity and source evidence

- Canonical project: `mooz/percol` (`https://github.com/mooz/percol`).
- Selected pin: `4b28037e328da3d0fe8165c11b800cbaddcb525e` (default branch head;
  latest upstream commit dated 2019-07-23).
- Declared implementation: Python 2.x, version `0.2.1`.
- Upstream describes the application as an interactive Unix/POSIX line
  selector. Its setup classifier says `Operating System :: POSIX` and
  `Environment :: Console :: Curses`.
- Setup metadata declares MIT, and the pinned Debian package's
  `debian/copyright` carries the MIT grant and conditions for all project files.
  The repository root has no LICENSE/COPYING file; this less-visible license
  location must be checked in the acquired archive before executing its code.
- Primary pinned records reviewed: [README](https://github.com/mooz/percol/blob/4b28037e328da3d0fe8165c11b800cbaddcb525e/README.md),
  [setup.py](https://github.com/mooz/percol/blob/4b28037e328da3d0fe8165c11b800cbaddcb525e/setup.py),
  [debian/copyright](https://github.com/mooz/percol/blob/4b28037e328da3d0fe8165c11b800cbaddcb525e/debian/copyright),
  [CLI entry point](https://github.com/mooz/percol/blob/4b28037e328da3d0fe8165c11b800cbaddcb525e/bin/percol),
  and [finder implementation](https://github.com/mooz/percol/blob/4b28037e328da3d0fe8165c11b800cbaddcb525e/percol/finder.py).

## User-visible behavior

Percol reads candidates from standard input or a named file, renders an
interactive filter through curses, accepts a search query and selection keys,
then writes selected candidate lines to stdout. Its primary observable oracle
is exact output bytes plus the target exit code. It supports multi-selection,
regex matching and a configurable Python startup file under `~/.percol.d/rc.py`.
That configuration path provides meaningful file-state coverage if its
preservation and update behavior is verified against the actual pinned code.

## Native runtime risk and bounded feasibility gate

Upstream explicitly supports Python 2.x only. Python 2.7 is end-of-life and is
not assumed to be present on current hosted Linux/macOS runners. A native
feasibility attempt must therefore build an isolated CPython 2.7.18 runtime
from a checksum-verified source archive and exercise Percol's built-in string
finder with its `six` compatibility dependency. The pinned `setup.py` also
declares `cmigemo`; a narrow string-finder smoke must disclose that it did not
install or qualify Migemo/Pinyin instead of implying a complete package
installation. Do not use a container, WSL or cross-compiled runtime as native
PTY evidence. Bound the runtime build time, source/archive sizes, compiler
output, child processes and cleanup. If CPython 2.7 cannot build or run on
either standard host, retain the failure and replace Percol only through the
declared reserve and substitution process.

The initial macOS feasibility run found that CPython 2.7.18's generated
`configure` script rejects the current Apple Silicon `arch` output. The native
feasibility workflow applies a narrow, recorded build-only patch that maps
`arm64` to the host's native architecture. It leaves the signed source archive
unchanged and does not cross-compile or modify Percol. Any resulting evidence
will identify the patch and its digest, and will not be presented as upstream
CPython arm64 support.

The next native Mac build exposed CPython 2.7's `Python/` source directory and
`python` executable collision on the hosted runner's case-insensitive volume.
The follow-up uses a temporary case-sensitive APFS image on that same macOS
host and records the build logs, then detaches the image in an always-run
cleanup step. This preserves native macOS execution while addressing the
interpreter's source-tree layout requirement.

The pinned source archive checksum, exact 32-file tree manifest and MIT notice
hash are independently bound in `source-artifact-audit-v1.json`. The feasibility
runtime input is pinned `six==1.16.0`; this is not a full install of Percol's
declared `cmigemo` dependency. The screening review itself grants no scenario,
public-route or project-admission credit.
