# Rclone scenario review, revision 2

No twenty-case authoring has run yet. The original declaration remains intact;
`scenario-declaration-v2.json` defines the corrected native profiles. Each case
starts from its exact declared fixture bytes in a fresh managed workspace.
After target completion, public assertions check every declared file and full
directory entry set. E01 also checks initial config absence before any input.

| Case | User risk |
| --- | --- |
| N01 | A new local configuration is not saved correctly. |
| N02 | A new alias records the wrong local destination. |
| N03 | Renaming loses the configuration or leaves the old name. |
| N04 | Copying changes the original or produces an incomplete copy. |
| N05 | Deletion leaves a stale section or damages unrelated files. |
| N06 | Editing an existing alias discards the new destination. |
| N07 | Reviewing defaults loses an explicitly configured option. |
| N08 | A correction made during review is ignored when saving. |
| E01 | A missing config produces false readiness or is never created. |
| E02 | An invalid name produces an inaccessible configuration section. |
| E03 | Duplicate-name recovery overwrites pre-existing configuration. |
| E04 | A single-letter name violates the native drive-ambiguity policy. |
| E05 | Supported Unicode letters are changed or truncated in section names. |
| E06 | Outer input whitespace leaks into the saved name. |
| E07 | An empty required storage choice bypasses validation. |
| E08 | An invalid numeric choice selects an unintended backend. |
| E09 | A directory used as config is silently replaced or its data lost. |
| E10 | Discarding a proposal commits it or changes a pre-existing section. |
| E11 | A Unicode local path value or neighboring binary file is corrupted. |
| E12 | Resizing loses Unicode input or a stale anchor hides missing characters. |

Combined risks are E03 (duplicate/preservation), E09 (wrong type/nonzero exit/
nested preservation), E10 (cancel/pre-existing state), E11 (Unicode path/binary/
entry sets), and E12 (active Unicode/two resizes/fresh markers/saved name).

E09 deliberately uses a stable error assertion, exact exit 1, directory type,
unchanged child bytes and entry sets. Its error contains fresh paths/timestamps,
so it does not approve a volatile full-screen snapshot. Other cases capture the
live post-transition viewport. Public `/screen` inspection follows each named
prompt/result during authoring so the first wrong prompt is retained before
further input. These diagnostic controls supply no assertion oracle or credit.

Budgets remain 10 seconds per step, 120 seconds per target run and 180 seconds
per capture command. Windows has the basic `nounc` prompt, CRLF output and
single-letter rejection; Linux has LF output and single-letter acceptance.
The shared advanced description prompt applies to both local and alias storage.

The wizard does not expose document navigation or a long-content viewer. Cloud
credentials, network access through aliases, mounts, servers and encryption are
outside this profile. Source faults remain unselected until the complete
two-host contract freeze is independently reviewed and committed.
