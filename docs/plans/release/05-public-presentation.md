# R5 — Public presentation before independent adoption

Status: implemented locally on 12 September 2026. The static build, generated-route checks, responsive browser matrix, documentation search, progressive fallbacks, interactive pass/failure evidence, social preview, and Windows pass/failure/recovery check pass in the working tree. Publication, live Pages inspection, external GitHub repository settings, and native macOS/Linux repetition remain open because they require external state or hosts. Product scope and evidence requirements remain unchanged.

## Objective

Make one journey clear and trustworthy:

**Understand Playtestr → download the right binary → run a passing test → see a useful failure → test your own application.**

Preserve the existing visual style and deterministic CLI/TUI testing scope. Improve clarity using only evidence already recorded in the repository. Do not invent testimonials, compatibility, metrics, performance results, or adoption results.

## Audit findings

- The README's first installation path quickly switches to cloning and building three Go binaries. The existing binary-only release walkthrough is a better newcomer path.
- The website promises a first passing test but currently ends its quickstart at `--version`; it does not demonstrate a complete pass/failure/recovery loop.
- The release tag, releases list, archive names, and checksum instructions are spread across surfaces and are not presented as one platform chooser.
- Platform evidence is thorough, but its historical detail is harder for a first-time user to interpret than a short current-support summary.
- The positioning is strong, but implementation history and sprint links appear earlier than some users need. Trust evidence is distributed across release, support, and compatibility documents.
- The website's Docs link points into the README rather than to a documentation index organized around user tasks.
- Existing site accessibility foundations are good: semantic sections, skip link, visible focus, responsive grids, and reduced-motion handling. Rendered mobile, zoom, overflow, and assistive-technology behavior still need validation.
- The static site has basic Open Graph metadata and a favicon, but no canonical URL, Open Graph URL/image, or Twitter card metadata was found in the source audit.
- Bug, security, and project-trial forms exist. The homepage exposes only generic Feedback, and trial recruitment material is mixed with internal adoption gates.
- The site uses a coherent paper/rust/terminal visual language. New screenshots and metadata should extend that language rather than introduce a new brand system.

## Priority plan

### P0 — Make the first test work without a source checkout

**Affected files:** `README.md`, `site/index.html`, `docs/releases/v0.1.0-installation-walkthrough.md`, and existing `testdata/install-smoke/` fixtures where useful.

**Implementation:**

- Make the binary-only greeting example the primary onboarding path.
- Provide complete Linux, macOS, and Windows instructions: download, verify, extract, create example files, and run.
- Add the missing Unix `chmod +x` instruction and make directory and binary-path transitions explicit.
- Show expected passing output, one deliberate assertion failure, its evidence file, and recovery.
- Follow with a short “Use your own CLI” explanation.
- Move source builds, race-detector setup, and internal failure fixtures into contributor-focused documentation.

**Acceptance criteria:**

- A newcomer can finish using the published runner and documented host tools, without Go or a repository checkout.
- The first-run path produces a pass, an intended failure, and a restored pass.
- Every command is complete for its stated shell; placeholders are explicitly labeled.
- Trial participation is optional and never required to download or use Playtestr.

**Validation checks:**

- Follow the exact instructions in fresh directories on each advertised native platform, including a path containing spaces.
- Record runner version, exit codes, and report/evidence outcomes.
- Do not infer macOS success from Windows or WSL results.

### P0 — Unify downloads and supported-platform wording

**Affected files:** `README.md`, `site/index.html`, `SUPPORT.md`, `docs/platform-support.md`, `docs/releases/v0.1.0.md`.

**Implementation:**

- Use consistent primary wording: **“Download stable v0.1.0.”**
- Provide an explicit platform chooser with archive, checksum, and installation-guide links.
- Explain architecture labels: Linux x86-64 (`amd64`), Apple silicon (`arm64`), and Windows x86-64 (`amd64`).
- Explain separately that the runner needs no Go installation while the target application still needs its own runtime and dependencies.
- Put a short current-support summary above historical verification details.
- Keep version-specific instructions pinned to the release they describe.

**Acceptance criteria:**

- Primary download paths lead to stable assets, with no release-candidate ambiguity.
- OS-only wording never implies support for all architectures or OS versions.
- Intel macOS, Windows ARM, and other unadvertised targets are not presented as verified.
- Checksums are described as integrity checks, without implying a signature or security certification.

**Validation checks:**

- Check every archive/checksum pair against published release metadata.
- Verify all links and filenames.
- Compare platform wording across public surfaces.

### P0 — Clarify positioning and surface existing trust evidence

**Affected files:** `README.md`, `site/index.html`, `SUPPORT.md`, `docs/platform-support.md`, `docs/terminal-compatibility.md`.

**Implementation:**

- Use “End-to-end testing for interactive CLIs and TUIs” consistently, supported by “Press the keys. Check the screen. Catch the regression.”
- Explain the result concretely: authored keyboard interactions, rendered-text assertions, reviewed snapshots, and useful failure evidence.
- Add a compact trust row: Apache 2.0, standalone local runner, exact supported downloads, release evidence, and support policy.
- Keep concise boundaries near onboarding: trusted targets, text rather than styled snapshots, and documented Unicode limitations.
- Separate current release evidence from historical runs and operator-run application trials.

**Acceptance criteria:**

- A reader can identify the audience, purpose, and main limitation without opening the roadmap.
- Every verification claim links to evidence with a version and platform scope.
- “Stable” retains the existing support-policy meaning.
- No testimonials, adoption counts, framework certification, performance claims, or reliability percentages are introduced.

**Validation checks:**

- Review each public claim against the release record, support policy, and terminal contract.
- Label old evidence by version.
- Remove ambiguous “current source” wording where it describes a historical commit.

### P0 — Create a clear documentation entrance

Expanded requirement: the documentation index must lead to full documentation pages hosted on the Playtestr website. A GitHub Markdown index alone does not satisfy this milestone. See the multipage website work package below for routes, publishing architecture, navigation, and search.

**Affected files:** new `docs/README.md` and `docs/development.md`; `README.md`, `site/index.html`, `docs/spec-v1.md`, `docs/report-v1.md`, `docs/trials/README.md`, `docs/sprints.md`.

**Implementation:**

- Create a small docs index organized around user tasks: install, write a test, review snapshots, diagnose failures, check compatibility, and get help.
- Link reference material and development plans separately.
- Add consistent “Documentation” and relevant next-step links to primary guides.
- Distinguish stable documentation from development documentation.
- Use absolute versioned links where documentation must also work from an extracted release README.

**Acceptance criteria:**

- Installation, test authoring, compatibility, and support are reachable within two navigation choices from the homepage.
- Existing published document paths continue to work.
- The README remains useful on GitHub and inside an archive.
- Planned features cannot be mistaken for released functionality.

**Validation checks:**

- Check Markdown links, HTML links, fragments, filename case, and links from an extracted archive.
- Review the GitHub-rendered navigation manually.

### P0 — Show one real, reproducible example

Expanded requirement: use this evidence as the foundation for the interactive terminal demonstration specified below. The static example remains its accessible fallback.

**Affected files:** `site/index.html`, `README.md`, new `site/assets/` demonstration assets, `docs/website.md`; existing `examples/menu.json` and snapshot-mismatch fixtures.

**Implementation:**

- Capture a real run of the menu example and an actual intentional snapshot mismatch.
- Show the short spec, relevant screen, and useful failure evidence together.
- Label captures with version, host, and reproduction command.
- Keep readable HTML/text equivalents; use a static image only where it adds value.
- Retain the paper/rust palette and terminal-prompt mark; make header, footer, favicon, and README presentation consistent.

**Acceptance criteria:**

- Captured output matches the stated command and version.
- Illustrations remain explicitly labeled when they are not actual output.
- No secrets, personal paths, or invented product behavior appear.
- The example remains understandable without images or color.

**Validation checks:**

- Reproduce the referenced runs.
- Compare displayed output with captured evidence.
- Review image alternatives and inspect small-screen readability.

### P0 — Validate accessibility and mobile usability

**Affected files:** `site/index.html`, `site/style.css`, `docs/website.md`.

**Implementation:**

- Preserve the existing skip link, semantic structure, visible focus styling, responsive layout, and reduced-motion behavior.
- Improve small supporting text and link target spacing where testing shows friction.
- Keep key navigation available on narrow screens; do not hide the only path to documentation.
- Keep long commands scrolling inside their containers without widening the page.
- Make overflowing examples keyboard accessible and meaningfully labeled.

**Acceptance criteria:**

- No page-level horizontal overflow at 320, 375, 768, and 1440 CSS pixels.
- Content remains usable with 200% text enlargement and 400% browser zoom.
- Keyboard users can reach all actions, follow the skip link, and identify focus.
- Contrast and target sizing meet applicable WCAG 2.2 AA requirements.
- Pass/fail and diff meaning do not depend on color.

**Validation checks:**

- Run an automated accessibility scan.
- Manually test keyboard navigation, a screen reader, zoom, reduced motion, and representative mobile browsers.
- Record tested combinations without claiming full accessibility certification.

### P1 — Complete social previews and GitHub presentation

**Affected files:** `site/index.html`, new `site/assets/social-preview.png`, `docs/website.md`; repository About fields, topics, and social-preview settings during implementation.

**Implementation:**

- Add the canonical Pages URL, matching Open Graph URL, preview image dimensions and alternative text, and Twitter card metadata.
- Create a simple 1200×630 preview using the existing mark, product name, and descriptive tagline.
- Use absolute image URLs that include the `/playtestr/` project path.
- Align the GitHub description, homepage link, topics, and preview image with the site.

**Acceptance criteria:**

- Shared links identify the product and purpose clearly.
- Metadata contains no unsupported claims.
- Images load independently and remain legible when cropped.
- GitHub settings accurately reflect the published project.

**Validation checks:**

- Inspect deployed HTML and image responses.
- Check preview rendering where available.
- Verify repository settings directly.

### P0 — Make support and trial participation easy to find

**Affected files:** `site/index.html`, `README.md`, `SUPPORT.md`, `docs/trials/README.md`, `docs/trials/cohort.md`, `.github/ISSUE_TEMPLATE/project-trial.yml`; optionally new `.github/ISSUE_TEMPLATE/config.yml`.

**Implementation:**

- Provide distinct links for “Get help,” “Report a bug,” and “Try Playtestr on your project.”
- Lead the trial page with eligibility, prerequisites, expected participation, and the existing signup form.
- Move recruitment targets and outreach administration into cohort material.
- Retain public-issue privacy guidance, optional attribution, and the absence of a promised response time.
- Do not advertise a private general-support channel unless one exists.

**Acceptance criteria:**

- Users can find help without reading the trial protocol.
- Trial expectations are understandable before opening the form.
- Trial results remain separate from internal technical validation.
- Sensitive security reporting routes to the existing private reporting mechanism.

**Validation checks:**

- Walk through each route without submitting anything.
- Verify issue forms and private vulnerability reporting are available and destinations match their labels.

### P0 — Establish a final consistency and publication gate

**Affected files:** `docs/releases/v0.1.0.md`, `CHANGELOG.md`, `docs/releasing.md`, `docs/website.md`, `.github/workflows/pages.yml`; a small presentation-check workflow if warranted.

**Implementation:**

- Structure release messaging around what users can do, downloads, first test, limitations, and help; retain detailed evidence below.
- Check release-body links in their actual GitHub Release context.
- Document one release-update checklist covering version labels, assets, checksums, platform wording, guides, and metadata.
- Add lightweight HTML, link, and asset checks before Pages deployment.
- Preserve historical tags and assets; documentation improvements do not rewrite released archives.

**Acceptance criteria:**

- Public entry points agree on stable version, supported targets, installation path, and support links.
- Pages still deploys the canonical schemas at their existing URLs.
- The site remains static, without a new frontend framework or tracking dependency.
- Publication follows review of the concrete changes.

**Validation checks:**

- Complete a final journey from homepage and README through installation, pass/failure/recovery, documentation, and help.
- Verify the live deployment after publication.
- Run product tests only if executable examples or tooling change; presentation-only edits require link, rendering, accessibility, and walkthrough checks.

## Suggested implementation order

1. Establish the shared website layout, route map, and static documentation build. Demonstrate the home, installation, and one reference page before filling out the remaining pages.
2. Complete the binary-only first-run path, download chooser, and canonical documentation migration. Validate links and commands before adding interaction.
3. Add documentation search, support/trial routes, and consistent release/evidence presentation.
4. Capture the reproducible pass/failure evidence, then build the terminal's static presentation and interactive controls.
5. Complete the remaining pages, metadata, and GitHub presentation using the existing color palette.
6. Validate the complete site for accessibility, mobile use, performance, broken links, fallback behavior, and truthful demonstrations; prepare a reviewable preview before publication.

Each checkpoint must be independently reviewable. A successful build alone does not close the website milestone, and the plan does not authorize publishing changes or sending outreach.

## Website expansion requested by the user

The website must feel like a complete maintained developer product: useful dedicated pages, readable reference documentation, an immediate route to a working test, and a distinctive terminal demonstration. The existing colors are fixed. No glassmorphism, blurred translucent panels, decorative gradient backgrounds, glowing borders, floating blobs, generic feature-card grids, or unnecessary motion.

### P0 — Build a complete multipage documentation website

**Reasoning:** Sending every Docs click to GitHub interrupts learning and makes the site function mainly as a landing page. Shared documentation pages make installation, authoring, failure diagnosis, and support part of one coherent experience. Keep GitHub source links for contribution and evidence, while the normal reading journey stays on the website.

**Proposed public routes:** All routes below are relative to `https://wyrcan-io.github.io/playtestr/`, including its project-path prefix.

| Route | Purpose and required content | Primary source |
| --- | --- | --- |
| `/` | Product purpose, terminal demonstration, stable download and first-test actions, supported-target summary | Existing homepage and reviewed example evidence |
| `/download/` | Exact OS/architecture choices, archive/checksum links, version, extraction and next step | Stable release record and installation guide |
| `/docs/` | Start here, learning path, reference entry points, supported documentation version | New `docs/README.md` |
| `/docs/installation/` | Binary-only pass, deliberate failure, and recovery on each supported host | `docs/releases/v0.1.0-installation-walkthrough.md` |
| `/docs/writing-tests/` | Commands, readiness, input, expected exits, working directory, environment, and limits | New task-oriented guide extracted from README and checked against spec v1 |
| `/docs/snapshots/` | Baseline creation, readiness, review, selective updates, and mismatch evidence | New guide grounded in existing spec and README behavior |
| `/docs/troubleshooting/` | Missing target, unexpected exit, assertion timeout, snapshot mismatch, cleanup, and stale artifacts | New guide grounded in existing outcome categories and support material |
| `/docs/spec-v1/` | Complete test contract and canonical schema link | `docs/spec-v1.md` |
| `/docs/report-v1/` | Report fields, categories, evidence references, and schema link | `docs/report-v1.md` |
| `/docs/compatibility/` | Short supported-target summary, terminal limitations, and links to exact evidence | `docs/platform-support.md` and `docs/terminal-compatibility.md` |
| `/examples/` | Reproducible menu/pass/failure example with setup, spec, reviewed baseline, and evidence | Existing examples and new sanitized demonstration data |
| `/releases/` and `/releases/v0.1.0/` | Current stable release, changes, downloads, support meaning, limitations, and historical links | `CHANGELOG.md` and versioned release records |
| `/support/` | Help, bug reporting, private security reporting, and support boundaries | `SUPPORT.md` and `SECURITY.md` |
| `/trials/` | Optional project-trial introduction and existing signup route | Participant-facing content in `docs/trials/README.md` |
| `404.html` | Useful missing-page message with home, docs, and download links | New website template |

**Implementation architecture:**

- Use a pinned Hugo static-site build with custom templates matching the existing design. Its concrete purpose is to render Markdown, reuse page layouts, and generate navigation and metadata. It is a website build tool only; the Go runner receives no new runtime or production dependency.
- Hugo supports Markdown content, menus, syntax highlighting, and configurable URLs; use these existing facilities rather than writing a new documentation engine. Reference: [Hugo content management](https://gohugo.io/content-management/).
- Keep `docs/` as the canonical source for shared technical prose. Introduce an explicit allowlist mapping source documents to public routes and navigation labels. Mount or stage these sources into the website build; do not maintain edited copies of the same reference text in `site/`.
- Prototype the installation and spec pages first to verify source mapping, headings, internal links, schema links, and GitHub Markdown readability. Record the selected mapping method in `docs/website.md` before extending it to all documents.
- Publish only allowlisted material. Internal trial operations, outreach drafts, and sprint plans remain linked source material where relevant, rather than automatically becoming public navigation entries.
- Use shared templates for the header, footer, documentation sidebar, page contents, code blocks, release information, and metadata. Avoid an off-the-shelf marketing theme.
- Keep stable downloads in one reviewed website data file containing version, exact asset URLs, checksum URLs, and evidence links. Render website download references from that data; separately check README and release copy for agreement.
- Route mapped relative Markdown links to their website equivalents and preserve fragments. Unmapped repository files use explicit GitHub source links. Fail the build/check on unresolved local targets instead of silently producing broken `.md` links.
- Generate real HTML files for every route. Direct entry, refresh, bookmarking, and browser back/forward must work on GitHub Pages without client-side routing.
- Expand Pages workflow path triggers to include published documentation sources, shared policy files, release data, and build configuration. Preserve the existing schema URLs.
- Document a single local preview command and a clean production build command. Keep generated output in an ignored build directory; deploy the checked build artifact.

**Documentation experience:**

- Global navigation: Docs, Examples, Releases, GitHub, and a stable Download action. Footer: Support, Project trials, License, and source/roadmap links.
- Desktop documentation layout: compact left navigation, readable article column, and page contents where the article is long enough to need it. Mobile uses accessible collapsible navigation and page contents; article text retains the full useful width.
- Include current-page indication, a visible documentation-version label, heading permalinks, next/previous links within guides, and a source/edit link to the correct file.
- Begin with one maintained stable documentation set labeled for v0.1.0/spec v1. Keep immutable release records separate; do not invent a working version selector before multiple maintained sets exist. Mark any future-only content explicitly.
- Add small on-demand client-side search over a generated index of published page titles, headings, and plain text. Show relevant excerpts, linked headings, an understandable empty result, a clear button, and keyboard-accessible results. No external search account or query telemetry.
- Keep navigation and all documentation readable without JavaScript. Search and copy controls are enhancements; a broken script cannot hide the content.
- Code-copy buttons copy only the command or file content, without shell prompts or explanatory labels. Provide ordinary selectable text if clipboard access fails.

**Affected files:** `site/index.html`, `site/style.css`, new `site/hugo.toml`, `site/layouts/`, `site/data/`, website-only content under `site/content/`, new small search/copy modules under `site/assets/`, canonical guides under `docs/`, `docs/website.md`, `.github/workflows/pages.yml`, and `.gitignore`. Exact template filenames are settled in the first prototype.

**Acceptance criteria:**

- Every route in the table contains useful finished content, shares the same navigation, and can be opened directly on Pages. There are no empty placeholders or misleading controls.
- The ordinary installation, authoring, reference, and troubleshooting journey stays on the website; external downloads, source evidence, and issue forms are clearly identified.
- Shared technical content has one editable source. Updating an allowlisted guide rebuilds its public page.
- Search finds installation, `expect_not`, snapshots, and cleanup; an unmatched query shows a useful empty state.
- Current version, support boundaries, and download targets agree across generated pages and repository documents.

**Validation checks:** Clean build from a fresh checkout with the pinned tool; crawl generated routes and fragments under the actual `/playtestr/` base path; inspect Markdown-to-HTML link rewriting; open nested pages directly; exercise search with keyboard, empty/no-match queries, and JavaScript disabled; check schema availability and custom 404 behavior; verify Pages staging includes only intended public content.

### P0 — Add a terminal demonstration visitors can explore

**Reference and interpretation:** The user referenced [GitHub CLI's homepage](https://cli.github.com/) and supplied a screenshot of its command-and-terminal presentation with a pause control. The fetched page contains a series of command examples and outputs. Its exact animation implementation was not inspected. Use the command-led demonstration and playback affordances as inspiration; do not assume it provides a live shell, copy its implementation, or reproduce its gradient background and branding.

**Recommended Playtestr interaction:** Make the visitor explore a test and its evidence. This communicates the product more specifically than an endlessly typing command animation.

1. Show the existing mission-control example in a solid terminal panel, with the actual command above it and a short spec alongside it on desktop.
2. Offer `Play example`, `Pause`, `Next step`, and `Restart`. As a step advances, highlight its JSON action, show the relevant captured terminal state, and explain the assertion in one sentence.
3. Provide `Passing example` and `Intentional failure` controls. Switching chooses a separate verified example dataset and resets playback. The failure view shows the actual mismatch, runner exit status, and captured diff/evidence from that example.
4. Offer `Expected`, `Actual`, and `Diff` evidence views after the mismatch. Show additions/deletions with symbols and text as well as the existing semantic colors.
5. Finish with `Run this example locally` and a complete linked recipe. A visitor must be able to reproduce the displayed outcome using the named version and prerequisites.

**How to implement it:**

- Use semantic HTML, the existing terminal CSS, and a small plain JavaScript module that advances a finite set of reviewed states. No browser terminal emulator, WebSocket service, arbitrary command input, or server-side target execution is required for this experience.
- Label it `Interactive example — recorded terminal states` and explain that controls explore a prepared run. Playback is a website feature, not a claim that Playtestr ships a recording/replay product feature.
- Store sanitized data for each scenario: scenario ID, runner version, host, source revision, reproducible command, viewport, exact spec, ordered screen states, final runner output, exit status, and available evidence. Do not add new fields to Playtestr report v1 for website playback.
- Obtain intermediate states from a bounded maintainer-only capture procedure using the trusted fixture. Record how capture was performed and which labels are explanatory UI. Do not invent runner log lines or pretend inferred intermediate frames were captured. If only final evidence is available, demonstrate the final result until authentic intermediate states have been collected.
- Keep presentation timing separate from measured execution. Do not display playback duration as a benchmark or imply a speed claim. Step counters mean authored actions, not timestamps or assertions that have not actually passed.
- Keep output as escaped text (`textContent` or equivalent safe template output). Never interpret terminal text or user-provided search values as HTML.
- Validate dataset shape, supported version, frame count, string sizes, and referenced assets at build time. A malformed or missing dataset falls back to the static verified example with a clear unavailable message.
- Start paused with a meaningful visible frame. Playback is user initiated, never loops by default, stops at the end, and pauses when the page is hidden. Reduced-motion users receive immediate state changes without typing effects.
- Keep native buttons available on touch screens. Optional arrow/Enter shortcuts operate only while the demo has focus; never capture global typing, scrolling, Tab, or Escape.
- Reserve panel space to avoid page jumps. Stack the spec, terminal, and evidence on phones; scroll long terminal rows inside the panel while keeping controls and captions reachable.
- Announce completed steps and final status politely to screen readers, not every character. Provide a complete static transcript and accessible labels for controls and evidence views.
- Use a short homepage scenario and the same component on `/examples/` for full inspection. Additional resize or timeout scenarios wait until the initial pass/failure pair is complete and verified.

**Affected files:** homepage/shared templates, `site/style.css`, new `site/assets/terminal-demo.js`, new sanitized data and transcripts under `site/static/demos/`, the examples page source, `docs/website.md`, and a small website-only capture/validation helper if necessary. Existing `examples/menu.json` and snapshot-mismatch fixtures are source references; runner behavior remains unchanged.

**Acceptance criteria:**

- Visitors can play, pause, step, restart, change scenario, inspect a real mismatch, and reach the local reproduction recipe.
- The failure is visibly a successful demonstration of regression detection; it cannot be mistaken for a broken website or a passing target.
- Every displayed result and claimed captured frame traces to the stated local evidence. Explanatory highlights are clearly presentation, and incomplete evidence is not filled with invented output.
- Playback works on keyboard and touch, without global key interception, layout shifts, automatic looping, or motion requirements.
- The initial useful example remains visible when JavaScript or data loading fails. Browser interaction never claims to launch a real local terminal.

**Validation checks:** Reproduce both scenarios locally; compare spec, screen, diff, exit status, and artifact names with published data; test all control transitions including rapid repeated clicks, scenario switches mid-playback, page hide/show, and end/restart; inspect timer cleanup; test malformed/missing data, slow loading, JavaScript disabled, reduced motion, keyboard, screen reader, and narrow touch layouts.

### P0 — Give Playtestr a distinctive, consistent visual identity

**Design direction:** Make the website feel like a carefully typeset test report around a real terminal. Its distinguishing feature is that a reader can connect an action to a screen and then to an assertion or diff. This makes the product itself memorable without decorative effects.

**Locked visual constraints:**

- Preserve the existing palette: paper `#fffdf9`, ink `#252323`, muted text `#625e5c`, rules `#d8d2cd`, rust `#652d3c`, and terminal background `#292728`. Retain existing pass/diff semantic colors where contrast checks pass.
- Preserve the existing prompt mark and general type approach: readable sans-serif prose with monospace code, keys, filenames, and evidence labels. Do not add a dark-mode redesign or a theme switcher during this milestone.
- Use solid surfaces, fine borders, deliberate whitespace, restrained square or nearly square corners, and clear text hierarchy. No frosted glass, backdrop blur, decorative gradients, neon glow, unnecessary shadows, ornamental floating elements, or repeated generic card tiles.
- Distinguish actual product output from editorial labels. Do not put invented logs, invented adoption proof, or fake performance counters in the terminal.

**Specific identity choices:**

- Align spec line numbers and action labels with the corresponding terminal step; reuse the same small action markers in guides and example captions.
- Let the hero demonstrate the actual keyboard/screen workflow. Follow it with the regression diff, then the concrete local first test and exact platform evidence.
- Use compact evidence captions containing version, platform, and source link where relevant, rather than badges implying broad certification.
- Style examples and reference pages as part of the same family: file captions, consistent code-copy behavior, readable diff gutters, and source links in predictable places.
- Keep headings plain and product-specific. Avoid inflated launch language and filler sections added only to make the page longer.

**Affected files:** shared website templates, `site/style.css`, existing `site/favicon.svg` only if needed for consistency, social-preview source/assets, `README.md`, and `docs/website.md`.

**Acceptance criteria:** Home, documentation, downloads, examples, releases, and support visibly share one design; existing color tokens remain intact; the distinctive interaction is visible and useful; there are no prohibited glass/gradient effects or fabricated proof elements.

**Validation checks:** Review desktop and mobile screenshots of every page type together; compare color tokens against the existing CSS; inspect typography, code contrast, long headings, navigation alignment, and evidence captions; ask a first-time reviewer to explain what Playtestr tests and how the shown failure was detected, recording observations without turning them into an adoption claim.

### P0 — Define production readiness for the complete website

**Reasoning:** Production-ready here means users can reliably read, navigate, install, understand examples, and obtain help. It is an acceptance boundary for this static site, not a marketing claim about universal runner compatibility.

**Affected files:** `.github/workflows/pages.yml`, website templates/configuration/scripts, `docs/website.md`, and a new dated validation record under `docs/` when implementation is tested.

**Acceptance criteria and validation checks:**

- Build and link checks run on pull requests without deploying. Deployment uses the reviewed build only after an authorized publication step; inspect the actual deployment result rather than treating configured CI as proof.
- Validate every page type at 320, 375, 768, and 1440 CSS pixels, with text enlargement, browser zoom, keyboard, reduced motion, and screen-reader checks. Test documentation navigation and demo controls as carefully as the homepage.
- Per-page title, description, canonical URL, social metadata, active navigation, heading hierarchy, and useful 404 links are complete. Sitemap entries use public canonical routes and do not advertise internal build/source paths.
- Base paths, nested asset URLs, schemas, downloadable demo files, and heading fragments work on the real GitHub Pages project URL. Existing useful inbound links retain their destinations or receive static aliases where Pages permits.
- No runtime dependency on analytics, remote fonts, search services, or live GitHub API responses to render basic content. A GitHub API outage must not erase the locally configured download information.
- Set provisional transfer budgets: shared CSS plus initial JavaScript no more than 100 KB compressed; home first-load assets excluding deferred demo data no more than 500 KB compressed. Load demo data and search index only when needed. These are implementation budgets to measure, not current performance claims.
- Run repeated mobile-throttled performance checks on a deployed preview. Target LCP at or below 2.5 seconds and CLS at or below 0.1 in the recorded lab setup, and inspect interaction responsiveness. Label these lab observations; do not claim real-user Core Web Vitals or adoption statistics without field evidence.
- Check browser console errors, missing assets, slow/offline enhancement behavior, clipboard failure, and search/demo teardown. Content and ordinary links remain usable when optional features fail.
- Preserve the published release assets and exact checksums. Updating current web guidance never silently replaces a binary or rewrites historical evidence.
- Hand off a concise maintainer guide covering content sources, local preview, build/check commands, demonstration capture, release-link updates, and deployment recovery through a previously verified commit/artifact. No application backend or uptime SLA is added.

**Exit record:** List tested commit, website build-tool version, local/deployed preview URL, browser/device combinations, link/accessibility/performance results, captured demo provenance, native onboarding outcomes, and any unresolved issues. A P0 acceptance failure remains open. A screenshot alone, one desktop check, or a green build does not close the milestone.

## Scope guardrails

- Do not add cloud services, hosted dashboards, telemetry, package managers, SDKs, styled snapshots, runner recording/replay features, parallel execution, or autonomous game behavior. A finite website demonstration using reviewed example data is explicitly included; it does not expand the runner contract.
- Website-only static generation and small client-side modules for search, copy controls, and the terminal demo are included. Keep the output static and the current color theme; no frontend application framework, glass effects, or decorative gradient redesign is part of the plan.
- Do not claim universal terminal, framework, operating-system, architecture, Unicode, security, compatibility, performance, or adoption coverage.
- Keep the local runner, versioned JSON contract, evidence behavior, and trusted-target boundary as currently documented.
- Keep implementation work at the release boundary until independent-user evidence justifies a separate sprint.
