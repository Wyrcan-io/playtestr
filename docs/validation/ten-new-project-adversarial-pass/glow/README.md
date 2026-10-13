# Glow development validation - in progress

Pinned MIT source: `charmbracelet/glow` at
`8b0600fa445535b9c53194c0d4f7fe3cf700ef3e`.
[Pre-acquisition scope](scope.md) records intended workflows and resource bounds.
Go 1.27.0 builds the unmodified application with exclusively owned caches.

Six useful normal and six edge contracts have passed public recording/replay
and exact input-file preservation checks on local Windows and WSL. These do
not grant hosted native or final frozen qualification. Normal workflows select
an overview, read a nested Unicode filename, scroll a long document, switch
documents, render code/tables and use line numbers. Boundaries cover an empty
library, missing filter results, partial-filter cancellation, an empty document,
repeated resizing and overlong-input recovery. Ordinary snapshots retain body
rows 1-29; the intentionally empty document includes row 30 so its real identity
footer provides meaningful evidence rather than an empty passing snapshot.

The admitted deterministic profile is `TERM=screen-256color`,
`GLAMOUR_STYLE=dark`, `GLOW_TEXT_SIZING=off`, with mouse disabled. It avoids
legacy OSC color probing and optional OSC 66 sizing, which are outside the
documented terminal-reply contract. It still uses ordinary Markdown rendering;
no upstream application source is patched to qualify the profile.

Initial Linux startup failed its readiness deadline. Disabling text sizing
alone did not resolve it. A bounded direct real-PTY SIGQUIT diagnostic traced
the remaining wait to the legacy logger's foreground/background OSC probing.
The declared non-query profile initially also failed because Playtestr silently
overwrote explicit `TERM`. The general environment-precedence repair failed its
real v1/v2 PTY regression before the fix, then passed eighty cases on Windows
and eighty on WSL. All twelve unchanged Glow body assertions and snapshots,
plus separate exact-file checks, subsequently passed on both local hosts.
[Earlier contracts](historical-xterm-profile/normal-project.json) and actual
first failures remain retained. No terminal-reply support is claimed.

Other authoring failures were accurate: an accented filter query did not match
the target's accent-normalized filename keys; an unobserved disappearance
anchor was rejected; `over` already appeared in `overview.md`; repeated `Z`
substrings were ambiguous; and an empty-body row selection had no evidence.
Revised contracts use normalized queries, the actual positive no-files caption,
unique `Find:` anchors and the empty document's meaningful identity footer.
Protected input bytes and useful workflow intent remain unchanged.

[Actual Windows race output](first-failures/race-diagnostic-1791929940398223900-0-.owned-target-race.5032.txt)
proves a producer/consumer shared-buffer race in pinned Ultraviolet
`006e29f97886`. The separately race-instrumented pristine target completed the
visible first workflow but exited 66; its original executable hash remained
unchanged. Windows is unqualified despite ordinary green tests. The explicit
[host-plan adjustment](../native-host-adjustments.json) moves the provisional
fifth Windows gate to Yazi. Linux/macOS qualification and actual Yazi Windows
execution remain required. No upstream outreach or dependency patch is made.

The revised prepared public Linux route used four commands, twelve recorder controls
and zero JSON edits in 24.369 seconds; build time, prior engineering and warm
caches are disclosed confounders. Intentional selection maintenance, actual
snapshot failure, HTML diagnosis, a named update, ordinary recovery, spaced
Unicode relocation and suffix rerecord passed. Generated workflow setup must
export the target's owned directory through `GITHUB_PATH` for subsequent steps;
a setup subprocess's private PATH is insufficient. The generic exporter was
checked against an actual temporary control file without replacing prior bytes.

All three actual WSL source faults passed: wrong-document selection, broken
bottom navigation and silent input-document corruption. Exact source/binary
restoration and unchanged contracts were checked; ordinary/state recovery
passed. [Local fault evidence](local-fault-evidence/manifest.json) retains actual
reports, screens and the ordinary-green/independent-red corruption result.

Native run `38479009828` passed all three core/race jobs, including the new
environment control; standard run `38479009834` passed. Both application jobs
passed initial cases, independent checks and source faults, then accurately
failed the original structured-reference snapshot during repetitions. The
actual table sometimes had minimal-width columns at an actual 100-column
viewport. Pinned `Init` and `WindowSize` commands render concurrently without a
generation guard; out-of-order completion is the source-based explanation,
not an independently instrumented proof of the exact scheduling sequence.
[Actual failures](first-failures/initial-table-render.json) and the original
startup contract remain retained, and that startup layout is unqualified.

The revised useful table-reflow workflow explicitly resizes to 80 and 100
columns and asserts each distinct exact divider position before capture.
Ten fresh ordinary and ten separate state runs passed locally on WSL, with
load variation. Its final baseline is byte-identical to the original
(`c8a69f8b8de626b6f85e5c755c2eced8a589a4cae14b7e16aee4dd322500551d`);
no snapshot weakening, timing sleep, deadline increase or target-source repair
is used. Native qualification of that revised workflow remains required.

Run `38481093443` subsequently completed all twelve macOS workflows, 120
ordinary and 120 separate state repetitions, source faults/restoration and
owned teardown. Linux passed revised table reflow and the next workflows,
then failed viewport-dependent navigation immediately after a narrow resize:
the screen showed paragraph 66-74 and 92%, rather than the requested bottom.
That recipe sent `G` before the target processed its new height.
[The original contract](historical-unsynchronized-resize/edge-resize-scroll.json)
and actual failure remain retained. The revised contract uses the existing
observed `/redraw` action immediately after each resize before dependent keys.
Ten fresh ordinary plus ten separate state runs passed on WSL; its final-screen
baseline remains byte-identical
(`65a1118737a32007ce540536d909cd20a7651a4caca8312c7288c5d7e1d8ba2a`).
No target-source repair or deadline increase is used. Full native qualification
of the synchronized recipe remains required.

Run `38483613287` completed the full synchronized Linux qualification,
including 120 ordinary and 120 separate state repetitions, faults/restoration
and owned deletion. macOS later failed no-match recovery under load: its final
screen showed one applied `guide` filter result rather than the opened document.
Enter arrived while the previous filtered result array was still active.
[That actual failure](first-failures/native-macos-unobserved-filter-selection.json)
and all earlier selection contracts/assessments remain retained. Every affected
selection now asserts its freshly selected result marker before Enter, rather
than assuming input delivery means filtering has finished. All six final
baselines remain byte-identical; native requalification is still required.

The strengthened no-match route passed ten fresh ordinary and ten separate
state executions on WSL. The public route, suffix rerecord and meaningful manual
selection edit also passed again. That edit explicitly changes both its selected
result and opened-body checkpoints; the generic maintenance helper now accepts
paired repeated checkpoint arguments rather than silently inferring edits.
Earlier assessments remain in the retained historical package.

A shared Windows/WSL ledger acquisition reported transient missing-path while
the Windows collector wrote concurrently. The harness retries that condition
only while its parent exists and within the same ten-second deadline; it never
recreates a disappeared parent or steals a lock. The new reduced case failed
before the repair, and all seventeen calibrations passed on Windows and WSL
afterward. The interrupted original state probe remains uncredited. See
[the ledger repair](../core/ledger-drvfs-repair.json). Full native reruns of this
latest recipe and calibration remain pending.

Native Linux/macOS repetitions/restoration/teardown and final frozen
qualification are still pending. No style/color/mouse/OSC fidelity, network/editor/clipboard
integration, full application coverage or beginner usability is claimed.
