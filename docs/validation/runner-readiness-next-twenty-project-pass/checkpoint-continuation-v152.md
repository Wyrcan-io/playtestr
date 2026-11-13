# Runner readiness continuation checkpoint v152

## Count and project position

The audited campaign count remains **17/30**. Pick is the 18th project slot and
is still unadmitted; this checkpoint records completed evidence gates but does
not change campaign counters. The project-ledger snapshot is stale and must be
reconciled against immutable admission receipts before any total is revised.

## Pick exact-candidate package

- Exact candidate: `v0.4.0-rc.8`, `native-exit-v3`; source pin
  `caae95938359b2e814b3e7406f396f486c9d99fb`.
- Development audit `43333839727`: 20/20 scenarios on Linux and macOS.
- Final archive audit `43336391685`: 240/240 cases per host, 480 total, with
  exact candidate/archive identities, source restoration and process cleanup.
- Fault audit `43341927666`: three distinct faults and nine phases per host,
  18 total. All mutations were rejected and pristine/restored targets passed.
  The initial F01 Down-key mutation was a false green and remains disclosed;
  the corrected PageDown fault is not represented as blind or held out.
- Public authoring route `43347165865`: passed and independently audited on
  Linux and macOS, including first-use recording, review/replay/save, diagnosis,
  maintenance, Unicode relocation and cleanup.
- Technical authoring route `43350106198`: passed and independently audited on
  both hosts, including suite selection, manual v3 editing, file-input
  preservation, JSON/HTML reports, v2 migration, suffix rerecord and cleanup.
- `next20_pick_model_controls.py` reconstructs the five exact-rc.8 audit
  receipts, verifies source/candidate/host/count/cleanup bindings, passes the
  positive model and rejects **17/17** semantic corruptions. Its immutable
  result is `pick/model-controls-v1.json`.
- Pick declares no application saved-state coverage; human usability remains
  unmeasured. Its generated workflow was reviewed as a preview and not run as
  delivered CI. Campaign delivered-CI triplets are separately evidenced for
  jrnl and Commitizen; they do not grant Pick project credit.
- All failed and superseded Pick attempts remain in
  `pick/public-route-attempts-v1.json`; successful routes do not erase them.

## Remaining work

1. Independently review Pick's complete project package and decide admission
   only after reconciling its selection, campaign ledger and candidate scope.
2. Continue with the next selected project; do not spend the campaign total for
   this model-control or route milestone.
3. Complete remaining project packages and all original-ten/current-candidate,
   old-migration, archive/control, fresh-checkout, storage, cleanup and campaign
   audits required by the execution prompt.
