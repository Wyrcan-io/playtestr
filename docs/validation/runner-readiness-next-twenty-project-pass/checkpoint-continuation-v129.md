# Runner readiness continuation checkpoint v129

Campaign remains **15/30 admitted projects**; `mg` is still **not admitted**. Current
branch is `work/p0-p2-implementation`, HEAD `7585bb3d0d6e4b7f00a4b64d27615f9eeeaa9806`.
The source fix and route-artifact retention change are pushed. User authorization
for scoped campaign commits, pushes, hosted Actions execution, monitoring and
artifact retrieval remains in effect.

## Completed since v128

- Corrected the mg route artifact upload to include the actual campaign
  `artifacts/.../identities/**` directory. The route receipt now preserves the
  failed first window separately from its repaired passing window.
- Standard hosted push run `42980303472` completed successfully: both N01 pilots
  and all 24 Linux/macOS final batches passed. Independent audit
  `mg/final-qualification-artifact-audit-run-42980303472-v1.json` verified 24
  provider artifacts (including native build receipts), 20 canonical scenarios,
  480 ordinary plus 24 separately receipted E10-branch executions, zero failed
  contract executions. It credits no project admission by itself.
- Route-only hosted run `42980338276` also completed successfully. Both passing
  runs' artifacts are retained under ignored `artifacts/.../mg/public-route-retrieved/`;
  raw provider ZIP sizes/digests and CRC were verified. The push-run artifact is
  ID `13837871916`, 332590 bytes, SHA-256
  `e5ed1849ade17f4fe863f3d6308da061867dc1ac8f1cff18e3e16fd094096ee0`; the
  route-only artifact is ID `13837178724`, 332587 bytes, SHA-256
  `d00fa8f805d186a8daea023cf7047f8cdd6cacb1952681ef878894c43b5cda14`.
- New independent route auditor `scripts/acceptance/next20_mg_public_route_audit.py`
  verified both artifacts: 9 ordered CLI invocations with positive lifecycle
  events, 9 console hashes, 7 content-addressed identity manifests, exact rc.6
  runner and mg binary hashes, first successful recorded/reviewed/replayed/saved
  spec and ordinary report, expected seeded diagnosis, selected file-state
  maintenance, exact initial fixture bytes, `Café 雪` relocation, delivery
  workflow preview, and four absent target copies. Audits are
  `mg/public-route-audit-run-42980303472-v1.json` and
  `mg/public-route-audit-run-42980338276-v1.json`; route-only credit is zero.
- The initial first-use window remains a failure (run `42830712855`, two shell
  invocations and 15 controls; target was not found before mode repair). The
  repaired passing window took three invocations and 15 controls. Runs
  `42840242945` (artifact lost executable mode) and `42883681805` (save-status
  anchor timeout) remain preserved. Beginner usability is unmeasured; route was
  agent-operated.

## Open gates and next actions

- `mg` remains unadmitted: complete independent-oracle/package closure, campaign
  retention and cleanup gates, current all-attempt reconciliation, and admission
  audit are still outstanding. The existing fault calibration audit is a
  separate retained run and has not gained fresh credit from run 42980303472.
- Latest local storage observation
  `artifacts/.../storage/f87f239f3377419faefc16e9a4f30a51/observed.json` still
  fails only `combined_retained`: 2,165,420,744 bytes vs 2,147,483,648 cap,
  17,937,096 bytes over. Do not delete failures. Prepare, read back, index and
  selectively restore evidence packets before checked removal; then rerun the
  storage audit and record a new observation. Earlier checkpoint v44 is not the
  current measurement.
- Next: reconcile v129 route and native artifacts into the project ledger and
  all-attempt journal; validate route-auditor negative handling; address the
  storage overage without discarding evidence; continue the remaining project
  packages and original-ten qualification. Do not raise the project count until
  a complete package passes every required gate.

## Workspace preservation

Preserve unrelated untracked paths: `.codex-go-cache/`, `.codex-test-tmp/`,
`.runner-readiness-compaction-tmp/`, continuation v117/v46 and the existing skim
readbacks/model-control files. New route ZIPs and native provider packets are
ignored raw campaign evidence. Do not run blanket cleanup.
