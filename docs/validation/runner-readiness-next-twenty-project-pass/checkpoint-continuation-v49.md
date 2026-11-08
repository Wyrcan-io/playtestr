# Continuation checkpoint v49: 8 November 2026 20:23 UTC

Branch `work/p0-p2-implementation` is at pushed commit `86130173`. The campaign
remains **4/20 new projects admitted on rc.6 (14/30 cumulative)**; the original
ten have zero current-candidate requalification.

## Skim V32 outcome and V33 repair

V32 run `42517430006` completed on Linux and Windows and failed only at the
public maintenance route. Each host independently passed all 240 exact-archive
ordinary cases and all nine source-fault phases. The first-use route passed its
eight authoring controls in three commands, and seeded snapshot diagnosis
produced a useful failure. Maintenance then attempted to publish the changed
query over the already existing immutable `selection.json`; `immutable_json`
correctly refused the overwrite before another target launch. Relocation and
workflow preview were not reached. Both source/process checks, verified compiler
cache cleanup, target inventory preparation and checked target removal passed.

Readback v10 independently verified both provider ZIP digests, all 24 batch
hashes, 480 reports and finished receipts, passing step/status data, one exact
runner and target identity per host, and all 18 source-fault phases. V32 grants
no Skim admission. The complete raw archives were audited in memory and not
retained locally. See `skim/artifact-retrieval-readback-v10.json` and
`skim/candidate-native-attempts-v13.json`.

V33 now creates `maintenance/selection-maintenance.json` while retaining the
first-use `selection.json`; relocation uses the maintained spec. A focused
regression covers preservation and missing/ambiguous query refusal. The V33
immutable declaration binds staged workflow, planner, auditor, route and test
bytes under plan namespace v27. Focused Skim public-route and final-series tests
pass locally. V33 is staged and awaits final local checks, scoped commit/push,
then a fresh complete Linux/Windows exact-series, calibration and public-route
run. Do not count V32's passing ordinary/fault outcomes as V33 execution.

## Taskell remains open

Taskell has zero rc.6 credit. Its latest Linux exact series failed E11M in 11 of
12 batches and passed only at the enlarged viewport; retain this as an unresolved
output-observation/candidate issue. Do not weaken the contract or reorder steps
to hide it. Its latest MacPorts LLVM 12 run failed before target launch because
the owned runtime closure lacked signed-package `libxml2.16.dylib` and
`libz.1.dylib`. The paired Linux fault packet is not yet independently audited.

## Remaining campaign

Continue Taskell diagnosis and bounded signed dependency closure; then finish the
remaining selected projects, refresh all original ten on the claimed candidate,
run applicable old migrations, controls and archive journeys, deliver two CI
triplets, finish independent tamper audits, exact storage, fresh checkout,
cleanup, cumulative reconciliation and final docs. Keep the counter at 14/30
until a complete package passes. Preserve `.codex-go-cache/` and
`.codex-test-tmp/`; neither is campaign scratch. No PR, issue, discussion,
release, outreach, paid infrastructure or next campaign is authorized.
