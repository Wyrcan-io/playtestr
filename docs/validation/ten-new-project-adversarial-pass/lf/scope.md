# lf scope declared before acquisition

Pinned MIT Go application: [gokcehan/lf](https://github.com/gokcehan/lf/tree/5d3c7b702515dfb72d8d496673fa1c4144d1dbed).
Native Linux and Windows are provisional. No source/runtime is acquired until
Copier's native evidence and owned deletion gates finish.

The pinned [command documentation](https://github.com/gokcehan/lf/blob/5d3c7b702515dfb72d8d496673fa1c4144d1dbed/doc.md)
documents built-in copy/cut/paste, rename, filtering and search. Use the supported
`-single` standalone client to avoid an ambient auto-started server and shared
clipboard. This excludes remote control and cross-client synchronization.
Verify that meaningful local file operations work in this mode before admission.
Use a tiny explicitly reviewed configuration, temporary home/temp and owned
synthetic directories; no shell command against a real repository or user files.

| ID | Useful flow / risk | Positive evidence and independent state |
| --- | --- | --- |
| normal-nested-search | Navigate to a nested directory and search a noninitial file | Actual selected filename/preview content, natural exit 0, exact original files preserved |
| normal-copy | Copy a selected file into another directory through built-in clipboard/paste | Destination appears after actual operation, exact source and copied bytes, protected neighbor unchanged |
| normal-move | Cut and paste a different file into a destination | Destination appears, exact destination bytes, source absent, protected state preserved |
| normal-rename | Rename a file to a spaced Unicode name using the actual modal input | New filename visible, new exact bytes, old name absent |
| normal-multiple-copy | Select a noncontiguous subset and copy it | Both intended files visible/present with exact bytes, unselected destination absent |
| normal-filter-sort | Filter mixed extensions, change documented sorting and recover the full view | Selected noninitial match and explicit restored listing; all files unchanged |
| edge-empty-directory | Enter an actually empty directory, recover to nonempty parent | Empty-state evidence followed by known parent item, no generated/missing state |
| edge-no-search-result | Search for an absent name and recover to a real match | Actual no-match diagnostic and later selected match, state unchanged |
| edge-cancel-rename | Edit rename text then cancel | Original filename restored visibly, no proposed filename, exact original bytes |
| edge-conflicting-rename | Attempt renaming onto an occupied different file; decline/recover according to actual target contract | Actual collision/rejection, both distinct contents preserved; never count a silent overwrite as success |
| edge-cancel-delete | Begin actual delete confirmation and cancel | Confirmation and recovered listing, exact selected and neighboring files remain |
| edge-resize-scroll | Repeatedly resize during navigation across bounded long content and Unicode names | Actual later selected file after small/large viewports, deliberate reviewed rows, unchanged state |

These are provisional behavioral intentions, not invented target output strings.
Read acquired code and explore the actual target before writing exact actions,
readiness, exits, supported ranges and oracle expectations. Reject an unsuitable
workflow explicitly and replace it with an equally substantive risk; preserve
Playtestr failures and fix them. At least five useful normal and five distinct
edge cases remain mandatory.

Default bounds: ten-second steps, 120-second scenarios, two-MiB terminal output,
64-MiB synthetic state, four-GiB owned target, 128-MiB raw evidence. Use small
fixtures with fixed names and exact known bytes. Time/date/owner/ambient path
fields need an explicit documented configuration or reviewed row exclusion;
never normalize them silently in the core. Exact file-state checks remain
separate from terminal assertions.

Two actual upstream source faults must affect observable navigation/file
behavior or status and be rejected with unchanged contracts. A genuine
copy/write corruption must preserve terminal green and be rejected by exact
state checks, followed by exact source/contract restoration. Choose sites only
after code review. The onboarding, meaningful suffix rerecord, manual edit,
selected baseline update, diagnosis, relocation, generated workflow, native
repetitions and verified owned deletion gates all apply. No completed-project
or platform credit is claimed by this scope declaration.
