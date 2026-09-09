# September 2026 evidence ledger

Status: rc.2 publication and native install evidence complete; candidate real-app and independent-participant gates partially complete. Updated 10 September 2026.

This ledger separates historical release evidence, exploratory trials, final samples, focused diagnoses, candidate-byte evidence, and adoption gates. Private reports and resource identifiers remain under ignored `.trial-private/`; this file records sanitized outcomes.

## Proven evidence

| Evidence | Build boundary | Result |
| --- | --- | --- |
| Historical primary sample | Windows rc.1; Linux checkout at base `a64af217fb4807894ea1392b238ced31eec18bd8` plus Unix PTY patch | 60/60 final primary attempts passed across Lazygit, Lazydocker, and K9s. Four earlier Windows Lazydocker primary attempts failed and remain separate. |
| Unix controlling terminal | Published rc.2 Linux/macOS archives | Real `/dev/tty` target passed in native packaging run 34333242993 and public install run 34333615063. |
| Lazygit modal lifecycle | Checkout-built Linux runner | Minimized 17-step help/resize flow uses `expect_not` after each close and exits zero. |
| Lazydocker stopped/start | Checkout-built Linux runner; dedicated container | Stop produced exact exit 137. Start removed stale `exited` state; exact-ID oracle observed `running` and a changed start timestamp. |
| Lazydocker compact help | Checkout-built Linux runner; pinned v0.25.2 | Direct PTY menu opens after live resize, but the automated compact sequence receives a transient menu followed by a replacing repaint. Accepted only as an 80x24 post-resize-help exclusion. |
| Failure evidence retention | Published rc.2 source | Deterministic target clears its alternate screen during shutdown; the failure artifact preserves the useful pre-cleanup screen. |
| Combined trial status | Published rc.2 source plus PowerShell harness | A passing terminal run paired with oracle exit 7 fails overall and preserves both results; corrected oracle recovers to a pass. |
| Application regression | Pinned Lazygit `c07f4d381b90419583b7ce04f87379654d983ebc`, Windows | Same spec passed an unmodified source build, failed a launched synthetic help-title mutation at the intended assertion, then passed the restored control. |
| Non-Go technical flow | IPython 8.27.0, Python 3.12.7, Windows | Real prompt wrote an exact UTF-8 file. An intentionally wrong external oracle failed overall; the correct oracle passed. |
| Candidate Windows Lazygit | Downloaded rc.2 Windows archive | 10/10 staging attempts passed, each with exact `git diff --cached --name-only == alpha.txt`, followed by index reset. |
| Candidate Linux Lazygit | Downloaded rc.2 Linux archive | 10/10 staging attempts passed with exact index oracles; stage/unstage, commit, branch, synchronized help/resize, and a second session also passed. |
| Candidate Windows Lazydocker | Downloaded rc.2 Windows archive | 10/10 log attempts passed against the exact labeled fixture with a separate oracle. |
| Candidate release boundaries | Downloaded rc.2 Windows and Linux archives | Natural exit, signal cancellation with runner exit 130, total timeout, output cap, and descendant cleanup produced the expected result and cleanup evidence on both hosts. |
| Harness privacy | Repository state | `approvedreposlist.txt` and `.trial-private/` are ignored. Public recipes contain no approval identities, credentials, personal paths, raw dashboard screens, or resource IDs. |

## Candidate provenance

- Release: [`v0.1.0-rc.2`](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.1.0-rc.2)
- Source: `583352ad381df15f0fda652dae9ef819f5f24c9a`
- Packaging: [run 34333242993](https://github.com/Wyrcan-io/playtestr/actions/runs/34333242993), all native jobs passed
- Public installation: [run 34333615063](https://github.com/Wyrcan-io/playtestr/actions/runs/34333615063), all native jobs passed with controlling-terminal verification enabled
- Archive hashes: Linux `207fe229239b4146b4eba8734c50f39b33c1e9b6b190dbcb5a7ab3297db83576`; macOS `bfc5be4c9ac2a11a17a2ab6104f2a0ac6456af676a135d4f30a334bf626c9c8d`; Windows `34585eacb405d15139b2b90338239240f77e8ff663b83d56ce98f8d8ed27c8e9`

The public archives matched workflow artifacts byte-for-byte and their extracted binaries reported the expected version.

## Claims reconciled

- LG-01 independently proved staging only `alpha.txt`; a lock experiment proved a screen-only false pass. A distinct unstage scenario was not executed and is not claimed.
- Historical attempts did not create per-attempt oracle files retrospectively. Candidate Windows repetitions do have one oracle per mutating attempt.
- Candidate repetitions currently total 30/30 completed primary attempts: Windows and Linux Lazygit plus Windows Lazydocker. This number is not added to or substituted for the historical 60/60.
- The candidate Lazydocker lifecycle rerun is a setup failure: Lazydocker displayed that the Docker named pipe did not exist. Initial Linux Lazygit attempts interrupted by restricted WSL access remain separate; the elevated read-only/run path later completed that cell.
- The first Linux candidate commit attempt passed every screen step but did not create a commit; the next retained attempt committed a duplicated persisted draft. Clearing the target field and asserting modal disappearance produced exactly `trial commit` with only `alpha.txt` changed. These failures reinforce the independent-oracle requirement.
- Lazygit has a named second-session sample on both hosts. No candidate K9s cell, Linux Lazydocker cell, Windows Lazydocker second session, or participant-owned CI integration has been completed.
- Git, Docker, and Kubernetes postconditions are harness or operator checks, not Playtestr core assertions.
- The install-smoke sentinel proves the `go` lookup used by its shell is blocked. It does not prove the hosted image has no Go binary elsewhere.

## Remaining gates

| Gate | Current state | Required closure |
| --- | --- | --- |
| Candidate real-app matrix | Windows/Linux Lazygit and Windows Lazydocker primary repetitions complete; Lazydocker Linux and K9s Windows/Linux remain | Run downloaded rc.2 on isolated healthy Docker/Kubernetes infrastructure and preserve per-attempt oracles and exact cleanup |
| Candidate Docker cleanup | Docker daemon unavailable; the exact candidate fixture identity is retained privately | When the daemon returns, verify the recorded ID, name, and two ownership labels, then remove only that ID and confirm absence |
| macOS real-app coverage | Only fixtures, packaging, and published install have run | Keep real-app claims absent unless exact macOS target flows execute |
| Independent R3 adoption | No qualifying review, reuse, or participant-CI records supplied | Three reviews across two stacks, two voluntary second uses, and one project CI integration |

Do not promote historical or source-built evidence to candidate evidence. Every future published-binary result must name the tag, source commit, archive SHA-256, host, scenario, runner report, external oracle where applicable, and cleanup outcome.
