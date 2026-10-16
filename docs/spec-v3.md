# Test specification version 3

Source candidate only. Existing published archives do not support this format.
Spec v3 retains [v2 workspace setup](spec-v2.md) and terminal actions, and adds
one ordered `state` action. Its [schema](../schema/playtestr-spec-v3.schema.json)
and [example](../examples/saved-state.json) accompany the implementation.

```json
{"state":{"path":"result.bin","kind":"file","bytes_base64":"AAo="}}
```

This expects precisely NUL then LF, including length and line endings. Use
`record /file result.bin` to capture candidate bytes without handwritten JSON.
Review the escaped preview and approve only intended bytes. Base64 is encoding,
not encryption; the selected bytes become part of the reviewed spec.

Other kinds are `absent`, `directory`, `empty_directory`, and `entries` with a
required `entries` array of immediate names. Empty arrays and empty files are
valid. Entry order is irrelevant; extra/missing entries fail, including hidden
entries. No recursive tree assertion or implicit normalization is performed.

Paths resolve from the copied fixture root, independently of `workspace.cwd`.
Use portable slash-separated relative names. `.` selects the root for directory
checks. Absolute, drive, UNC, traversal, dot components, backslashes, streams,
reserved Windows names, control characters and trailing dots/spaces are refused.
Links, junctions, reparse points and special files are unsupported and rejected.

A state step needs a successful screen checkpoint or exact exit assertion after
the last input/resize. It observes once at that step **in this execution**, before
cleanup; it never polls. If the target has exited, declare the exact exit before
checking state. A state check does not establish readiness for a screen snapshot.
Use a meaningful completion checkpoint to avoid inspecting an unfinished write.

Bounds: 100 state steps, 64 KiB per selected expected/observed file, 512 KiB of
aggregate expected bytes, 256 immediate directory entries, 32 path components,
and the ordinary step/run deadlines. Reads check cancellation between chunks.
No arbitrary shell hooks or application adapters execute assertions.

The runner uses rooted filesystem access and checks types/identities before and
after observation. Unix file opens also refuse final symlinks and use nonblocking
opens to avoid a replacement FIFO hanging. Windows uses rooted opens plus native
reparse checks. These are trusted-target checks, not a malicious-process sandbox.
Concurrent replacement/writes can invalidate an observation; this is neither an
atomic directory snapshot nor a durability/fsync guarantee. Native permission
semantics depend on the executing user's actual access rights.

Wrong bytes, missing/wrong-type/unreadable/oversized/unsafe/changing paths and
wrong entry sets fail with `state_assertion_failure` and a bounded diagnosis.
Output overflow, unexpected exit, cancellation, run deadline and cleanup retain
their separate outcomes. Reports contain selected path/kind and same-execution
identities, never selected file contents or unselected directory names. The
target's visible terminal output can still contain sensitive data.

To migrate, retain a managed v2 fixture, set `version` to `3`, then add explicitly
reviewed state steps at meaningful checkpoints. Older tools reject v3 before
launch. V1/v2 retain their behavior. Screen `--update` never changes state bytes.
New recordings refuse existing export paths. For selected file maintenance,
`record --edit test.json` opens approved expectations; `/update-state N`,
`/review`, `/replay`, `/save` updates only the chosen state expectation and
preserves unrelated screen files. A failed or cancelled save preserves the
approved spec. Concurrent edits require reopening. Native qualification beyond
the recorded Windows controls remains open.
