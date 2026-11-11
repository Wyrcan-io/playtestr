# JOE source and build-hook review v2

Reviewed the exact extracted source for `joe-editor/joe@3874898078005d1f5e519235401fab4fd428dd9b`, after matching all 388 extracted file hashes to the hosted acquisition manifest. License is GPL-2.0.

The build requires Autoconf, Automake and a C compiler; the target describes libc as its only runtime dependency, with termcap/terminfo selected by configure. `configure.ac` contains compile/header/library probes and optional spell-checker detection, but no `AC_RUN`, network fetch, arbitrary configure command block, or privileged operation. The GitHub sync workflow uses curl, but it is not part of this local build and will not be executed.

`make install` installs into the owned staging prefix. Its variant-link hook removes/recreates only `joe`, `jmacs`, `jstar`, `rjoe`, and `jpico` names beneath the configured `DESTDIR` binary directory. The macOS install command uses `LC_ALL=C` per upstream instructions. We will verify resolved installation paths before running install.

JOE exposes `!command` filenames and shell windows and includes helper commands for them. They are intentionally outside the fixture route: frozen specs use ordinary owned file paths, keyboard input, save/readback and screen checks only. No real project, host files, spell checker, compiler, shell command or networked operation is used.

No build hook or application command ran during this static review. Exact hook hashes are in `source-hook-review-v1.json`.
