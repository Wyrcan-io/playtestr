# Sprint 14: make the proof memorable and reproducible

Status: complete 25 September 2026; published and publicly verified by R6-V on 26 September. Owner: Playtestr maintainer. Evidence: [Sprint 14/R6-K record](../../validation/sprint-14-r6-k-2026-09-25.md) and [R6-V record](../../validation/r6-publication-and-blocker-2026-09-25.md). User result: a newcomer sees a real bug caught, understands the evidence, and can run the same example.

Draft scripts can be prepared earlier; final captures run against the **R6-F/11-C qualified executable hashes**. R6 publication follows the completed kit, and final public download/asset links are verified afterward. See [root sequence](../../../roadmap.md) and [execution contract](../execution-contract.md). A draft captured from development source must be replaced or explicitly labeled before release.

## A: three honest stories

| Story | Demonstration | Required proof |
| --- | --- | --- |
| Hero, 45–60 seconds | Select item, pass; inject wrong-selection defect, fail; inspect report; fix, green | Same spec and reviewed baseline; actual target defect, exact nonzero result |
| Stateful, 60–90 seconds | Wizard or repository action starts fresh; cancellation must leave expected state | Real file/Git postcondition and fresh workspace, not only success text |
| Compatibility, 60–90 seconds | Resize/redraw or selected Unicode case stays correct; meaningful regression fails | Exact supported behavior and host; no full-Unicode or style assertion implication |

Use repository-owned fixtures for easily redistributed defect toggles; include at least one real third-party recipe as deeper proof with proper attribution. Preserve target/runner hashes, specs, patches, commands and captured artifacts. Baseline-only mismatch demos must be labeled and cannot replace real-defect proof.

The distinct product idea is a demo where viewers can inspect the same evidence and run the same regression locally. It needs no new runner protocol. A static evidence gallery with pass/fail/recovery controls may be built from captured files; label it recorded, include keyboard controls, reduced motion, captions and static fallback. Use VHS or ordinary screen capture externally if useful; do not build a recorder into Playtestr.

Hero storyboard: seconds 0–8 name the user regression; 8–18 show the short test and one input; 18–32 show unchanged baseline detecting the target defect; 32–45 open the actual focused report; 45–60 show recovery and one clear link to run the same example. Timing is an editorial target, not a runner speed claim. Keep full uncut reproduction and exact commands available. Never accelerate a hang and imply instantaneous diagnosis without a caption.

Choose legible 80-column evidence rather than a crowded montage. Show what the failure means before low-level metadata. Annotated colors in a report must not imply the runner asserts terminal styles. Use one authentic third-party recipe as supporting proof, with permission/license-aware assets and no inferred maintainer endorsement.

Acceptance: each story has fresh reproducible artifacts; no invented output, testimonials or benchmarks; baseline remains unchanged across pass/defect/recovery; video editing/accelerated waiting is disclosed.

## B: watch-to-run path

One clear path: understand the caught bug → choose exact host archive → run the example → inspect real failure → adapt a recipe. Separate stable, prerelease and development features. Link prerequisites before commands; distinguish installation time from test time. Reuse existing site components instead of redesigning branding.

Publish-ready material: three recipe pages, screenshot/report gallery, compatibility table by project/version/host/workflow, a short framework-unit/E2E comparison, versioned download guidance, update/rollback notes and known limits. Every compatibility badge links to evidence; an app name is not a framework certification.

Browser checks: desktop/narrow layouts, keyboard-only navigation, meaningful labels, readable long terminal lines, contrast, reduced motion, no-script/static fallback and zero external requests for exported reports. Re-run existing website checks. Link a real downloaded report and test that it remains useful offline.

Close the earlier R5 manual screen-reader gap with a recorded desktop/browser/screen-reader combination: read the failure summary, follow the skip link, enter the evidence pane, understand diff additions/removals, and reach the runnable example. Accessibility-tree inspection alone is not a screen-reader session. If the environment is unavailable, keep that review open and avoid claiming a complete accessibility audit. Do not claim universal WCAG conformance from this small check.

## C: rehearsal and launch kit

Run the installation/three-recipe path on clean native hosts using the candidate. Record every manual intervention and fix documentation before R6. Have the project owner review whether each story makes the bug and next action obvious. This review is not independent adoption.

Prepare concise release notes, one technical walkthrough and channel-specific draft announcements pointing to the runnable example. No unsolicited messages or public posting in this sprint. Specific outreach/publication needs explicit instructions; research and local draft preparation can proceed.

After A1, distribution can emphasize actual case studies in relevant language/TUI communities with permission. Measure opt-in walkthrough completion, useful CI use and retention. Avoid default telemetry or optimizing for stars/views at the expense of working tests.

## Exit

- [x] Three real stories, including attributed third-party proof and independent state checks.
- [x] Recipes reproduce success, meaningful failure and recovery on documented hosts.
- [x] Website/report automated accessibility, links and version accuracy checked; actual screen-reader session remains explicitly open because no interactive assistive-technology session was available.
- [x] Downloadable evidence and draft launch kit ready for R6-P.
- [x] Remaining usability hypotheses handed to A1; no outreach or adoption implied.
