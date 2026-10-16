# E3 fidelity investigation — 27 September 2026

Evidence availability: bulk raw records are local-only; see [the archive policy](README.md).

Accepted investigation and evidence-backed deferral; no wide-cell implementation
or new Unicode support. Owner/reviewer: Codex/self-review, not independent review.

[Native first-attempt campaign 36305941244](https://github.com/Wyrcan-io/playtestr/actions/runs/36305941244)
used Ubuntu 24.04 amd64 and macOS 15.7.9 arm64, Go 1.26.0, `-trimpath`, source
`54e8ee661000ea6f50353766e548819f6871b180`. Linux runner SHA-256:
`a07d62e1c23f162b4481a1cb6077af3bdda506fd221d0f9aae2320ac61f966b2`;
macOS: `6e5a1afe5d51a3bd8207b21dfd30e1508672d8b9b2c672c75578267e0f7cee8c`.
Micro commit `04c577049ca898f097cd6a2dae69af0b4d4493e1`, fzf commit
`a140afeb4d733cad3c96a56bf6db7e26853b6757`. The ledger (`e3-e4-observations-2026-09-27.json`, local evidence)
preserves exact binaries, inputs, fixture/spec identities and reports.

Both native hosts failed original MICRO-08 at step 3, assertion timeout, useful
`雪l alpha marker` screen and confirmed cleanup. Exact input is `e9 9b aa 20`,
not mojibake. Original geometry is 70×16 then 84×22, with explicit UTF-8 locale.
A separately labeled probe changing only the wide rendered expectation to
`alpha marker` passed save and the exact-file oracle on both hosts. That is input
and persistence evidence, **not a rendering pass or replacement accepted spec**.
The historical E1 failure remains intact. Native Windows' original MICRO-08
passed with a separately hashed development runner; this does not overturn Unix
results or prove general wide-cell layout.

Frozen fzf wide selection with repeated 60→45→60→80-column resize and its original
selected-record snapshot passed on both hosts. Combining-record filter/select
also passed. All ten native attempts remain: two unsupported rendering failures
and eight positive probes. No holdout ran. App-specific success does not certify
cursor layout.

The explicitly reviewed reduced fixed-cell contract makes Snow occupy two cells,
combining acute zero additional cells and ASCII one. `雪X` should end at zero-based
column 3; vt10x ends at 2. `雪 X`, CUP 1;4, then Z should give `雪 Z`; vt10x gives
`雪 XZ`. `éX` should end at column 2; vt10x ends at 3. ASCII control passes.
The selected expectations use [Unicode width guidance](https://www.unicode.org/reports/tr11/)
and [xterm CUP semantics](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html).
Unicode cautions that terminal width needs tailoring; this is not a universal
grapheme definition or an emulator majority vote. Pinned vt10x `parse.go` advances
every printable rune by one. The reduction plus source mechanism supports the
emulator-width hypothesis; the independent file oracle separates input/editing.

The reduced emulator answers CSI 6n through its configured writer, but the runner
does not connect replies to target input. Query-dependent flows remain unsupported.
Literal editor/wizard text input is not bracketed-paste support. No style, mouse,
emoji, key-encoding or query protocol was added.

Decision: retain the dependency and explicitly defer this family. Inserting spaces
in an adapter would mishandle erase, addressed redraw, wrapping and cell replacement.
A replacement needs its own ADR and native migration evidence. Workaround: use
exercised basic-character rendered assertions or a separately qualified app route
with exact persisted-state oracle; incorrect wide snapshots remain untrustworthy.
Impact/exclusion: reliable MICRO-08 wide fidelity on every host. Initial Linux/macOS
failures were deterministic. During E5's local Windows 50-test instrumented
suite, repeat 46 failed at the same step with `雪a alpha marker`; the unchanged
uninstrumented suite passed 50/50. Both first results are retained at
`artifacts/e5-windows-tree` and `artifacts/e5-windows-plain`. The Windows 120-cell
first pass remains an observation, not qualification of reliable wide rendering.
The already reduced one-rune/one-cell mechanism is platform independent; sampler
load is not a proved cause. The support claim excludes this cell even on Windows,
where intermittent ConPTY output can make the rendered text look correct.
Separately scoped resource suites use the previously frozen basic café/λ control,
with exact file oracle, and retain original inputs/failure. No wide assertion
was relaxed or promoted into a supported pass. Owner: maintainer. Revisit
when an adopter needs this exact task, starting with retained reduced cells. No
previously supported native behavior is silently removed.

After two pilots, five cells per host fit the six-hour/1-GiB budget. Actual native
jobs: 145 runner-seconds; compressed evidence: 7,384,148 bytes. Artifact digests
and 14-day expiry are retained in the ledger. Human effort is unknown; agent elapsed
work is not two human working days. Continue to E4.
