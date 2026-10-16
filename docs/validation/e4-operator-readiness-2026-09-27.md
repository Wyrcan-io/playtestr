# E4 operator execution record — 27 September 2026

Evidence availability: bulk raw records are local-only; see [the archive policy](README.md).

Status: **E4 accepted within the familiar-operator and scoped accessibility
boundary**. At this E4 checkpoint no final candidate was qualified; the subsequent
[E5 record](e5-qualified-readiness-2026-09-27.md) closes private qualification.
E3 closed through its
[investigated fidelity boundary](e3-fidelity-boundary-2026-09-27.md).

The [reproduction guide](../e4-operator-walkthroughs.md) and
machine observations (`e3-e4-observations-2026-09-27.json`, local evidence) retain four fresh-directory
journeys: fzf selector, create-vite stateful wizard, micro editor and Lazygit
repository tool. Selected final definitions accepted 52/52 executions: original
good, reviewed baseline adoption/review, code defect and recovery, plus two
synthetic maintenance changes each with unmodified failure, corrected good,
code defect and recovery. Eight changes are controlled realistic fixture/UI
patches, not eight upstream version upgrades. Helpers, commands, line edits,
source/package pins and whole-command durations are counted in the ledger.
Human first-use, authoring and diagnosis time is unknown; this is familiar
operator engineering, not independent adoption or blinded diagnosis.

Original failures remain visible. The first wizard baseline captured a volatile
managed-directory path and mismatched on review; the corrected baseline captures
the stable wizard prompt. A cp1252 source-reading error was fixed with explicit
UTF-8. Lazygit preparation initially copied an already mutated source file;
the owned variant was reconstructed from its pinned Git source before the
affected walkthrough, retaining both setup records. The original fixture and
reviewed corpus baselines were preserved. These are harness/authoring faults,
not product passes and not discarded attempts.

Six predeclared diagnosis cases accepted 6/6: persisted target-code error
(`unexpected_exit`, oracle step 2), invalid spec, missing runtime, live assertion
timeout, wrong exit and artifact setup failure before launch. The last is a
CLI artifact diagnostic, not an invented machine category. Existing native
regressions separately check primary and artifact/cleanup errors. No measured
human two-minute diagnosis claim follows from tool execution time.

Source installer tests exposed a real Windows body-read timeout defect.
The strengthened test failed before repair because cancellation was not
observed server-side. `ReadAsync` cancellation alone did not bound the stalled
body. The installer now tracks the whole-request budget and bounds every
wait by its remaining time; no renewed chunk allowance. Stalled and slow-drip
tests observed server cancellation at about 1.5 seconds for the one-second
request allowance, including shell/setup overhead. Before-fix attempts and
after-fix logs remain under `artifacts/e3-local/installer-timeout-r*.jsonl`.

[Source run 36307315138](https://github.com/Wyrcan-io/playtestr/actions/runs/36307315138)
passed full tests, vet, race, required event inventory, installer failures,
manual examples and report checks on Ubuntu 24.04 amd64, macOS 15 arm64 and
Windows amd64. [Public route run 36307330579](https://github.com/Wyrcan-io/playtestr/actions/runs/36307330579)
passed six old/public v0.4.0-rc.1 lanes. Those published bytes/action do not
contain the new source repair. Candidate public install verification is pending
separate publication; no tag, release or deployed site changed here.

Ordinary macOS CI subsequently exposed an intermittent lost final screen.
The original failure and deterministic reduction are retained in
[run 36307693286](https://github.com/Wyrcan-io/playtestr/actions/runs/36307693286).
macOS may discard queued output when the last slave closes. Retaining the
parent slave protects bytes; shutdown must also interrupt active reads and
writes. Linux retains the original EOF optimization. The delayed-reader test
was corrected after a native stack trace showed that reaping before reading
can itself wait during macOS target exit. A post-write side channel now proves
output was written before deliberately delaying the reader. Every cancelled
intermediate run stays identified in the final index; none counts as a pass.
[Native before/after run 36329407653](https://github.com/Wyrcan-io/playtestr/actions/runs/36329407653)
failed the synchronized delayed-reader regression against the earlier factory
and passed against the repair on macOS 15 and 26; twenty immediate-exit
repetitions passed on each. Linux passed both current controls.
[Final E4 native source run 36329364021](https://github.com/Wyrcan-io/playtestr/actions/runs/36329364021)
passed full tests/vet/race, required non-skipped focused events, installers and
manual examples on all three native hosts.
[Ordinary CI 36329407636](https://github.com/Wyrcan-io/playtestr/actions/runs/36329407636)
also passed all three hosts, including macOS 26. macOS now uses the existing
bounded final drain rather than the Linux immediate-EOF optimization; this is
a diagnosed performance tradeoff, with final-byte suite measurements still E5.

Offline HTML exported with relative evidence references passed hidden Edge
checks at 375 and 1440 pixels: Tab/Enter skip navigation, named accessibility
controls, no-JavaScript content, contrast/layout and no network requests.
An initial browser connection race and absolute artifact reference rejection
are retained; absolute references are intentionally rejected, so the recipe
uses relative paths. This is not a human screen-reader walkthrough. Broad
accessibility remains excluded; maintainer owns a later human/operator check.

Differentiation remains unmet. Accepted E2 task-level evidence records RW1
Playtestr about 1116 ms versus Atago 164 and Termlens 214 (loss); RW3 about
114 ms ties Atago 114 and beats Termlens 164. Selected correctness ties,
and total human effort is unknown. Count shared helpers, oracle and cleanup
glue; do not present two meaningful real-task advantages. No recorder/exporter
or extra convenience API was justified or added. Independent demand,
comprehension and voluntary retention remain A1 questions; outreach is held.
