# September 2026 evidence ledger

Status: source-level follow-up complete; published candidate and independent-participant evidence pending. Updated 9 September 2026.

This ledger separates historical release evidence, exploratory trials, final samples, focused diagnoses, and adoption gates. Private reports and resource identifiers remain under ignored `.trial-private/`; this file records only sanitized outcomes.

## Proven evidence

| Evidence | Build boundary | Result |
| --- | --- | --- |
| Historical primary sample | Windows rc.1; Linux checkout at base `a64af217fb4807894ea1392b238ced31eec18bd8` plus Unix PTY patch | 60/60 final primary attempts passed across Lazygit, Lazydocker, and K9s. Four earlier Windows Lazydocker primary attempts failed and remain separate. |
| Unix controlling terminal | Checkout-built Linux runner | Real PTY target opened `/dev/tty`; regression fails without `Setctty`/`Ctty` and passes with it. Published rc.1 remains defective. |
| Lazygit modal lifecycle | Checkout-built Linux runner | Minimized 17-step help/resize flow uses `expect_not` after each close and exits zero. |
| Lazydocker stopped/start | Checkout-built Linux runner; dedicated container | Stop produced exact exit 137. Start removed stale `exited` state; exact-ID oracle observed `running` and a changed start timestamp. |
| Lazydocker compact help | Checkout-built Linux runner; pinned v0.25.2 | Direct PTY menu opens after live resize, but the automated compact sequence receives a transient menu followed by a replacing repaint. Accepted only as an 80x24 post-resize-help exclusion. |
| Failure evidence retention | Current source | Deterministic target clears its alternate screen during shutdown; the failure artifact preserves the useful pre-cleanup screen. |
| Combined trial status | Current source plus PowerShell harness | A passing terminal run paired with oracle exit 7 fails overall and preserves both results; corrected oracle recovers to a pass. |
| Application regression | Pinned Lazygit `c07f4d381b90419583b7ce04f87379654d983ebc`, Windows | Same spec passed an unmodified source build, failed a launched synthetic help-title mutation at the intended assertion, then passed the restored control. The source file hash was restored. |
| Non-Go technical flow | IPython 8.27.0, Python 3.12.7, Windows | Real prompt wrote an exact UTF-8 file. An intentionally wrong external oracle failed overall; the correct oracle passed. This is stack diversity, not independent adoption. |
| Harness privacy | Repository state | `approvedreposlist.txt` and `.trial-private/` are ignored. Public recipes contain placeholders and no approval identities, credentials, personal paths, raw dashboard screens, or resource IDs. |

## Historical claims reconciled

- LG-01 independently proved staging only `alpha.txt`; an index-lock experiment proved a screen-only false pass. A distinct unstage scenario was not executed and is not claimed.
- The primary ten-run cells are preserved, but per-attempt external-oracle files were not created retrospectively. Candidate repetitions must record an oracle for every mutating attempt.
- The campaign exercised cancellation, cleanup, readiness waits, retained-log faults, and setup interruption in separate scenarios. No campaign-specific output-flood artifact or named second-session sample exists; release fixtures cover output flood and lifecycle behavior, while candidate real-app second sessions remain pending.
- Git, Docker, and Kubernetes state checks were operator-run private evidence. They are not Playtestr core assertions.
- Linux real-app success applies to a checkout build. No published Linux archive containing the fix has been tested yet.
- The install-smoke sentinel proves the `go` lookup used by its shell is blocked. It does not prove the hosted image has no Go binary elsewhere.

## Pending evidence

| Gate | Why pending | Required closure |
| --- | --- | --- |
| Hosted rc.1 install smoke | Complete at workflow commit `9cf00e89f378703d66b6bc05978777c6dc8e2ec1` | [Run 34332701717](https://github.com/Wyrcan-io/playtestr/actions/runs/34332701717) passed all three hosts with controlling-terminal verification disabled only for rc.1. Failed Windows fixture attempts [34331624815](https://github.com/Wyrcan-io/playtestr/actions/runs/34331624815), [34331960179](https://github.com/Wyrcan-io/playtestr/actions/runs/34331960179), and [34332334639](https://github.com/Wyrcan-io/playtestr/actions/runs/34332334639) remain retained. |
| Published next candidate | No immutable asset contains the current patch | Package, publish, download, checksum, and run native assets with `/dev/tty` enabled. |
| Candidate real-app matrix | Existing Linux evidence is checkout-built | Run supported Lazygit/Lazydocker/K9s paths and fresh repetitions from downloaded bytes. |
| macOS real-app coverage | Only fixtures and release packaging have run | Keep real-app claims absent unless exact macOS target flows execute. |
| Independent R3 adoption | Technical operator work cannot substitute for participants | Three completed project trials across two stacks, reviewed failure evidence, two voluntary second uses, and one project CI integration. |

## Source provenance before candidate freeze

- Base commit: `a64af217fb4807894ea1392b238ced31eec18bd8`.
- Source commits through the successful rc.1 install proof: runner `eedd456`, evidence/harness `7927c7f`, release gates `a1501f6`, cleanup correction `6c378a5`, and hosted fixture corrections through `9cf00e8`.
- Trial target versions and original release hashes: [`trials/manifest.json`](../../trials/manifest.json).
- Reproduction requirements: [`trials/recipes.md`](../../trials/recipes.md).

Do not promote historical or source-built evidence to candidate evidence. Every published-binary result must name the tag, source commit, archive SHA-256, host, scenario, runner report, external oracle where applicable, and cleanup outcome.
