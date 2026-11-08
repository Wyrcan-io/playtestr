# Taskell macOS LLVM runtime closure investigation

Status: implementation prepared locally; no MacPorts package has yet been
downloaded or verified by the hosted workflow. This is not a claim that the
Apple Silicon GHC toolchain now launches successfully.

The preserved macOS loader diagnostic reported missing MacPorts `libxml2.16`
and `libz.1` dylibs while starting the pinned LLVM 12 `opt`/`llc`. Primary
MacPorts source shows libxml2 2.15.4 revision 0 is MIT licensed, has upstream
source SHA-256
`98087fd181d9070724f3fbc65c7377db03038eb92bd882374daff44940138821`, and is
built with ICU and zlib while depending on libiconv. zlib 1.3.2 revision 0 is
zlib licensed and has upstream source SHA-256
`d7a0654783a4da529d1bb793b7ad9c3318020af77667bcae35f95d0e42a792f3`. The MacPorts
ICU 78.3 revision 1 source hash is
`3a2e7a47604ba702f345878308e6fefeca612ee895cf4a5f222e7955fabfe0c0`; libiconv
1.19 revision 0 source hash is
`88dd96a8c0464eca144fc791ae60cd31cd8ee78321e67397e25fc095c4a19aa6`.

Sources reviewed:

- [MacPorts libxml2 Portfile](https://github.com/macports/macports-ports/blob/master/textproc/libxml2/Portfile)
- [MacPorts zlib Portfile](https://github.com/macports/macports-ports/blob/master/archivers/zlib/Portfile)
- [MacPorts ICU Portfile](https://github.com/macports/macports-ports/blob/master/devel/icu/Portfile)
- [MacPorts libiconv Portfile](https://github.com/macports/macports-ports/blob/master/textproc/libiconv/Portfile)
- [Signed libxml2 binary package index](https://packages.macports.org/libxml2/)
- [Signed zlib binary package index](https://packages.macports.org/zlib/)
- [Signed ICU binary package index](https://packages.macports.org/icu/)
- [Signed libiconv binary package index](https://packages.macports.org/libiconv/)
- [GNU libiconv and libcharset upstream](https://www.gnu.org/software/libiconv/)

The local helper now fetches exact darwin 24 arm64 packages and their detached
signify signatures; verifies each against the already pinned MacPorts archive
key; extracts only bounded matching dylib families beneath the owned toolchain
root; records package, signature, source, and selected-file identities; and
walks actual `otool -L` dependencies. ICU has a larger explicit 512 MiB archive
expansion bound and 128 MiB selected-library bound. No installer, package hook,
or global MacPorts installation runs. Unit fixtures cover the libxml2 → ICU,
zlib, and libiconv relationships, family selection, static-file exclusion, and
missing dependency refusal, including the libiconv -> libcharset link.

The first new archive-family fixture reused one archive pathname for two
packages, so the libxml2 extraction test read the later zlib fixture and failed;
the test helper was corrected to use distinct archive names. A separate initial
test command ran from the repository root instead of `scripts/acceptance` and
failed module discovery before importing any tests. The corrected scoped suite
ran 14 tests successfully with two expected Windows symlink-capability skips;
Python compilation and `git diff --check` also passed.

The final check remains the actual hosted macOS run: independently verify all
signatures and selected bytes; inspect `otool -L` recursively for every loaded
owned dependency; check `opt --version` and `llc --version` including the AArch64
backend; then run Taskell's pinned tests and candidate scenarios. Any newly
revealed dependency must be researched and bounded before changing the closure.
The Linux E11M viewport-sensitive failure remains independent and unaltered.

The Taskell exact-candidate workflows now also preserve a SHA-256-checked copy
of the built executable before teardown, verify native process absence and
source ownership, inventory Stack's generated `.stack-work` tree with per-file
hashes and explicit bounds, remove only that generated tree, bind Hpack's
generated `taskell.cabal` separately, and invoke the general checked target
cleanup. A common concurrency group prevents Taskell's ordinary and fault
workflows from concurrently mutating the same owned target root. The Linux and
macOS workflow steps include this preparation evidence in their retained
artifact. These cleanup changes have only local unit/preflight evidence so far;
the next hosted Taskell execution must prove the platform behavior. They do not
resolve the LLVM loader issue or the independent Linux viewport miss.

The expanded focused local suite ran 23 tests: 19 passed and four native
symlink-capability checks were skipped on this Windows host. The two Windows
junction scenarios ran and passed. Python compilation and `git diff --check`
passed. No Taskell host was started by this local check.
