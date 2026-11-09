# mg pre-acquisition review v1

Status: primary-source review completed before acquisition; the exact pin has since
been acquired and hashed as recorded in `source-provenance.json`. It is not yet
built or behavior-tested. No admission credit. Review performed against the canonical GitHub repository at commit
`2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66` using its pinned README, `UNLICENSE`,
`configure.ac`, `Makefile.am`, `src/Makefile.am`, `src/main.c`, `src/file.c`,
`src/fileio.c`, `src/basic.c`, `src/buffer.c`, `src/undo.c`, and
`.github/workflows/build.yml`.

## Identity and compatibility

- Canonical project: `troglobit/mg`, Micro (GNU) Emacs, C, terminal full-screen
  editor; distinct application and editing workflow.
- Selected commit: `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`.
- License: repository `UNLICENSE`; the pinned file dedicates copyright to the
  public domain and grants use, modification, distribution, and sale.
- README at this pin reports macOS 10.10+ and multiple Unix systems. The upstream
  workflow builds Ubuntu Linux and Windows MSYS2, but does not test macOS.
  Campaign admission must therefore rely on our exact native Linux/macOS jobs,
  not that workflow's matrix.
- The README says release tarballs include `configure`; a GitHub commit archive
  needs `./autogen.sh` (`autoreconf -W portability -visfm`) before configure.
  Use a bounded source build and record the actual autotools/compiler versions.
  The default build uses termcap/curses when available and can use its own ANSI
  backend with `--without-curses`.

## Hooks, files and process scope

- Build hooks are Autoconf/Automake generation, `configure`, and `make`; review
  and execute only at the pinned source in the isolated active target. Do not
  run upstream `make install` with its documented `/usr/local` default. If an
  install route is needed, set every prefix/data/doc/sysconf destination inside
  the owned target and verify the resulting file inventory.
- `Makefile.am`'s `package` target invokes `debuild`; it is outside the test path.
  The upstream CI also installs system packages; do not copy that privileged
  setup into our workflows.
- The application opens and saves named files and can start shell/program
  commands through editor features. Run only against synthetic files in an
  owned workspace with isolated HOME/XDG/temp paths. Start with `-S` to disable
  startup files and external-program commands, and `-n` to disable backups.
  Do not assume `-s` is suitable for save-as cases: its source restricts file
  access to command-line paths.
- No host configuration, user repositories, network services, real secrets,
  privileged installation, or upstream outreach is in scope.

## Acquisition and resource gate

Checkpoint v44 recorded 36,503,264 logical retained bytes of shared headroom.
The pinned source was subsequently acquired successfully (1,349,286 expanded bytes,
126 source files, archive SHA-256 `bd8aff8ddbf55f7d37067a9f01e6bef887a2b0f2c0699aaa08a73d7dfd6069a8`).
The latest local storage observation after acquisition passes all caps and records
36,498,217 bytes of combined retained headroom. Forecast at most 24 MiB for mg's
complete project evidence; remeasure after each retained packet and do not begin
another project without its own bounded forecast. The active source tree does not
count as retained evidence or as project admission.

Before any future acquisition, bind the downloaded archive to this commit, check
its license and hooks against the retained screening record, keep compressed
source at or below 8 MiB and expanded source at or below 64 MiB, and enforce the
20-minute acquisition/build ceiling. Stop and record a zero-credit rejection if
the ceiling is exceeded.

## Scenario and fault feasibility draft

Proposed public workflow: launch the pinned editor in a real PTY, edit synthetic
files using normal Emacs key sequences, assert the visible buffer/prompt and
save result, then exit. Exercise the public spec/snapshot route for each frozen
scenario. Oracle data will be generated independently from expected file bytes
and explicit screen anchors; editor exit status alone is insufficient.

The 20-case draft has eight normal journeys (create/save, open/edit/save,
multiline insertion, search, region cut/yank, undo/redo, buffer switching, and
Unicode text) and twelve edge journeys (empty/missing files, EOF and beginning
boundaries, long lines, wide Unicode, overwrite confirmation/decline, read-only
files, save-as spaces, cancelled prompts, invalid input, resize/redraw, and
expected nonzero launch/exit). Final cases require inspection against the exact
acquired source and pilot evidence before freezing.

Potential safe fault sites, subject to exact-source review and baseline-first
verification, are saved-buffer persistence (`filesave`/`buffsave`), line-boundary
editing (`backdel`/`forwdel`), and undo restoration (`undo`). Each mutation must
be minimal, local to the owned synthetic workspace, produce an observed failure,
and be restored byte-for-byte before another fault. These are feasibility
hypotheses, not confirmed defects or completed fault credit.

## Next step

Continue campaign-wide retention compaction and measure the space it actually
recovers. Reassess the candidate forecast against exact evidence sizes before
creating `mg/source-provenance.json` or running `next20_acquire.py mg`.
