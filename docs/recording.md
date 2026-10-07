# Record and maintain a terminal test

`record` and `workflow` are source-candidate commands, added in P0–P2. Published stable/prerelease binaries do not acquire these commands automatically. Build the current source using [development](development.md); no account or network is needed for recording or replay.

From the repository root, build `bin/fixture` (`bin/fixture.exe` on Windows). The committed synthetic wizard fixture contains only `seed.txt`:

```sh
playtestr record --output examples/recorded/my-wizard.json \
  --name "Create a project" --fixture fixtures/wizard \
  --temporary-home --temporary-temp --timeout-ms 15000 \
  -- ../../bin/fixture wizard
```

Flags explicitly select argv, cwd or fixture/cwd, viewport, environment allowlist, per-step deadline, whole recording budget and output cap. Use `--help` for all choices. `--env NAME=value` deliberately stores that value in the reviewed test; `--inherit-env NAME` stores only a name. Operational inherited variables remain as specified in [environment/workspace contracts](workspaces.md). Relative v2 executable paths resolve from the exported spec directory; v1 paths resolve as in the ordinary runner. The setup preview shows the chosen output, argv, cwd, fixture, viewport and bounds. The target runs with your permissions; use explicitly trusted applications and synthetic fixtures.

The control console stays separate from target input. `/live` displays the rendered target viewport and forwards supported typing, plain paste and keys through its real PTY. Ctrl+G returns to the console; to send this literal control to a target, use `/text "\u0007"` at the console. There is no collision with a target while using console commands. `/key ArrowDown`, `/key Enter` and `/text "atlas"` also drive the target directly. Unsupported escape sequences, keys or encoding fail visibly; mouse, style assertions, arbitrary escape injection and advanced grapheme support are excluded. Windows supplementary-plane key events are rejected rather than silently corrupted. Paste is capped at 64 KiB, drafts at the existing 1 MB/1,000-step contract, and at most 100 snapshots / 16 MiB of retained snapshot data. Removing steps or rerecording prunes discarded candidate snapshots. Export includes the spec within the 16 MiB aggregate bound.

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

Use unique, meaningful content identifying the new state. The recorder rejects an anchor already present immediately before input, whitespace-only anchors and text appearing multiple times. `/absent previous content` requires an earlier positive observation and intervening input/resize. After input or resize, a snapshot needs a fresh text/disappearance/exit checkpoint. `/redraw` is optional and must immediately follow `/resize`; observed redraw and settling do not replace a checkpoint. No recorded sleeps or automatic normalization hide dynamic fields. Configure deterministic state in the target, or select a more useful assertion. Correctness and coverage remain the author's responsibility.

`/screen` inspects rendered text. `/review` shows the exact spec and each candidate snapshot, including potentially sensitive input/output. Nothing saves a raw draft automatically. A target can print secrets; review and Git review remain necessary. `/replay` closes capture, confirms cleanup, and uses the same ordinary runner against a fresh fixture/home/temp. Its first failed result and useful screen stay in memory for diagnosis after a later recovery. Fixture changes since setup invalidate the candidate. No replay failure writes a secret-bearing draft evidence file automatically.

`/save` requires review and a successful replay of the current candidate. It exclusively reserves new paths, writes snapshots first and spec last, and removes reserved files on an observed error/cancellation. Existing specs/baselines are refused. The explicitly chosen parent directory is canonicalized once (including macOS system `/var` links); output-file links and links/junctions subsequently introduced into canonical export paths are rejected. This is a runtime transaction; a machine/power loss can leave reserved/partial files and requires inspection, not automatic acceptance. Do not let another local process rewrite the export directories concurrently. `/quit` or Ctrl+C at the console exports nothing, restores terminal modes, and returns 130. Capture deadlines/output overflow stop an idle target as well. Cleanup errors remain errors and unconfirmed workspaces are retained for inspection.

Maintenance is practical and explicit: `/delete N`, `/move N M` or `/replace N {"expect":"..."}` edits 1-based steps, validates the entire resulting sequence and invalidates replay. `/rerecord N` keeps the first N steps, starts fresh and reconstructs the prefix before accepting a replacement suffix. `/rerecord 0` starts over. To maintain an existing exported spec, edit its ordinary JSON and use `playtestr test`; update only an intentional named snapshot with `test --update --snapshot name.txt spec.json`, then inspect the diff. The recorder does not bulk-overwrite an existing suite.

The wizard target checks its file before its success marker. The native acceptance harness also independently reads `result.txt` and compares it with the expected synthetic bytes while the recorder's managed workspace still exists, before replay/cleanup. That host-side oracle is bounded and specific to this example; it is not a new general filesystem assertion or a guarantee that an arbitrary target saved correct state. Existing independent state harnesses remain necessary for other applications. No postcondition hooks or new public spec version were added.

After successful rerecording, the console prints the resolved target and new working directory again. A managed workspace is recreated, so use this latest identity when independently inspecting synthetic saved state; the previous directory has already been cleaned up.

See [recorded examples](../examples/recorded/README.md), [workflow setup](generated-workflows.md) and [dated acceptance evidence](validation/p0-p2-2026-10-07.md). Operator measurements supply development evidence, not independent-user usability or campaign credit.
