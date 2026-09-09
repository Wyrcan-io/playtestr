# R3 observations and backlog

Status: technical findings recorded; participant evidence still awaited. Add an item only when it has a user task and reproducible observation.

## Known pre-trial questions

These are prompts to observe, not cohort findings:

| ID | Question | Existing evidence | Trial decision needed |
| --- | --- | --- | --- |
| PRE-001 | Does retained adjacent failure evidence confuse a later passing run? | Report v1 correctly removes evidence references, while old `.actual.txt` files remain. | Ask participants whether the latest report/status is clear and whether manual removal is acceptable. |
| PRE-002 | Does direct release installation create too much CI plumbing? | R2 uses explicit asset download and checksum verification. | Record actual adopter setup before scheduling reusable CI work. |
| PRE-003 | Does mutable application state prevent repeated runs? | No qualifying project evidence yet. | Record exact files/resources rather than assuming a workspace feature solves it. |

Pre-trial questions do not count toward frequency or roadmap priority until a participant encounters them.

## Accepted observations

| ID | Trial(s) | User task | Category | Impact | Reproduction/evidence | Workaround | Frequency | Smallest useful response | Destination | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R3-T01 | Lazygit/Linux | Launch a full-screen TUI that opens `/dev/tty`. | Runner correctness | The rc.1 Linux candidate exits before rendering. | `v0.1.0-rc.1` returned `unexpected_exit`; a Unix real-PTY regression failed before `Setctty` and passed after it. Published rc.2 Linux and macOS assets passed the `/dev/tty` gate. | Install `v0.1.0-rc.2` or newer. | One target, then validated with Lazygit and K9s in the historical checkout sample and with native release fixtures. | Complete the remaining rc.2 real-app Linux sample separately. | Release candidate | Fixed and verified in rc.2 bytes |
| R3-T02 | Lazygit/Windows and Linux | Prove that staging actually changed the Git index. | Spec authoring / harness | A static `Staged changes` heading let the screen-only spec pass while a stale index lock prevented staging. | Both host runners passed the text steps; `git diff --cached` remained empty. | Treat the independent Git oracle as part of the overall result. | 2/2 hosts. | Document external postconditions for mutating workflows. | Trial guidance | Accepted |
| R3-T03 | Lazydocker/Windows | Capture evidence from a global Docker dashboard. | Environment / privacy | Screens include unrelated local resource names and cannot be published safely. | Reviewed private initial screen from the shared Docker Desktop endpoint. | Keep raw evidence private and select the fixture by exact filter, ID, and labels. | One shared endpoint. | Require a dedicated endpoint for publishable service-dashboard trials. | Trial harness | Accepted |
| R3-T04 | Lazygit/Linux | Quit after opening help across two resizes. | Spec synchronization | Background text allowed input before the modal was proven closed. | A minimized flow with `expect_not` after each Escape passed 17 steps and exited zero. | Assert modal disappearance after observing it. | Reproduced and corrected on one host. | Keep the `expect_not` validation and integration coverage. | Spec contract | Resolved locally |
| R3-T05 | Lazydocker and K9s negative cases | Diagnose an unavailable endpoint or denied identity from captured terminal text. | Runner evidence plus target usability | Cleanup could replace a useful failure screen; some targets also render no diagnostic. | A clear-on-shutdown fixture proves pre-cleanup capture. Lazydocker invalid endpoint and K9s denied/unreachable cases still supply no assertable message. | Preserve the pre-cleanup rendered screen and classify absent target output honestly. | Deterministic runner regression plus four target/client attempts. | Keep the evidence fix; defer new channels until real demand. | Runner and backlog | Runner side fixed locally; target limitation accepted |
| R3-T06 | Lazydocker/Linux | Resume a Docker-backed TUI trial after a Docker Desktop restart. | Environment / setup | Ubuntu temporarily lost `/var/run/docker.sock`, blocking the client matrix cell. | WSL reported no socket after the restart; a later preflight found the socket and Docker Engine 29.7.2, after which the cell ran. | Require an explicit endpoint preflight and mark the cell blocked while integration is absent. | One host interruption. | Keep the preflight in the local harness instructions. | Trial harness | Resolved |
| R3-T07 | Lazydocker/Linux | Start the selected stopped fixture and prove the mutation occurred. | Spec synchronization / oracle | Retained logs hid an asynchronous state transition in the original flow. | Focused stopped/start specs used `expect_not` for stale `exited`; exact-ID Docker inspection observed `running` and a changed `StartedAt`. | Wait for the old state to disappear and poll the exact external resource. | Original failure plus one corrected Linux rerun. | Keep independent Docker oracles mandatory for lifecycle actions. | Trial guidance | Resolved for pinned flow |
| R3-T08 | Lazydocker/Linux | Reopen help after resizing from 120x40 to 80x24. | Target/version compact redraw | Direct PTY use can open the menu, but under the automated sequence its bytes are transient and a later compact-layout repaint removes it. | Pinned v0.25.2 comparisons covered plain quit, resize-only, both menu keys, bounded redraw synchronization, raw-byte presence, and clean process-group cleanup. | Use 120x40 for help; 80x24 resize-only remains usable. | One Linux host; Windows path passed. | Exclude compact post-resize help from the supported matrix and retest a later target version. | Compatibility notes | Accepted narrow limitation |
| R3-T09 | Lazygit/Linux rc.2 | Commit a staged change from a fresh test run. | Spec synchronization / oracle | Lazygit's commit draft persisted across launches, so matching the typed summary let the screen pass without proving the intended new commit. | First candidate run passed terminal steps while the Git oracle still saw the baseline; a second run committed a duplicated draft. Clearing the field and asserting the dialog disappeared produced exactly `trial commit` and changed only `alpha.txt`. | Clear text inputs whose target state may persist, assert modal disappearance, and keep the Git oracle mandatory. | One candidate cell, with two retained failed attempts and a corrected pass. | Add the synchronization rule to the reusable recipe; no runner change required. | Trial guidance | Resolved in candidate recipe |

## Priority rules

| Priority | Qualifying impact | Required response |
| --- | --- | --- |
| Release blocker | False pass, surviving managed process, data loss, unintended sensitive-data persistence, or broken advertised installation. | Hold stable promotion, preserve a sanitized reproduction, fix, and verify new candidate bytes where needed. |
| Adoption blocker | The agreed real workflow cannot be tested without disproportionate custom setup or incorrect supported rendering. | Decide on a narrow candidate fix or evidence-backed sprint before expanding the trial. |
| Repeated friction | Two or more participants struggle with the same authoring, discovery, evidence, or CI task. | Rank by time/impact and feed the smallest relevant sprint. |
| Project-specific issue | One target/environment needs a workaround that is safe and documented. | Record the workaround and avoid a general compatibility claim. |
| Preference or speculation | No blocked task or reproduction. | Keep as context; do not schedule automatically. |

## Triage checklist

For each accepted item, verify:

- The target version, host, starting state, spec, expected result, and actual result are known.
- The failure layer is identified without relying only on console prose.
- Shared evidence is sanitized and publication permission is recorded.
- Impact and cohort frequency are stated separately.
- The workaround does not hide a false pass, leak a process, update a baseline blindly, or weaken production time/output limits.
- The proposed response is the smallest user-visible improvement that solves the observed task.

Close an item only with recorded evidence or an explicit decision that the behavior remains a documented limitation. Do not claim a participant accepted a workaround unless they actually did.
