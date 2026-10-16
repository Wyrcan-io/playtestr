# v0.4.0-rc.2 scope

Evidence availability: bulk raw records are local-only; see [the archive policy](validation/README.md).

This prerelease completed native three-host qualification and
[public installation/upgrade verification](validation/e5-publication-2026-09-28.md). The
[readiness record](validation/e5-qualified-readiness-2026-09-27.md) and
machine packet (`validation/e5-observations-2026-09-27.json`, local evidence) are authoritative;
this table distinguishes executed cases from reliable support claims.

| Boundary | Evidence | Claim limit |
| --- | --- | --- |
| Native runner | Linux amd64, macOS arm64, Windows amd64, exact manifest hashes | Named native images only; other architectures/distributions unqualified |
| Existing project corpus | 120 first good executions, 15 controls, 15 recoveries | 119 supported cells plus diagnostic MICRO-08; TIG/taskwarrior targets are WSL |
| Repeated qualification | Ten selected workflows, 100 attempts per native host | Repeats are not 3,000 distinct workflows; no universal reliability guarantee |
| Six primary journeys | Native Linux/macOS final-byte controls plus Windows corpus/walkthroughs | Exact pinned Lazygit, micro, create-vite, fzf, litecli and Posting routes; Posting query editing remains excluded |
| GitUI/television holdouts | Two operator-designed definitions, final-byte Windows controls | Historical corpus presence limits independence; not customer adoption |
| Terminal rendering | Basic exercised code points, redraw, resize, alternate screen | Wide/combining cursor layout and query-dependent tasks unsupported on all hosts; a passing Snow string does not prove cells |
| Contracts | Preserved v1; opt-in v2 workspace/report and new reader | Old strict readers may reject v2; baseline bytes preserved |
| Installer | Native source failure/success and exact local archive identity | Public-origin archive/hash and immutable external action checks passed on all three hosts |
| Lifecycle | Natural/final output, timeout, cancellation, flood and managed descendants | Explicitly trusted targets; subprocess/PTY is not a sandbox; documented process escape limits |
| Report presentation | Offline rendering, scripted Tab/Enter, named accessibility controls | Human interactive screen-reader usability unmeasured; no broad accessibility claim |
| Performance/effort | Descriptive repeated timing and n=1 resource suites | Historical task losses/ties remain; human total effort unknown; differentiation unmet |

Use the [migration guidance](migration-v0.4.0-rc.2.md) and retained
archive bytes. Published v0.4.0-rc.1 remains a distinct qualified version;
later repairs cannot be attributed to its binaries or old action pin.
