# JOE source preflight review v1

- Canonical upstream: `joe-editor/joe`, pinned at `3874898078005d1f5e519235401fab4fd428dd9b`; GNU GPL version 2, verified from the pinned README and `COPYING`.
- The pinned README describes a C terminal screen editor with its own terminal control code, custom termcap/terminfo support, multiple editor variants, prompt completion, undo/redo, UTF-8 support, file history/state, and shell windows. The latter are execution surfaces; tests will use reviewed deterministic edits only and will not invoke shell windows or `!command` filenames.
- Pinned INSTALL instructions use `./configure`, `make`, and `make install`; macOS notes require `LC_ALL=C` during install due to a documented `sed` issue. Install prefix, HOME, TMP and all generated files will be campaign-owned. No administrator install or network-dependent target action is planned.
- Initial native allocation is Linux plus macOS as declared in the selected row. Windows-specific tips exist upstream, but no Windows cell is planned for this project.
- Target scenarios will exercise keyboard-driven editing, prompts, saves, recovery and UTF-8 only. Do not use JOE's shell command, pipe/filename, spell-check, compile, grep/find, or pop-up shell features. Keep target data synthetic and isolated.
- Before build execution, inspect the exact acquired archive's `configure`, `Makefile.in`, generated source/build inputs and installation scripts, and record all external commands, downloads, writes and environment access. Refuse any unexpected network, privileged or out-of-root side effect.
- No source/build command or application process ran during this initial remote-source review.
