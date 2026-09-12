# Public presentation validation — 12 September 2026

## Scope

This record covers the local implementation of R5 public presentation at source commit `26fbda898347be14345dfa382227799ada0d2053` plus the uncommitted website and documentation changes in the working tree. It is local evidence, not a claim that GitHub Pages has deployed these bytes.

## Build and generated output

- Hugo: `v0.164.0-ce2470e7012b5ab5fc4e10ebe4027e9f8d9e00dc`, Windows amd64.
- Official Hugo archive checksum was compared with the published checksum before extraction into ignored `.tools/`.
- Node used for validation: `v24.7.0`.
- Command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\site.ps1 build`.
- Result: pass. Hugo generated 21 page objects and 18 HTML files; the validator found every required route, schema, demonstration file, and social image.
- Link, fragment, canonical URL, metadata, unique-title, search-index, release-data, color-token, prohibited-effect, and demonstration checks passed.
- Shared compressed CSS and JavaScript measured 7,362 bytes. Compressed home HTML plus that shared code measured 11,538 bytes. These are local generated-file measurements and exclude network protocol overhead and the deferred demonstration JSON.

## Browser matrix

- Browser: Google Chrome `152.0.7977.84`, headless through the Chrome DevTools Protocol.
- Host: Microsoft Windows NT `10.0.26200.0`, amd64.
- Routes: home, download, documentation start, installation, writing tests, snapshots, troubleshooting, spec v1, report v1, compatibility overview, platform evidence, terminal compatibility, examples, releases, v0.1.0 release, support, trials, and a missing route using the 404 page.
- Viewports: 320×812, 375×812, 768×1000, and 1440×1000 CSS pixels.
- Result: pass. No page-level horizontal overflow, empty page titles, duplicate/missing H1, missing skip links, or unnamed links/buttons were found.
- The mobile navigation opened from its labeled button.
- Documentation search returned results for `expect_not`.
- The terminal demonstration switched to the intentional failure, advanced to step 4, exposed `snapshot_mismatch`, and displayed the recorded diff.
- Reduced-motion emulation moved playback directly to the final state instead of animating through timed frames.
- With JavaScript disabled, the examples page retained the static terminal transcript and explanation.
- The browser accessibility tree contained no unnamed links or buttons on the inspected documentation page.
- Representative desktop and mobile screenshots were inspected from ignored `.cache/site-browser-final/`; the paper/rust theme, solid terminal surface, documentation layout, and mobile stacking rendered as intended.

This automated accessibility inspection does not claim complete WCAG certification or replace a manual screen-reader session. Keyboard-accessible native controls, visible focus rules, skip navigation, reduced-motion behavior, semantic landmarks, accessible names, and color-independent diff symbols are implemented and checked where automation can observe them.

## Local performance observation

The homepage was loaded at a 375×812 emulated viewport with 150 ms request latency, 200,000 bytes/second download throughput, 93,750 bytes/second upload throughput, and 4× CPU throttling. The local lab observer recorded LCP 104 ms and CLS 0.000. The request was served from localhost and may benefit from browser cache, so this is only a regression check against the R5 thresholds. It is not field data, a real-user Core Web Vitals claim, or evidence of public-host performance.

## Demonstration provenance

- Passing source: `examples/menu.json` and `examples/snapshots/diagnostics.txt`.
- Intentional failure source: `examples/snapshot-mismatch.json` against the same reviewed baseline.
- Capture host: Windows amd64.
- Source revision: `26fbda8`.
- Passing result: six steps passed and the spec passed.
- Intended failure: three steps passed; step 4 produced a snapshot mismatch, runner exit 1, the recorded actual screen, and the recorded unified diff.
- Browser state transitions reflect deterministic output from `cmd/demo`; line highlights and explanatory sentences are identified as website presentation.
- The browser never launches a PTY or arbitrary command. The public provenance text is `site/static/demos/README.txt`.

## First-test behavior

The current Windows amd64 source-built runner completed the install-smoke greeting sequence from `testdata/install-smoke/windows/`:

| Case | Expected | Observed |
| --- | --- | --- |
| Good | Exit 0 and six passing steps | Exit 0 and pass |
| Intended bad | Exit 1 with a bounded failed assertion and screen evidence | Exit 1, assertion timeout at step 4, cleanup confirmed, screen saved |
| Recovered good | Exit 0 and six passing steps | Exit 0 and pass |

The exact published v0.1.0 archives already have recorded native packaging and public-install evidence in `docs/platform-support.md`. This turn did not repeat the updated written walkthrough on native Linux or macOS hardware.

## Workflow validation

- `actionlint` v1.7.12 completed with no findings for `.github/workflows/pages.yml`.
- The workflow builds pull requests without deploying, and limits deployment to `main` pushes or an explicit manual dispatch.
- The workflow downloads the pinned Hugo v0.164.0 archive and verifies its published SHA-256 checksum before use.

Final review on 13 September 2026 repeated the site build, static validator, Go tests, Go vet, JavaScript syntax checks, and repository whitespace checks after the last documentation change.

## Open external validation

- Review the concrete local change before publication.
- After an authorized merge/push, inspect the deployed GitHub Pages URLs, nested-route refreshes, schemas, downloads, search, terminal controls, social preview, and 404 behavior.
- Verify or apply the prepared GitHub About description, homepage, topics, and social-preview image through repository settings.
- Repeat the current written first-test walkthrough on native Linux x86-64 and Apple silicon macOS when those hosts are available.
- Perform a manual screen-reader pass on at least one desktop/browser combination and record the observed navigation and announcements.

These open checks limit the evidence. They do not invalidate the local build and browser results, and they must not be reported as completed.
