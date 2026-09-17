# Sprint 7 — Understand a failure in one offline report

Status: implemented and locally validated on Windows amd64 on 18 September
2026. The number is retained for existing links. Sprint 6 is not a
prerequisite. Published-binary verification remains a release gate;
independent maintainer adoption and outside feedback are intentionally deferred
until after Sprint 10.

## User result

A developer opens a failed run and immediately sees which test and step failed,
the captured terminal text, the relevant snapshot diff, and the cleanup outcome.
This same useful view becomes the memorable moment in the public demo.

The report is a self-contained HTML file produced locally from captured
evidence. It opens without a server, account, network, or target application.

## Entry cases and scope

Use two concrete tasks: a snapshot mismatch and an assertion timeout or early
exit. Start with existing fixtures and one available project reproduction;
record independent reviewer results separately when participants are available.
Document the questions a reviewer needs answered and the current effort.

Required: one report renderer using report v1 and its existing screen/diff
artifacts; clear failure navigation; portable offline output; bounded loading
and rendering; usable keyboard navigation and small-screen layout.

Later proposals: event histories, step checkpoints, continuous recording,
side-by-side style comparison, or automatic diagnosis. None is needed for this
milestone. Existing evidence can be made easier to understand without expanding
the terminal capture contract.

## Proposed command and first view

```text
playtestr report --input artifacts/results.json --evidence-root artifacts --output artifacts/report.html
```

Finalize flag names at checkpoint 7.1. The evidence root is explicit so a
downloaded report cannot request arbitrary files on the developer's machine.
Rendering accepts already captured evidence and never starts the target.

The first view contains:

- Overall pass/fail/cancelled/not-run counts.
- A compact list of failures, selected by stable spec identity.
- The selected failure's step, category, terminal dimensions, captured screen,
  and existing unified diff where available.
- Separate process exit, cleanup, and evidence-write outcomes.
- Missing evidence labeled where it belongs.

The ordinary view needs no knowledge of sidecars, emulator libraries, or schema
internals. Supporting metadata can sit behind native disclosure elements.
Passing tests remain available without displacing failures.

Do not recover omitted command arguments, typed text, or expected strings by
reading arbitrary specs. A timeout report can show its category, step, and
captured screen; it must label an expected expression unavailable if report v1
did not record it. Show no guessed history or root cause.

## Evidence, privacy, and resource contract

Use the current report v1 outcome model. No new timeline format, reproduction
manifest, or runner instrumentation is required. Reuse existing artifacts
rather than sampling a terminal again or silently comparing a newer baseline.

At checkpoint 7.1 define how an exported run keeps report references resolvable.
Reject references outside the chosen root, escaping links/junctions, network
URIs, input/output aliasing, and inconsistent spec/artifact association. Existing
v1 files may not prove artifact integrity; do not represent a readable file as
cryptographically verified capture.

Set bounded per-file and aggregate input/output limits before implementation:
provisionally 256 KiB per screen and 32 MiB for the whole generated document,
while honoring existing report/snapshot limits. Inspect file sizes and enforce
bounded reads as well. Validate limits against the selected tasks. Missing
optional evidence is visible; malformed input, path rejection, or a failed
requested output write returns a rendering error without changing test results.

Escape all text, paths, and diffs as literal content. Do not interpret terminal
OSC/ANSI as links or HTML. No CDN, telemetry, external fonts, or remote requests.
Embed the admitted screen/diff contents so the output can be moved as one file.
Write atomically and preserve any previous output if rendering fails.

Screens and diffs may contain application data. Make export explicit, use
synthetic examples, and tell authors what the HTML embeds before they share it.
Metadata continues excluding secrets, command arguments, and typed input.
Automatic sanitization is not promised.

## Implementation checkpoints

### 7.1 — Freeze the two tasks and the presentation

Sketch one small failure view from actual report/screen/diff evidence. Decide
path resolution, limits, output errors, missing-data labels, and command names.
Choose legible typography, aligned terminal text, restrained diff highlights,
and a visible first failing step consistent with the existing site.

Acceptance: every displayed fact has an identified captured source. The report
is useful with no timeline and no additional recording.

### 7.2 — Render existing evidence

Implement the Go renderer and command behind the artifact boundary. Keep test
outcomes unchanged. Handle one spec and a mixed suite, duplicate display names,
cancelled/not-run results, missing screens, and cleanup failure.

Acceptance: generated files are portable, offline, and readable with JavaScript
disabled. No target launches or baseline writes occur.

### 7.3 — Verify hostile and incomplete input

Cover traversal, absolute/remote references, escaping links, wrong versions,
malformed/truncated reports, oversized files, HTML/OSC text, unusual Unicode,
and unwritable/aliased output. Test only applicable filesystem paths on each
advertised host.

Acceptance: errors are bounded and understandable, original inputs survive,
and test results cannot be changed through the renderer.

### 7.4 — Review the actual user experience

Open the output in a browser on narrow and desktop viewports. Check keyboard
navigation, focus, contrast, terminal alignment, diff readability, literal
hostile text, and zero external requests. Long terminal lines may scroll within
their pane; the page itself should remain navigable.

Acceptance: a reviewer finds the first failing step and explains the captured
difference without parsing JSON. Record assistance and unanswered questions.

### 7.5 — Demonstrate and hand off

Use the [demo acceptance](../product-focus.md#demo-acceptance) with the same
generated report a user receives. Show a good run, controlled target regression,
correct failure, and restored good run. Preserve the bad run's evidence.

Acceptance: another developer can follow the documented export and inspect
workflow. Record technical completion separately from independent usability
and adoption outcomes.

## Definition of done

- [x] Both diagnosis cases render correctly from report v1 and existing files.
- [x] Input paths, aggregate sizes, output errors, and privacy are bounded.
- [x] Browser review proves offline usability, keyboard access, and portability.
- [x] Missing information stays visible; no inferred history or cause appears.
- [ ] Documentation and the demo use commands from an actual released version.
  The implementation is unreleased and is labeled accordingly; publishing a
  release was not authorized as part of this engineering change.
- [x] Independent review explicitly remains open. Per product decision,
  maintainer adoption and outside feedback resume after Sprint 10.

Review the next obstacle after delivery. Add history or reproduction machinery
only when an observed question requires new evidence.

Engineering evidence, source mapping, exact limits, hostile-input coverage,
browser checks, demo results, and the deliberately open release/adoption gates
are recorded in [Sprint 7 engineering validation](../../validation/sprint-7-engineering-2026-09-18.md).
