# Continuation checkpoint v61: Taskell native v3 readiness

Date: 9 November 2026. The campaign remains **5/20 new-project admissions on
rc.6; 15/30 cumulative**. Taskell remains open and unadmitted; the original ten
remain 0/10 requalified on rc.6.

## Exact Taskell candidate run `42562896979`

The corrected public authoring route passed on Linux and macOS. Both hosts passed
the pinned upstream suite and built the exact isolated native runtime. The
public-route receipts report successful ordinary use, selected-state
maintenance, Unicode relocation and workflow preview; the seeded diagnosis and
intended-change-before-maintenance controls failed as declared. Target copies
were removed, the native binaries were bound to their retained runtime
identities, and exact pinned source restoration and Stack-work cleanup passed on
both hosts.

The complete provider artifacts were streamed into memory; no ZIP was retained
locally. Provider SHA-256 and ZIP CRC checks passed. Every batch summary and
every candidate report was accounted for:

| Host | Batch summaries | Reports | Passing | Failing | Independent report hashes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Linux x86_64 | 12 | 252 | 250 | 2 | 252/252 |
| macOS arm64 | 12 | 252 | 252 | 0 | 252/252 |

The two Linux failures were N04 rename invocations in batches 3 and 6. Both
reports showed the renamed task and `NORMAL` mode after Escape, but the next `q`
did not exit within the five-second step deadline. The runner forced shutdown
and confirmed process exit; both workspaces were cleaned. The same case passed
in the other ten Linux batches and in every macOS batch, so this was preserved
as a repeatability failure rather than credited or retried.

The full evidence is in [Taskell exact attempt v43](taskell/final-series-attempts-v43.json).
Linux artifact `13650188171` has provider digest
`e3a37263cef4eb8b36df6034350202850e1dc3218670bb45a86a3a18c8e4a7e1`;
macOS artifact `13651333087` has provider digest
`520dbbe5e615ad47265b4dcc699b499f525971f58ca7883d3de2181c2eea8336`.
The run has zero admission credit.

## Native scenario revision v3

The N04 contract now waits for post-Escape navigation to move from `2/3` to
`3/3` and back to `2/3` before sending `q`. These observable checkpoints prove
that Taskell resumed accepting normal-mode input after the rename. The saved
file state and exit assertion remain unchanged. The new contract tree,
scenario hash, declaration and revision receipt are separately frozen as v3;
the v2 contracts and failed attempt remain immutable. A local two-test contract
integrity suite verifies the 21 frozen scenario hashes, declaration binding,
and that only N04 changed. It passes.

The exact native workflow now selects `--window v3` and runs the contract
integrity suite before the target build. Commit and push the scoped v3 packet,
then require the full public route, all 252 ordinary reports on each host,
verified artifact hashes, source/runtime identity and checked cleanup. Taskell
remains open until both native hosts and the remaining independent project gates
pass. Do not acquire project seven (`mg`) beforehand.

Unrelated untracked caches and Skim drafts remain untouched and unstaged. There
is no release, tag, PR, issue, discussion, outreach or paid infrastructure
action.

No 30/30 completion claim is made. Human usability remains unmeasured, and paid
admissions remain zero.
