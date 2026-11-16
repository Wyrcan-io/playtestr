# Runner readiness continuation checkpoint v160

## Cumulative status

The audited campaign remains **17/30 admitted**. Fzy's 480-run exact rc.8
matrix passed on the two declared native hosts, but independent artifact audit
and project admission review remain open. Pick's project audit and ledger
reconciliation are also pending.

## fzy exact-candidate final matrix

Run `43358562580` used the declared `final-archive` phase. Linux amd64 and macOS
arm64 each passed all 20 frozen scenarios twelve times (240 each, 480 total).
Both jobs built the reviewed pin, passed the 32-test upstream suite, installed
the exact frozen rc.8 archive, confirmed source restoration/removal and
descendant cleanup, and passed bounded storage with empty active/failed
inventories. Exact host artifact IDs, provider sizes/digests, source/target and
candidate hashes are retained in
`fzy/final-archive-run43358562580-v1.json`.

Retrieve each provider ZIP, check the published digest and reconstruct all
scenario, report, event, candidate, source and cleanup bindings with
`next20_fzy_artifact_audit.py`. Do not grant admission credit until that audit
and package/ledger review pass.

## Remaining

1. Audit the full fzy final matrix; then finish its three-source-fault suite,
   public authoring/update route, maintenance, applicable controls, model
   tamper controls and admission package.
2. Complete Pick's independent admission and reconcile the exact candidate
   ledger without counting historical candidate results twice.
3. Continue the remaining unique projects and inherited qualification gates to
   thirty complete admissions.
