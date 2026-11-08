# Continuation checkpoint v44: 8 November 2026

Branch `work/p0-p2-implementation` is pushed at `8909397b`. The exact rc.6
campaign ledger currently qualifies four of twenty new projects (14/30
cumulative); eight distinct projects have admissions on a candidate, but four
of those are rc.5 only and do not count toward the current candidate. The
original ten remain rc.5 carry-forward only. Do not report 30/30.

## Changes and local evidence since v43

- MacPorts LLVM archive layout was inspected after the signed package was
  rejected for its `opt` scaffolding and bounded launcher wrappers. The
  extractor now admits only the declared scaffold and small versioned wrappers.
- The macOS `opt --version` failure was instrumented to expose bounded captured
  stdout/stderr. Hosted evidence showed the signed LLVM archive requires
  `libffi.8.dylib`, absent from the hosted image and LLVM package.
- Added the separately signed Darwin 24 ARM64 MacPorts libffi 3.4.8 package.
  Its Ed25519 signature is verified before extraction; only the bounded
  `libffi` dylib family is selected into the campaign-owned LLVM prefix. The
  manifest records both archive hashes, signer identities, upstream tag/source
  hash, MIT license, selected dylib hashes, and the no-install-hook extraction
  scope. Archive paths use POSIX normalization on every host.
- Raised only the Windows synthetic staged-native acceptance test allowance
  from 30 to 120 seconds after its hosted execution timed out under load. The
  product script bounds are unchanged.

Local checks: `test_next20_*.py` passed 124 tests with eight documented
host-specific skips before the libffi additions; the refreshed LLVM helper
suite passed seven tests with one local Windows symlink-privilege skip. The
staged-native Windows test passed separately in 5.69 seconds. Python compilation
and `git diff --check` passed. The local Go standard library is incomplete, so
the Taskell Go Ed25519 test remains for hosted setup-go evidence.

## Hosted evidence and active work

- Git Town exact rc.6 run `42506300401` completed successfully on standard
  Ubuntu 24.04 and Windows 2025 runners. Both executed 240 ordinary cases and
  nine fault calibrations, restoring the target source and removing the owned
  runtime; Windows native removal was confirmed. This is a revalidation of an
  already admitted Git Town package, not an extra admission. Artifacts are
  `13628203307` (Linux) and `13628146068` (Windows); independent artifact audit
  remains in the final campaign work.
- Skim exact rc.6 run `42506300345` has Linux ordinary execution complete
  (240/240); both hosts are executing source-fault calibration/cleanup. Linux
  artifact `13628204007` is uploaded. No new Skim admission is recorded yet.
- Taskell run `42507408313` failed on both hosts: Linux's final series is a
  pre-libffi attempt; macOS captured the exact missing `libffi.8.dylib` error.
  Fault run `42507408450` also failed on macOS before calibrations and is still
  retained as a zero-credit attempt.
- Current Taskell final run `42508608826` is running at pushed source
  `8909397b`; Linux is running upstream Taskell tests and macOS is setting up
  the pinned Go verifier before signed LLVM/libffi acquisition. The matching
  source-fault run `42508608712` is queued. The shared harness `42508608863`
  passed all three native hosts.

Git Town, Skim and Taskell artifact contents, all failures, source/runtime
identities, and exact candidate archive hashes still need the independent
campaign audit before any new admission or refreshed receipt. The signed
libffi extraction is synthetic-tested locally; its real package layout and
LLVM load must pass on macOS before Taskell can earn credit.

## Workspace and next actions

The only untracked workspace paths observed are `.codex-go-cache/` and
`.codex-test-tmp/`; preserve them. No local target source/runtime or new raw
campaign packet is being retained. The last v43 storage checkpoint remains a
historical measurement, not current capacity evidence.

1. Monitor Taskell run `42508608826` through the MacPorts LLVM `opt` and `llc`
   probes, upstream test/build, 12 native batches, and checked cleanup. Inspect
   the actual failure output if any step fails.
2. Monitor queued Taskell fault run `42508608712`; require all baseline/mutated/
   restored phases and process cleanup on both Linux and macOS.
3. Finish Skim run `42506300345`, then independently audit its host packets,
   scenarios, faults, cleanup, and exact candidate before changing the ledger.
4. Continue the remaining selected projects and reserves, old-ten rc.6
   qualification, migration/regression gates, evidence tamper audit, storage
   accounting and fresh-checkout checks. None is implied complete by this
   checkpoint.
