# Lazygit, Lazydocker, and K9s technical trial

Status: historical technical campaign completed across all six Windows/Linux client cells. The Linux PTY defect in rc.1 is fixed and verified in published rc.2; stable promotion remains held by incomplete candidate real-app and independent-adoption evidence.

This operator-run technical campaign began on 7 September 2026 and its focused follow-up continued through 9 September. It does not represent maintainer review, endorsement, voluntary repeat use, or willingness to pay. A later IPython check supplies a non-Go technical sample; the parent R3 participant gates remain open.

## Environment and pinned inputs

- Windows client: Windows build `10.0.26200`, amd64, ConPTY.
- Linux client: Ubuntu 24.04.3 LTS under WSL2, amd64, Unix PTY.
- Docker: Docker Desktop 4.89.0, Linux Engine 29.7.2. The endpoint was shared, so raw screens were kept private and mutations targeted one recorded container ID with both `io.wyrcan.playtestr.owner=playtestr` and `io.wyrcan.playtestr.trial=r3-ld` labels.
- Kubernetes: one disposable kind v0.33.0 cluster named `playtestr-r3`, with a digest-pinned Kubernetes v1.35.0 node image and a dedicated kubeconfig. Windows and Linux K9s clients reached the same Linux-node cluster.
- Target versions, commits, archive hashes, runner assets, container image, and node image are frozen in [`trials/manifest.json`](../../trials/manifest.json).

The published `v0.1.0-rc.1` runner was always tried first. Windows historical results use that release asset. Linux historical results after the initial failure use a checkout-built `dev` runner and therefore do not prove rc.1 is compatible. Published rc.2 later passed the native `/dev/tty` package and public-install checks, then completed the candidate Linux Lazygit cell; its candidate sample is tracked separately in the [evidence ledger](evidence-ledger-2026-09.md).

## Matrix result

| Target and client | Required workflow result | Primary sample | Result boundary |
| --- | --- | --- | --- |
| Lazygit / Windows | Stage, commit, branch, help and resize passed | 10/10 passed | Published runner |
| Lazygit / Linux | Stage, commit, and branch passed; the original help/resize exit sequence was later corrected with explicit modal-disappearance synchronization | 10/10 passed | Patched runner; published runner failed at launch |
| Lazydocker / Windows | Logs, stop/start, restart, and help/resize passed; negative endpoint and empty-list messaging were not interpretable | 10/10 passed | Published runner; shared endpoint constrained isolation |
| Lazydocker / Linux | Logs, stop, and running-container restart passed; a focused rerun proved stopped-container start with an exact Docker oracle. The compact 80x24 help redraw remains excluded, and negative messaging was not interpretable | 10/10 passed | Patched runner; Docker integration restored before the final sample |
| K9s / Windows | Logs, YAML, delete, cancel, help/resize, and empty namespace passed; denied/unreachable APIs had no assertable rendered diagnostic | 10/10 passed | Published runner |
| K9s / Linux | Same functional paths passed; denied/unreachable APIs had no assertable rendered diagnostic | 10/10 passed | Patched runner |

Sixty final primary attempts passed without automatic retry: 20 Lazygit, 20 Lazydocker, and 20 K9s. Four earlier Windows Lazydocker attempts failed while the primary spec relied on ambient selection; those failures remain in the private denominator and led to exact-name filtering. The final samples are separately labeled and do not erase those earlier attempts.

## Runner defect found

The published Linux runner launched each target in a new session but did not assign the PTY slave as the session's controlling terminal. Lazygit v0.65.0 immediately failed while opening `/dev/tty` with `no such device or address`. This is a release blocker for the advertised Linux full-screen TUI workflow.

The fix sets `Setctty` with child descriptor zero alongside `Setsid`. A Unix-only real-PTY regression test opens `/dev/tty` from the target process. It failed before the fix and passes afterward. The full Windows suite, `go vet`, Windows race detector, and the cross-compiled full runner suite executed in Ubuntu passed with the change. Published rc.2 then passed this gate from extracted and publicly downloaded Linux and macOS archives.

## Workflow evidence

### Lazygit

- LG-01 staged only `alpha.txt`; `git diff --cached --name-only` and the cached diff verified the result on both hosts.
- LG-02 created the expected `trial commit`; Git independently checked the commit message and tree.
- LG-03 selected `trial-branch`; `git symbolic-ref` checked the branch.
- LG-04 reopened keybindings after both 80x24 and 120x40 resizes. The Linux failure came from matching text behind the modal and sending the next input before proving the modal had closed. The new `expect_not` action requires an earlier positive observation and a subsequent input or resize; the minimized 17-step Linux flow then passed and exited zero.
- Filenames with spaces and Unicode were present in the isolated fixture. A clean working tree correctly made the staging scenario fail, then the original change was restored and passed again on both hosts.
- With a synthetic `.git/index.lock`, the screen-only staging spec reported a pass while the independent index oracle remained empty. This is a spec/harness false positive caused by asserting the static `Staged changes` heading; it is not evidence that the runner ignored a failing assertion. The lock was removed and the same workflow then staged `alpha.txt` successfully.

### Lazydocker

- Exact filtering was required before every action because the Docker endpoint contained unrelated resources. No unrelated container was started, stopped, renamed, removed, or inspected for trial assertions.
- LD-01 selected the owned fixture and displayed `PLAYTESTR_LD_READY` from its logs.
- LD-02 stopped the same recorded container ID on both hosts, and Docker independently reported `exited` with code 137. A focused Linux rerun waited for the stale `exited` text to disappear and independently verified the exact container became `running` with a changed `StartedAt`; stopped-container start is accepted for that pinned rerun. The earlier false screen pass remains evidence for mandatory external oracles.
- LD-03 required waiting for the asynchronous restart before checking Docker's changed `StartedAt` value. A retained log marker alone would have been stale evidence. The running-container restart and timestamp oracle passed on both hosts.
- LD-04 reopened the menu after 80x24 and 120x40 resizes and quit cleanly on Windows. On Linux, direct PTY comparisons opened help after a live 80x24 resize, while the Playtestr sequence received the menu bytes only transiently before a later compact-layout repaint replaced them. Resize-only and normal-viewport help pass. Compact post-resize help remains a narrowly documented target/version limitation.
- A temporary rename of the running, ownership-checked fixture produced the intended missing-fixture failure; restoring its exact name returned LD-01 to green on both hosts.
- Filtering to a nonexistent name rendered an empty panel without the target's `No containers` message. An invalid Docker endpoint cleared the terminal and exited zero without leaving an assertable diagnostic. Playtestr previously captured the screen after cleanup, which could lose useful alternate-screen evidence; it now retains the rendered screen before cleanup on failure, with a deterministic regression test. The targets that emit no terminal diagnostic remain documented as such.
- Docker Desktop temporarily stopped exposing its socket to Ubuntu after a backend restart. The Linux cell resumed only after the integration returned; it was never redirected to an ambient or unverified endpoint.

### K9s

- K9-01 opened logs for the labeled fixture pod and displayed `PLAYTESTR_K9S_READY`.
- K9-02 selected the synthetic ConfigMap and rendered `trial-message: value with spaces λ` in YAML on both clients.
- K9-03 sent Ctrl+D, moved focus from the dialog's default Cancel button to OK, and deleted one pod. The Kubernetes API observed the original UID disappear and a new Ready UID appear.
- K9-04 cancelled the same dialog. The original UID remained and had no deletion timestamp.
- K9-05 reopened help after both viewport sizes and exited cleanly.
- K9-06 displayed a useful `No resources found` message for the empty namespace. An unprivileged service account and an unreachable loopback API produced bounded runs but no assertable on-screen `forbidden` or `connection refused` diagnostic.
- During the controlled ConfigMap fault, the first assertion matched an old value inside `kubectl.kubernetes.io/last-applied-configuration`. Removing that fixture annotation made the changed live value fail on both hosts; restoring `value with spaces λ` returned both to green. This confirms that broad text assertions over YAML can match historical annotations.

## Findings and release decision

| ID | Classification | Severity | Decision |
| --- | --- | --- | --- |
| R3-T01 | Runner correctness | Fixed in rc.2 | Published Linux and macOS candidate assets passed the controlling-terminal regression. |
| R3-T02 | Spec authoring / harness | High | Require independent state checks for mutations; do not accept static headings, retained logs, or annotation text as the only evidence. |
| R3-T03 | Environment / privacy | High | Use a dedicated Docker endpoint for publishable Lazydocker evidence. Shared global views can disclose unrelated resource names. |
| R3-T04 | Spec synchronization | Resolved locally | `expect_not` proves each observed modal closes before the next input; the minimized Linux flow exits zero. |
| R3-T05 | Runner evidence and target usability | Partially resolved | Capture the failure screen before cleanup; retain the documented limitation when the target supplies no diagnostic. |
| R3-T06 | Environment/setup | Resolved interruption | Docker Desktop integration returned; the Linux Lazydocker cell and ten-run sample were then executed. |
| R3-T07 | Spec synchronization / oracle | Resolved for pinned flow | Wait for stale state to disappear and require exact Docker status plus changed `StartedAt`. |
| R3-T08 | Target/version compact redraw | Accepted limitation | Exclude Lazydocker v0.25.2 Linux help-after-80x24-resize; normal viewport help and resize-only paths remain in scope. |
| R3-T09 | Spec synchronization / oracle | Resolved in candidate recipe | Clear persisted commit input, prove dialog closure, and require the exact Git commit/tree oracle. |

Focused disposition through 10 September: T01 is fixed in published candidate bytes. T04 passes the downloaded candidate real-app path. T07 is fixed at the spec/harness layer and passes its minimized checkout-built Linux rerun; the candidate Lazydocker lifecycle rerun remains blocked by Docker. T05's runner-side evidence loss is fixed, while target-supplied blank diagnostics remain a limitation. T08 is accepted only as a Lazydocker v0.25.2 compact-layout exclusion. T09's failed external oracles remain retained, and its corrected candidate commit flow passes.

The follow-up also built an unmodified pinned Lazygit control and a synthetic source mutation that changed the help title. The same spec passed the control, failed the launched mutated application at the intended assertion, and passed after restoring the control. A separate IPython 8.27.0 interaction wrote an exact file through its real prompt; the combined harness failed with an intentionally wrong oracle and passed after the oracle was corrected. These are technical value and stack-diversity results, not participant adoption.

The original campaign modified only fixtures. The focused follow-up added a separately labeled synthetic Lazygit source mutation and an IPython technical flow, closing the application-regression and cross-language technical checks. Human review, voluntary second use, and project CI adoption remain open.

The disposable cluster and original ownership-checked Docker fixture were removed by exact identity. The focused follow-up's exact fixture ID was already absent when final cleanup verification ran. No broad Docker listing, prune, remove-all, context change, or host-service restart was used.
