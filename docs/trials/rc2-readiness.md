# v0.1.0-rc.2 readiness record

Status: candidate published and native install gates complete; R4 entry held by incomplete candidate real-application cells and independent-participant gates. Updated 10 September 2026. Release owner: Wyrcan-io repository owner.

## Candidate identity

- Tag: [`v0.1.0-rc.2`](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.1.0-rc.2)
- Source commit: `583352ad381df15f0fda652dae9ef819f5f24c9a`
- Native packaging: [run 34333242993](https://github.com/Wyrcan-io/playtestr/actions/runs/34333242993), passed on Linux amd64, macOS arm64, and Windows amd64
- Public install: [run 34333615063](https://github.com/Wyrcan-io/playtestr/actions/runs/34333615063), passed on all three hosts with `/dev/tty` verification enabled

| Archive | SHA-256 |
| --- | --- |
| Linux amd64 | `207fe229239b4146b4eba8734c50f39b33c1e9b6b190dbcb5a7ab3297db83576` |
| macOS arm64 | `bfc5be4c9ac2a11a17a2ab6104f2a0ac6456af676a135d4f30a334bf626c9c8d` |
| Windows amd64 | `34585eacb405d15139b2b90338239240f77e8ff663b83d56ce98f8d8ed27c8e9` |

Public downloads matched the workflow artifacts byte-for-byte and reported `playtestr v0.1.0-rc.2` after extraction.

## Finding dispositions

| Finding | Candidate evidence | Disposition |
| --- | --- | --- |
| T01 controlling terminal | Extracted and publicly downloaded Linux/macOS assets passed the real `/dev/tty` fixture | Fixed and verified in candidate bytes |
| T02 external state | Combined harness fails when a screen pass is paired with oracle exit 7 and recovers with the correct oracle | Fixed in trial harness |
| T03 dashboard privacy | Public recipes require owned resources and sanitize evidence; private dashboard output remains ignored | Accepted process control |
| T04 Lazygit help/resize/quit | Downloaded rc.2 Linux asset passed the full synchronized real-app flow | Fixed and verified in candidate bytes |
| T05 negative evidence | Failure screen is captured before cleanup; deterministic regression passes | Runner fixed; target-supplied blank diagnostics accepted as a target limitation |
| T06 Docker integration | Endpoint preflight fails without fallback; current daemon outage is recorded as setup failure | Accepted process control; local infrastructure unavailable |
| T07 Lazydocker stopped/start | Checkout-built Linux exact-ID flow passed with changed `StartedAt` | Recipe fixed; candidate lifecycle rerun interrupted by daemon loss |
| T08 compact help | Lazydocker v0.25.2 Linux help after live resize to 80x24 | Demonstrated limitation excluded from supported scope |
| T09 persisted commit draft | Two candidate screen-pass/oracle-fail attempts retained; clearing input and proving modal closure produced the exact commit and tree | Fixed in candidate recipe; external Git oracle remains mandatory |

## Candidate scenario evidence

| Scenario | Evidence | Result |
| --- | --- | --- |
| Native installation and `/dev/tty` | Public install run 34333615063 | 3/3 hosts passed |
| Windows and Linux release boundaries | Downloaded rc.2: natural exit, signal cancellation, total timeout, output cap, descendant cleanup | 5/5 passed per host with expected statuses and cleanup evidence |
| Windows Lazygit primary | Downloaded rc.2, exact staged-file oracle per attempt | 10/10 passed |
| Windows Lazydocker logs | Downloaded rc.2, exact owned-container oracle per attempt | 10/10 passed |
| Windows Lazydocker lifecycle | Stop/start/restart attempt | Setup failure: Docker named pipe disappeared before the action; not counted as a product result |
| Linux Lazygit primary | Downloaded rc.2, exact staged-file oracle per attempt | 10/10 passed |
| Linux Lazygit broader flow | Stage/unstage, commit, branch, and synchronized help/resize with Git oracles | 4/4 passed; earlier oracle failures retained separately |
| Lazygit second sessions | One reset-and-rerun session on Windows and Linux | 2/2 hosts passed |
| Candidate Lazydocker Linux and K9s | No safe daemon or cluster access after Docker loss | Unexecuted |
| Application-regression value | Pinned Lazygit good/mutated/restored experiment | Complete technical evidence |
| Cross-language flow | IPython 8.27.0 file write with failed and recovered oracle | Complete technical evidence |

The candidate sample stays separate from the historical 60/60 technical campaign. It is currently 30/30 across the three completed repeated cells; no denominator includes setup-interrupted or unexecuted cells.

## R4 blockers

- Complete the downloaded rc.2 Lazydocker Linux and K9s Windows/Linux cells when isolated Docker/Kubernetes infrastructure is available; complete the Windows Lazydocker second session then.
- Verify and remove the recorded candidate Lazydocker fixture by exact ID and ownership labels when Docker becomes available.
- Obtain three qualifying independent project reviews across at least two stacks.
- Record two voluntary second uses and one integration in a participant project's CI.

Stable release work must not start from this record yet. Restarting Docker Desktop was deliberately avoided because it could affect unrelated containers; the outage was not bypassed through an ambient endpoint. WSL access recovered when the read-only run used the required sandbox permission, and its Lazygit and release-fixture cells completed. Human adoption gates cannot be replaced by operator repetitions or inferred from private permission records.
