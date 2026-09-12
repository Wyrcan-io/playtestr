# v0.1.0-rc.2 readiness record

Status: candidate publication, native install gates, downloaded-binary release boundaries, the earlier six-cell matrix, and [R3c nine-application validation](cross-stack-validation-2026-09.md) are complete. Updated 12 September 2026. Independent adoption follows stable publication. Release owner: Wyrcan-io repository owner.

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
| T06 Docker integration | Endpoint preflight fails without fallback; interrupted attempts stayed classified as setup failures, then candidate trials resumed only after the verified endpoint returned | Accepted process control and verified recovery |
| T07 Lazydocker stopped/start | Downloaded rc.2 passed exact-ID stop/start/restart flows on Windows and Linux with status, exit-code, and changed-`StartedAt` oracles | Recipe fixed and verified in candidate bytes |
| T08 compact help | Lazydocker v0.25.2 Linux help after live resize to 80x24 | Demonstrated limitation excluded from supported scope |
| T09 persisted commit draft | Two candidate screen-pass/oracle-fail attempts retained; clearing input and proving modal closure produced the exact commit and tree | Fixed in candidate recipe; external Git oracle remains mandatory |

## Candidate scenario evidence

| Scenario | Evidence | Result |
| --- | --- | --- |
| Native installation and `/dev/tty` | Public install run 34333615063 | 3/3 hosts passed |
| Windows and Linux release boundaries | Downloaded rc.2: natural exit, signal cancellation, total timeout, output cap, descendant cleanup | 5/5 passed per host with expected statuses and cleanup evidence |
| Windows Lazygit primary | Downloaded rc.2, exact staged-file oracle per attempt | 10/10 passed |
| Windows Lazydocker logs | Downloaded rc.2, exact owned-container oracle per attempt | 10/10 passed |
| Windows Lazydocker lifecycle | Stop/start/restart against one ownership-checked fixture | 3/3 passed; a fresh second session also passed |
| Linux Lazygit primary | Downloaded rc.2, exact staged-file oracle per attempt | 10/10 passed |
| Linux Lazygit broader flow | Stage/unstage, commit, branch, and synchronized help/resize with Git oracles | 4/4 passed; earlier oracle failures retained separately |
| Lazygit second sessions | One reset-and-rerun session on Windows and Linux | 2/2 hosts passed |
| Linux Lazydocker | Ten log repetitions, four lifecycle actions, supported help/resize, bounded invalid endpoint, and a fresh session | 10/10 primary and all broader supported paths passed; compact 80x24 post-resize help remains an explicit exclusion |
| Windows K9s | Ten log repetitions; live YAML, help/resize, empty namespace, delete/cancel, denied/unreachable APIs, and a fresh session | 10/10 primary and all broader paths passed with Kubernetes API oracles |
| Linux K9s | Same downloaded-candidate paths and independent API checks as Windows | 10/10 primary and all broader paths passed |
| Application-regression value | Pinned Lazygit good/mutated/restored experiment | Complete technical evidence |
| Cross-language flow | IPython 8.27.0 file write with failed and recovered oracle | Complete technical evidence |

The candidate sample stays separate from the historical 60/60 technical campaign. It is 60/60 across all six Windows/Linux client cells, with no hidden retries. Setup interruptions, exploratory failures, corrected-oracle reruns, expected negative cases, and broader scenarios remain outside that denominator.

## Next publication gate and later adoption

- Stable outcome: R3c completed at 9/9 applications, 18/18 intended cells, and 54/54 frozen primary attempts. R4 then completed its contract audit, stable-byte build/package/install checks, and nine primary workflow refresh before publishing v0.1.0 on 12 September 2026.
- After publication: obtain three qualifying independent project reviews across at least two stacks, two voluntary second uses, and one successful participant-owned CI integration. These remain uncompleted adoption requirements.

The candidate Docker fixture was removed only after its exact ID, name, and two ownership labels were verified. The disposable `playtestr-r3` kind node was likewise verified by exact name and cluster/role labels, its final namespace state was recorded, and the named cluster was removed with exact absence confirmed. No unrelated container was enumerated or changed, and no active Kubernetes context was changed.

The R3c record supplies operator-run technical evidence, not adoption evidence. Its Windows and WSL Linux application results do not add a macOS real-application claim. Operator repetitions and private permission records cannot replace independent adoption after publication.
