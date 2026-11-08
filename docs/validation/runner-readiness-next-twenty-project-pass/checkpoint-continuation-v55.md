# Continuation checkpoint v55: Skim V35 readback and Taskell native failures

Date: 9 November 2026. Overall admission remains **4/20 new projects (14/30
cumulative)**. No new project admission is granted by this checkpoint.

## Skim

V35 exact-candidate native run `42528435724` on commit
`4d61153840316a223e6d80d26ca94b0c893eb838` succeeded on Linux and Windows.
Provider-digest-bound artifacts, V15 readbacks, 480 positive ordinary cases,
480 reconstructed contracts, 18 fault phases, checked cleanup and 24 rejected
semantic corruptions across both actual cell models are retained in
[readback v15](skim-artifact-retrieval-readback-v15.json) and
[model controls v3](skim-model-controls-v3.json). This is a repeat of V34's
frozen candidate and earns no new unique breadth. Skim still lacks its formal
project admission and cumulative reconciliation; directional-key behavior and
raw NUL framing remain limitations.

## Taskell

The exact rc.6 V35 run `42528435710` is recorded in
[build attempt v35](taskell/build-attempt-v35.json). Linux built the pinned
target and passed its upstream suite, then failed E11M in eleven of twelve
batches; the sole pass used the separately declared wider viewport. The native
series has zero credit. macOS was blocked before target build by a harmless
`opt/local/etc` directory member in a signature-verified MacPorts package; the
cleanup step also failed because the target build receipt did not exist. No Mac
target case ran. The failure packet and run IDs/digests are preserved.

The earlier fault run `42528435700` is recorded in
[fault attempt v2](taskell/fault-attempt-v2.json). Linux uploaded a successful
but unaudited packet; macOS hit the same package-extraction and secondary
cleanup failures before target execution. No calibration credit is claimed.

Local fixes now accept safe, non-materialized directory metadata only below
`opt/local` and continue source identity/checked cleanup when no build receipt
exists. Focused tests were run from `scripts/acceptance`: 21 tests, 17 passed,
four skipped for Windows symlink capability. Python compilation, workflow YAML
parsing and `git diff --check` passed. An initial test invocation from the repo
root failed module discovery; the corrected directory-scoped invocation passed.
The fixes remain unverified on hosted Linux/macOS pending a new exact run.

## Storage and next actions

The last measured retained total is 2,148,345,666 bytes against a
2,147,483,648-byte cap, an overage of 862,018 bytes (about 0.82 MiB). Raw,
curated, project and combined raw measurements were within their declared
limits. Storage closure remains open; no acquisition or retention headroom is
claimed.

Next: stage only the reviewed Skim V15 evidence/model helper and Taskell fixes,
workflow changes and attempt records; preserve ignored local caches and the
untracked v46 checkpoint; commit and push to the already authorized branch;
monitor only the resulting standard hosted native runs; independently retrieve
and audit their artifacts. Do not grant Taskell or Skim admission until the
exact gates, cumulative reconciliation and storage closure pass. Continue the
remaining selected projects, original-ten rc.6 qualification, migrations,
controls, delivered CI, fresh-checkout and all-attempt closure afterward.
