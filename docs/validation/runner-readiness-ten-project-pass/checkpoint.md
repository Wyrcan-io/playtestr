# Resume checkpoint

16 October, subsequent native/development checkpoint (source still unfrozen):
`e22c1b7` Terminal tests run `38917498568` passed Linux and macOS; Windows
failed the new cleanup test's short/long temporary-path comparison. The test now
canonicalizes both sides before checking ownership. Dedicated core run
`38917498609` bootstrapped all SDKs successfully, then failed: downloaded SDK
test sources were incorrectly included by `go test ./...`; Windows additionally
exposed installer long-path launch and share-mode calibration assumptions.
All three bounded packets (about 204 KiB compressed) were retrieved locally.
A campaign module boundary now excludes downloaded sources, with five evidence
tests passing (`e5cb67c81d5b4d0da3827c83b2687695`). Windows byte-range lock and
cleanup controls pass, with a real independently failing locked read. Share-mode
behavior on privileged hosted rooted opens remains unestablished; no blanket
sharing-lock claim is made. PowerShell 7 long-path launch correction awaits CI;
the installed PowerShell 5 route passed `707fc9ddc2eb410393b0b2a8a660ac30`.

Plop has nineteen distinct Windows development scenario passes: all eight normal
and eleven edges. Initial contract manifest is retained. E04's original Unix
exit-130 assumption failed on Windows with actual exit 1; only the host-specific
exit expectation changed, preserving every no-write/file assertion. E05 remains
red: second resize to 80x12 timed out at the current transport fence (attempt
`8b722a09bed74d3181c96eeed5583bb7`). No admission or final-series credit.
Independent edges E06-E12 passed under parent
`e9a643d6ed4d4e58a6bb78e32cb75a18`. Startup blank-screen timeouts reproduced
in shell/direct-Node forms, then later probes reached readiness quickly. A
synthetic real-ConPTY shell/Node/import probe passed; cause remains unknown.
Do not describe a green retry or larger diagnostic budget as its repair.

Next: corrective native run, reduce quiet repeated resize without regressing
historical wizard synchronization, then genuine Plop source faults, authoring
maintenance/relocation and native project checks. Plop remains the only active
application. The other nine projects, old migration, archives and final audit
remain open. Human usability remains unmeasured.

Stage B/C, 16 October 2026. Public v3 state assertions, recorder capture/selected
maintenance, report v3 and same-execution identities are implemented. Windows
full tests, vet and race passed before the latest recorder false-green repair;
those results do not qualify the newer repair. Source candidate remains unfrozen.

Thirty new pinned metadata records reviewed, ten provisional selections and five
reserves. Exactly one active target, Plop, acquired at its declared pin; owned
Yarn installation succeeded with scripts disabled. First public route exported
an input-only false green after several failed captures; independent admission
calibration rejected it. Preserve the original exported spec in local evidence.
Two reduced real-PTY regressions failed before and passed after the repair.
Latest repair also blocks unresolved control syntax failures. Repaired recorder
checks, full Windows Go tests and vet now pass. Native CI/race must requalify the
newer source; the earlier successful Windows race run predates this repair.

Plop's repaired prepared first-use route passed (three shell invocations, eleven
controls). All initial/diagnostic/repaired attempts total seven invocations and
twenty-eight controls, exceeding the original engineering target. All failures
and the original input-only export remain retained. No project admission follows.
Next: commit/push the public vertical slice, dispatch native core CI, and finish
Plop's twenty declared scenarios and genuine faults sequentially.

Original Plop startup timeout under concurrent race work remains unexplained;
later bounded shell/direct Node startup probes passed at three seconds, without
establishing a cause. Never call the original route a successful test.

Open gates: full R1 native controls, ten new project packages, old-project
migration, native matrix, historical investigation, private archives, final
repetitions and audit. Human usability unmeasured; publication not authorized.

GitHub authentication works outside the restricted command sandbox. The user
explicitly authorized scoped campaign commits/pushes and standard hosted workflow
execution after the initial permission question. Do not ask again. No new hosted
dispatch/result is claimed yet. No project is admitted; final/archive/migration
counts remain zero. Before dependency installation observed campaign storage was
166,626,448 bytes; Plop's installed active tree measured 399,321,279 bytes.
Reinventory before advancing; these are observations, not an exact peak/quota.
