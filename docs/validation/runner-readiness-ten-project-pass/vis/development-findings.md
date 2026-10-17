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

Revision-two run `39063744346` passes eighteen cases on each host, with N02 and E09 still rejected; both packets and source cleanup are retained. The earlier interpretation of N02 was incorrect: without Enter the file has no final newline; upstream `vis_insert_newline` explicitly inserts a second newline at EOF for the blank line. Revision three specifies a new named document without a final newline and independently checks those exact bytes. Neither previous byte mismatch is accepted as a pass.

E09 exposed an unobserved transition: consecutive Escape bytes followed by a printable key may be decoded as Alt input by the target. Use the documented insert-mode Ctrl-C alias, then Escape, then observe disappearance of the previously asserted command text before returning to document input. No sleep, dropped control, deadline increase or runner behavior change.

Corrected storage observation `4cffffa49c8f42a0921f21cb7565cfc6` attributes both native packet layouts: Vis 6,432,164 retained bytes, campaign 1,313,994,745, retained total 200,870,894; observations precede later small records. All declared caps hold.

Revision-three authoring and complete ordinary suites pass all twenty cases on both hosts in `39063981212`. Independent review `17f35fad7a66484aae0117da7d37ea6e` checks every public export, independently expected bytes, native snapshot/fixture identity, actual executable inputs, same-run assertions and cleanup. Canonical Linux contracts and exact freeze are now retained before fault selection. Initial review `2220ae55104d4968aed74bdaf047443d` mistakenly compared directory-entry set enumeration order; the corrected review compares the public exact-set semantics, rejects duplicates and leaves all frozen package bytes unchanged. Only the declared locale differs between native contracts; no saved-byte or snapshot normalization.
