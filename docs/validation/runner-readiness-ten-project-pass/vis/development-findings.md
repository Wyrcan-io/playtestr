# Vis development findings

First public route run `39063231477` succeeds on native Linux amd64 and macOS arm64. Independent event/source/binary/same-run state/cleanup verification: `9fab7e84f872493ab1dd1764f29296c3`. Three commands, sixteen recorder controls; no handwritten spec; human usability unmeasured.

Initial twenty-case authoring run `39063459858` passes fourteen independent captures/ordinary tests on each host; six failures are preserved in both native packets. No source fault has been selected.

- N02: inserting into a new document already leaves the editor's final newline; an additional Enter writes two. The independent byte review rejects the extra newline. Remove the extra Enter and keep the one-newline oracle.
- N04 and E10: disappearance must reference the exact previously asserted text. Waiting on an unasserted substring was rejected; unchanged old content also cannot establish fresh readiness. Assert disappearance of the complete changed line before redo/reload continuation.
- N06: the final pre-existing line is a stale readiness anchor after paste. Observe the new dirty marker and verify the complete exact saved file, including duplication.
- E06: Vis treats CR as content before LF; append-at-line-end inserts after CR. Prepend to the first line instead, retaining an independently specified exact CRLF file. No newline normalization.
- E09: an unknown command keeps the prompt active. The reviewed upstream prompt handler needs Escape to leave insert mode and another Escape to close that prompt, before editing the document.

These are authoring/oracle corrections. They do not establish a Playtestr repair or justify omitting failed controls. Revision two preserves the original declaration and all first failures. Native rerun and twenty-contract freeze remain pending.

Storage measurement initially attributed only the older nested artifact layout. The new Vis packets use a flat campaign layout; attribution now recognizes both without traversing links. Earlier observations remain historical undercounts for Vis. Global campaign totals already included those files.
