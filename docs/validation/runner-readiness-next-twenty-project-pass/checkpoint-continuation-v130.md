# Runner readiness continuation checkpoint v130

Campaign remains **15/30 admitted projects**. `mg` remains unadmitted. Current
branch `work/p0-p2-implementation` has the two audited-route commits pushed; the
native matrix and route jobs used commit `7585bb3d0d6e4b7f00a4b64d27615f9eeeaa9806`.

## Verified since v129

- Native run `42980303472` passed on standard hosted Linux and macOS. Independent
  audit retained in `mg/final-qualification-artifact-audit-run-42980303472-v1.json`:
  24 cells, 20 scenarios, 480 ordinary plus 24 separately receipted E10 branch
  contracts, 504 total, zero failed. This does not add project-admission credit.
- Public route runs `42980303472` and `42980338276` passed and were independently
  audited. Their identities are present in the provider artifacts. The first
  route window still failed before target launch; the repaired route passed in
  three invocations with 15 controls. Beginner usability remains unmeasured.
- Storage overage was real: observation `f87f239f3377419faefc16e9a4f30a51`
  measured 2,165,420,744 retained bytes. Exact duplicate evidence was indexed,
  fully read back, and selected-restored before a single-shell PowerShell
  hash/path preflight and deletion of 11,728 aliases. Expanded text evidence was
  indexed, fully read back, selected-restored, then removed by
  `next20_text_evidence_remove.ps1` after verifying all 25,601 source hashes,
  lengths, containment and parent directories. Both packets pass post-removal
  verification. Details are in `index-compaction-v2.json`.
- Latest storage observation `bd092b4cdce74c10aa8bfa3910546d4f` passes all caps:
  combined retained 2,071,511,801 bytes (75,971,847 headroom); raw, curated and
  project totals are in `storage-checkpoint-v45.json`. The live mg source root
  remains deliberately retained and is reported separately.
- `test_next20_compact_index.py`: 2 passed. `test_next20_mg_public_route.py`:
  4 passed, one Unix execute-bit case skipped on Windows. Python compilation and
  `git diff --check` passed for the route auditor and compaction tooling.

## Remaining work

Do not advance the count. The mg native and public route gates are evidenced,
but full package admission, remaining independent-oracle/closure audit, current
all-attempt reconciliation and original-ten qualification remain open. The 20
new-project goal still requires completion of the unqualified packages and all
campaign-wide delivery, control, migration, cleanup and fresh-checkout audits.

Preserve unrelated untracked `.codex-go-cache/`, `.codex-test-tmp/`,
`.runner-readiness-compaction-tmp/`, continuation v117/v46, and existing skim
readbacks/model-control files. The v2 duplicate/text evidence packets and raw
provider ZIPs live under ignored campaign artifacts. Never run blanket cleanup.
