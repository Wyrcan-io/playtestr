# Public saved-state assertions

Decision, 16 October 2026; implementation in progress.

Existing spec versions 1/2 and report versions 1/2 have strict readers and
published consumers. Introduce spec 3 (required managed workspace, inheriting
v2 setup) and report 3. Old tools reject the spec before launch. Preserve older
spec/report contracts and generic screen update behavior.

`state` is one ordered action with `path`, `kind`, and kind-specific reviewed
expectations. Kinds: `file` (required `bytes_base64`, including empty string),
`absent`, `directory`, `empty_directory`, `entries` (required `entries` list of
immediate names). Inline base64 preserves every byte without external-baseline
path ambiguity. Recorder review must show a bounded escaped preview; reports
must never store expected or observed payloads. No implicit normalization.

Paths use portable slash-separated relative components, rooted at the copied
fixture (independent of workspace.cwd). `.` selects the root for directory
checks. Reject parent/dot components, absolute/drive/UNC/device paths, NUL,
backslashes, streams, Windows reserved names, trailing dots/spaces and links or
special entries. Use Go os.Root containment plus lstat/identity/type checks.
Targets are trusted: observation is not an atomic filesystem snapshot and
concurrent same-size writes cannot provide durability or complete race freedom.

Observation occurs once at the declared step, before cleanup. Authors must
first checkpoint completion or declare an exact exit. State assertions do not
poll or establish terminal readiness. Reads check cancellation and existing
output/exit failure boundaries. State actions share the existing 1,000-total-step
limit with terminal actions. Limit 64 KiB per selected file,
512 KiB expected aggregate, 256 immediate entries and 32 components per path.
No recursive traversal. Changed identity/metadata during reads fails closed.

Same-run evidence associates state observations with a fresh invocation ID and
workspace ID; it records only selected path/kind/outcome and sizes, never file
payloads or unselected entry names. Missing, wrong type/bytes/entries, unsafe,
unreadable, changing and oversized state remain distinguishable diagnoses.

Review/capture is explicit and fresh replay is mandatory before recorder export.
Editing a selected assertion invalidates replay and preserves other steps.
Generic snapshot updates cannot approve state expectations. Inline expectations
use the recorder's existing spec-last export transaction and bounds; crash
durability is not promised. Native permission/link/replacement tests remain
required before compatibility qualification.

20 October update: the original Broot large-tree case needs 527 ordered state
checks but only 15,192 expected bytes. The private rc.4 runner rejected it before
launch, and parser/real-PTY regressions fail on that limit. Remove the separate
100-state ceiling while retaining the existing 1,000-total-step ceiling, 512 KiB
aggregate expected-byte budget, per-file/path/entry bounds and all deadlines.
This expands accepted v3 inputs without changing assertion semantics or report
formats. Older private rc.4 binaries still reject these larger contracts;
their bytes and evidence remain unchanged. Rebuild native candidate archives
and bind later qualification to the new bytes. The original fixture and every
state expectation remain intact rather than splitting them across executions.
