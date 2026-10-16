# Record and maintain a terminal test

`record` and `workflow` are source-candidate commands, added in P0–P2. Published stable/prerelease binaries do not acquire these commands automatically. Build the current source using [development](development.md); no account or network is needed for recording or replay.

Managed-fixture recordings now export [spec v3](spec-v3.md). After a meaningful
completion checkpoint or exact `/exit`, use `/file result.txt`, `/missing old.txt`,
`/directory output`, `/empty-directory cache`, or `/entries output`. Paths are
relative to the copied fixture root, including spaces without extra quoting.
`/file` captures at most 64 KiB of exact bytes; `/review` shows base64 in the spec
and an escaped preview of the first 256 bytes. Review the complete selected bytes
when the preview is truncated. Captured output is a candidate expectation: you
decide whether it is correct. `/replay` checks a fresh execution before `/save`.
Only selected paths are read; state expectations never change under screen
snapshot `--update`. Existing v1/v2 specs keep their original contract.

Failed requested controls remain unresolved until retried successfully or a
successful fresh `/rerecord`. To intentionally omit failed controls, use
`/discard-errors`, then review the resulting coverage and replay. A successful
unrelated checkpoint does not erase a failed file capture. Replay/export also
requires a positive completion checkpoint after the last input or resize; an
input-only draft cannot become a passing recorded test.

For an intended saved-file change, open `playtestr record --edit path/to/test.json`.
Use `/update-state N` for the 1-based existing state step, `/review`, `/replay`,
then `/save`. This reconstructs the prefix in fresh state, captures the selected
expectation, retains the suffix, and requires the full candidate to pass in
another fresh execution. It saves only the spec after checking that approved
files have not changed concurrently. Failed or cancelled saves leave approved
data intact. Existing screen files remain byte-for-byte unchanged; maintain
those separately with `test --update --snapshot name.txt`. A crash can leave an
uncommitted temporary file; it does not automatically approve candidate bytes.

From the repository root, build `bin/fixture` (`bin/fixture.exe` on Windows). The committed synthetic wizard fixture contains only `seed.txt`:

```sh
playtestr record --output examples/recorded/my-wizard.json \
  --name "Create a project" --fixture fixtures/wizard \
  --temporary-home --temporary-temp --timeout-ms 15000 \
  -- ../../bin/fixture wizard
```

Flags explicitly select argv, cwd or fixture/cwd, viewport, environment allowlist, per-step deadline, whole recording budget and output cap. Use `--help` for all choices. `--env NAME=value` deliberately stores that value in the reviewed test; `--inherit-env NAME` stores only a name. Operational inherited variables remain as specified in [environment/workspace contracts](workspaces.md). Relative v2 executable paths resolve from the exported spec directory; v1 paths resolve as in the ordinary runner. The setup preview shows the chosen output, argv, cwd, fixture, viewport and bounds. The target runs with your permissions; use explicitly trusted applications and synthetic fixtures.

Allow target startup and preparation to reach the actual checkpoint, including subprocess work such as local version-control operations. If capture times out, use `/screen` to inspect what was rendered; measure fresh runs before restarting with a different `--timeout-ms`, and keep the whole-run budget explicit. A progress banner alone does not prove readiness for input.

`/resize` changes the PTY dimensions; the application processes that change
asynchronously. Before sending keys whose meaning depends on the new viewport
(such as scrolling to the bottom), use `/redraw` immediately after `/resize`.
This exports the existing `wait_for_redraw` action: observed target output and
a bounded redraw window precede the input. Continue with a meaningful content
assertion before a snapshot. A resize-specific fresh layout assertion can also
establish the intended rendered geometry when no dependent input intervenes.

The control console stays separate from target input. `/live` displays the rendered target viewport and forwards supported typing, plain paste and keys through its real PTY. Ctrl+G returns to the console; to send this literal control to a target, use `/text "\u0007"` at the console. There is no collision with a target while using console commands. `/key ArrowDown`, `/key Enter` and `/text "atlas"` also drive the target directly. `Home`, `End`, `PageUp` and `PageDown` work through `/key` and live input, including native Windows console keys and common Home/End sequence variants. Unsupported escape sequences, keys or encoding fail visibly; mouse, style assertions, arbitrary escape injection and advanced grapheme support are excluded. Windows supplementary-plane key events are rejected rather than silently corrupted. Paste is capped at 64 KiB, drafts at the existing 1 MB/1,000-step contract, and at most 100 snapshots / 16 MiB of retained snapshot data. Removing steps or rerecording prunes discarded candidate snapshots. Export includes the spec within the 16 MiB aggregate bound.

For the wizard, enter:

```text
/expect Project name? (synthetic workspace)
/text "atlas"
/resize 100 30
/key Enter
/expect Confirm project atlas at 100x30; seed=synthetic
/snapshot my-confirm.txt
/text "y"
/expect Saved and verified atlas:synthetic
/exit 0
/snapshot my-saved.txt
/review
/replay
/save
```

Use unique, meaningful content identifying the new state. The recorder rejects an anchor already present before the first input in the sequence since the previous checkpoint and whitespace-only anchors. It waits within the configured step deadline for exactly one occurrence of a meaningful anchor; transient duplicates during redraw can resolve, while persistent duplicates fail with an ambiguity/deadline error. Readiness and uniqueness use the same observed screen. This permits typing a filter and then confirming it with Enter even when its new result renders before Enter. An unchanged caption present before that sequence still cannot prove the transition. A successful text/disappearance/exit checkpoint ends the sequence; fresh prefix rerecord reconstructs the same rule. `/absent previous content` requires an earlier positive observation and intervening input/resize. After input or resize, a snapshot needs a fresh text/disappearance/exit checkpoint. `/redraw` is optional and must immediately follow `/resize`; observed redraw and settling do not replace a checkpoint. No recorded sleeps or automatic normalization hide dynamic fields. Configure deterministic state in the target, or select a more useful assertion. Correctness and coverage remain the author's responsibility.

At startup, observe content showing that the initial view has finished loading
before sending the first navigation key. A title or selected filename can appear
while the application is still processing startup events. For a file browser,
check the selected file's preview and the completed list status as well as its
path. Choose checkpoints from the application's actual screen, then confirm
that fresh replay reliably performs the first action.

When an application temporarily leaves its full-screen view to run a command,
text can disappear before the application resumes accepting input. Before
sending another key, use `/expect` to observe a specific resumed-view prompt
that was absent from the command screen. Then check disappearance or navigate.
For previews and scrolling, assert the intended selection or viewport marker
when visible text alone could match an intermediate redraw. Review the fresh
replay before saving the test.

`/screen` inspects rendered text. `/review` shows the exact spec and each candidate snapshot, including potentially sensitive input/output. Nothing saves a raw draft automatically. A target can print secrets; review and Git review remain necessary. `/replay` closes capture, confirms cleanup, and uses the same ordinary runner against a fresh fixture/home/temp. Its first failed result and useful screen stay in memory for diagnosis after a later recovery. Fixture changes since setup invalidate the candidate. No replay failure writes a secret-bearing draft evidence file automatically.

`/save` requires review and a successful replay of the current candidate. It exclusively reserves new paths, writes snapshots first and spec last, and removes reserved files on an observed error/cancellation. Existing specs/baselines are refused. The explicitly chosen parent directory is canonicalized once (including macOS system `/var` links); output-file links and links/junctions subsequently introduced into canonical export paths are rejected. This is a runtime transaction; a machine/power loss can leave reserved/partial files and requires inspection, not automatic acceptance. Do not let another local process rewrite the export directories concurrently. `/quit` or Ctrl+C at the console exports nothing, restores terminal modes, and returns 130. Capture deadlines/output overflow stop an idle target as well. Cleanup errors remain errors and unconfirmed workspaces are retained for inspection.

Maintenance is practical and explicit: `/delete N`, `/move N M` or `/replace N {"expect":"..."}` edits 1-based steps, validates the entire resulting sequence and invalidates replay. `/rerecord N` keeps the first N steps, starts fresh and reconstructs the prefix before accepting a replacement suffix. `/rerecord 0` starts over. To maintain an existing exported spec, edit its ordinary JSON and use `playtestr test`; update only an intentional named snapshot with `test --update --snapshot name.txt spec.json`, then inspect the diff. The recorder does not bulk-overwrite an existing suite.

Use `/key Enter` for a logical Enter event between typed lines. Literal LF and
Enter are different terminal inputs; a target may interpret or ignore LF
differently across platforms. After Escape changes an editor mode or closes a
prompt, checkpoint the observed mode or a previously asserted prompt's
disappearance before typing the next command. This avoids treating Escape and
the following characters as one combined key sequence. For an intended input
change, explicitly adjust an associated content checkpoint when needed before
reviewing the resulting snapshot mismatch; do not weaken unrelated assertions.

The older wizard example checks its file before printing its success marker.
Its historical acceptance harness also independently inspected `result.txt`.
That evidence applies only to that example. For a general saved-file check in
the current source candidate, explicitly record `/file result.txt` after the
completion checkpoint. Spec v3 then checks those reviewed bytes in the ordinary
test's own workspace before cleanup. An independent probe from another run
cannot supply that same-execution proof.

After successful rerecording, the console prints the resolved target and new working directory again. A managed workspace is recreated, so use this latest identity when independently inspecting synthetic saved state; the previous directory has already been cleaned up.

For a deliberate limited screen contract, `/snapshot-rows name.rows.json 2 24` captures inclusive 1-based rows after the same readiness checks. Review the explicit range and selected text before replay/export. See [selected-row format and migration](snapshot-rows-v1.md); this source feature does not automatically normalize paths or timestamps and is unavailable in published archives.

See [recorded examples](../examples/recorded/README.md), [workflow setup](generated-workflows.md) and [dated acceptance evidence](validation/p0-p2-2026-10-07.md). Operator measurements supply development evidence, not independent-user usability or campaign credit.
