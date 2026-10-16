# Validation reports and local evidence

This directory keeps concise engineering reports, reviewed test contracts,
snapshots, small synthetic fixtures, regression patches and selected result
summaries in the public source repository.

Bulk machine-generated evidence is local-only and ignored by Git:

- downloaded/collected native run trees (`native/`);
- repeated input/provenance manifests (`identities/`);
- attempt ledgers and test-event streams (`*.jsonl`);
- generated coverage history and all-attempt accounting JSON;
- historical `*-observations-*.json` packets directly in this directory.

Untracking these files does not delete their local contents. A fresh clone does
not contain them. Markdown references rendered as local evidence paths are not
public download links. A published report records its actual historical result;
having its summary does not let a fresh clone independently rerun the complete
historical evidence audit.

## Running tests and historical audits

The runner, ordinary Go tests, regression fixtures and harness source remain
tracked. Normal development and CI checks must not depend on the author's local
archive. New harness executions can create fresh ignored evidence.

Historical full-campaign collectors/auditors and the guarded all-ten freeze
require the original local archive, including native collections, identities,
ledgers and the generated coverage JSON at their recorded relative paths.
Restore those exact bytes before running those commands. Missing evidence must
refuse qualification; never replace it with a passing summary, empty ledger or
invented count. `scripts/acceptance/adversarial_coverage.py` can generate a new
control declaration, but cannot recreate old execution evidence.

The archive owner is responsible for retaining a separate recoverable copy if
needed. Ignored files are not a Git backup. Git clean operations that include
ignored files can delete them; do not run those against this workspace.

## Publication and storage

Public compatibility and reliability claims must stay within the linked reports'
scope. Full raw evidence is not promised as part of a source checkout or release
archive. Share a reviewed bounded evidence bundle separately if one is needed;
do not force-add the entire local archive to Git.

Ignoring evidence does not reclaim local disk space. Large expanded Actions
downloads and duplicated provenance should be inventoried, compressed or
deduplicated, then verified before removing task-owned expanded copies. Preserve
first failures, accepted-run identities, state oracles and cleanup receipts.

Old Git commits still contain previously tracked evidence. This change does not
rewrite history, make already public material private, or shrink historical
clones. History rewriting is a separate operation.
