# Download publication — 28 September 2026

Evidence availability: bulk raw records are local-only; see [the archive policy](README.md).

The user authorized publishing downloads and completing distribution checks,
and explicitly prohibited outreach and marketing. The execution prompt is
[publish verified downloads](../archive/prelaunch-2026-10-06/plans/publish-verified-downloads-prompt.md).
This overrides the earlier publication hold; A1/A2 remain unstarted.

Status: **published and verified on all three native hosts**. The
[v0.4.0-rc.2 prerelease](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.4.0-rc.2)
was published at 2026-09-27 19:48:02 UTC (28 September in Asia/Calcutta).
Its tag resolves to `ae97c62022966cde9699b26169b4dc6ef0a12439`.
Seven assets contain the three original native archives, three adjacent
checksums and the aggregate checksum file. Stable v0.1.0 is unchanged.

All public archives and checksum files were downloaded locally and matched
the [qualified manifest](../../release/e5-candidate-manifest.json) byte-for-byte.
No runner was rebuilt. The prior [E5 private acceptance](e5-qualified-readiness-2026-09-27.md)
remains historical qualification evidence: 3,000 selected first attempts,
119 supported corpus cells plus the excluded wide-cell diagnostic.

Native distribution/upgrade run
[36345677928](https://github.com/Wyrcan-io/playtestr/actions/runs/36345677928)
executes three public archive/action lanes and three old-to-new upgrade lanes.
It uses the actual external immutable setup action
`Wyrcan-io/playtestr/setup-playtestr@ae97c62022966cde9699b26169b4dc6ef0a12439`.
The runner pin is independently `v0.4.0-rc.2`. Test helpers build with Go 1.26;
the published runner is downloaded, never built by this verification.

Separate binary-only smoke run
[36346042029](https://github.com/Wyrcan-io/playtestr/actions/runs/36346042029)
checks installed hashes/version/PATH and good/failure/recovery/offline reports
on all three native hosts, without installing Go as a prerequisite.
Actual job outcomes, focused evidence, artifact digests, public asset identities
and final CI records are retained under ignored `artifacts/e5-publication/`.
Do not infer passes from configured workflows.

Wide/combining cursor layout and terminal-query-dependent flows remain excluded.
Human screen-reader use, first-use/diagnosis time and independent adoption remain
unmeasured; differentiation is unmet. Trusted target execution is not sandboxing.
The prior private kit is not uploaded as a release asset. No user prompt,
secrets, environment dump or private target state is published.

No messages, invitations, marketing, announcements, issues, discussions or PRs
were created. No website deployment or repository-setting change is included.
Engineering completion does not authorize contacting anyone; only a later
explicit user instruction can reopen that boundary.

Actual acceptance: six distribution/upgrade lanes and three final binary lanes
passed. The machine packet (`e5-publication-observations-2026-09-28.json`, local evidence)
retains 66 distribution/upgrade report outcomes and 14 final binary outcomes,
including expected negatives. Managed cleanup was confirmed for every launched
reported target; invalid specs were rejected before launch. Unix `/dev/tty`,
version/PATH, exact-byte extraction, reviewed-baseline preservation, v1/v2/mixed
reports, expected nonzero exits and stateful cancellation passed.

First failures are preserved rather than retried invisibly:
[36345680511](https://github.com/Wyrcan-io/playtestr/actions/runs/36345680511)
launched fixture scripts from the wrong invocation directory. All three
failed safely; an owned fixture copy and correct cwd passed in
[36345851114](https://github.com/Wyrcan-io/playtestr/actions/runs/36345851114).
The expanded gate [36345947855](https://github.com/Wyrcan-io/playtestr/actions/runs/36345947855)
expected invalid input to return argument-error exit 2, whereas the established
contract reports `invalid_spec` as failed-test exit 1. Unix tty/greeting checks
had passed; correcting the expected exit and inspecting prelaunch evidence
passed in the final run. Neither failure required a runner/action repair,
rebuild, published-byte replacement, deadline change or qualification rerun.

The frozen build-time and E5 private records keep their historical unpublished
status; this separately authorized public verification is the later evidence.
The hosted runners can have Go preinstalled; the binary-only route does not
install, invoke or require it. Documentation/source helpers are not runner
rebuilds. Website checks build locally/in CI; deployment remains disabled.
