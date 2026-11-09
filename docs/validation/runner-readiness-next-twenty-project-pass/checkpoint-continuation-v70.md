# Continuation checkpoint v70

## Current project count

Five of twenty new projects are admitted for the current candidate; fifteen of
thirty overall are credited. The historical ten remain at zero current-candidate
requalification. mg is acquired with zero scenario, fault and admission credit.

## Run 42704599164 on commit 5797bd2

Linux passed. macOS passed the helper suite and pinned source acquisition but
failed during GNU M4's `make`: shipped generated `lib/config.hin` was considered
stale against an extracted input, and Make invoked `autoheader` before Autoconf
had been built. This followed the earlier `aclocal` regeneration failure.
Artifact 13713815718 is retained locally, has valid ZIP CRC and matches GitHub's
SHA-256 digest. Receipt `mg/native-macos-build-receipt-v4.json` records the
exact failure and evidence identity.

The new fix gives every regular file from each exact, hash-pinned GNU release
archive one shared timestamp immediately after safe extraction. Bytes and
permissions remain unchanged; build tools consume the mutually consistent
generated files shipped in that release instead of trying to regenerate them
with bootstrap tools that have not yet been built. A focused regression covers
the timestamp invariant. The full portable local helper suite passes (13 tests,
three POSIX-only tests skipped on Windows), and syntax, whitespace and campaign
storage checks pass. A new native run is needed to verify this fix and any later
toolchain stages before mg behavior work.

Latest local storage audit: combined raw 3,965,617,755 bytes and combined
retained 2,124,017,012 bytes; both are within the campaign limits. No target
scenarios, source faults or admission have been established.
