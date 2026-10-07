# Selected-row snapshot format 1

The early real-project reliability candidate supports explicit viewport-row snapshots. Published archives and earlier source pins do not support this format. It is useful when a target displays a generated path or clock outside the interface contract being tested. Choose the omitted content deliberately; Playtestr does not infer masks, remove dynamic strings or approve expectations automatically.

In the recorder, after a meaningful readiness checkpoint:

```text
/snapshot-rows results.rows.json 2 24
/review
/replay
/save
```

Rows are inclusive and 1-based physical viewport rows, measured after the current resize. Entire rows are selected; no horizontal cropping, style comparison or new grapheme claim is introduced. Empty/whitespace-only selections, reversed/zero/out-of-viewport bounds and unready snapshots fail. Missing lower unused rows are treated as blank only within the actual viewport. Existing normalization preserves leading spaces/internal blank rows and trims trailing spaces/unused selected rows.

The exported ordinary v1/v2 step remains `{"snapshot":"results.rows.json"}`. Its baseline is a separate strict versioned UTF-8 JSON artifact:

```json
{
  "snapshot_version": 1,
  "first_row": 2,
  "last_row": 24,
  "text": "reviewed selected terminal text\n"
}
```

Unknown fields, multiple JSON objects, invalid versions/ranges, invalid UTF-8 and existing size/line limits are rejected. `.rows.json` is the reserved filename suffix that selects this reader. Ordinary `.txt` snapshots keep complete-screen semantics. If an old plain-text baseline happens to use `.rows.json`, rename it and its spec reference to `.txt` before using this candidate; it is not silently converted. No spec action or unknown field was added.

Review both the rows and text. An excluded row is not tested by this snapshot. Keep separate `expect` assertions for important facts outside the selected interval. A resize that makes the range invalid fails rather than truncating the comparison or passing with empty content.

Selected intentional updates use the existing command:

```text
playtestr test --update --snapshot results.rows.json test.json
```

It preserves the reviewed range/version, updates only the text and commits only after all steps and cleanup pass. A new row snapshot needs explicit metadata from recording or a reviewed file template before update; `--update` cannot guess its range. Change the range only by deliberate artifact editing or rerecording and review it as a test-contract change.

A mismatch compares the selected rows in its diff and preserves the full rendered viewport in failure evidence. JSON/HTML report versions and spec versions are unchanged. Artifact contents can still expose synthetic paths or anything the target prints; use trusted targets and review evidence for secrets. This format does not assert filesystem correctness or full-application coverage.

The measured motivating failure was Gdu's actual fresh replay with a different managed-workspace directory in the first rendered row. The fix is framework/application independent. Readiness, timeout, output limits, cleanup, memory limits and transactional export/update still use the existing runner.
