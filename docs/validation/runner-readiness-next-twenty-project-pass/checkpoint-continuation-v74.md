# Continuation checkpoint v74

## Campaign count

The campaign is still **15/30**. Five new-project admissions are credited; the
original ten have zero current-candidate requalification. mg has zero admission
credit.

## Completed and current mg work

The exact rc.6 N01 first-use journey passed once on Linux x86_64 and once on
macOS arm64 in run 42712723851. Independent artifact/report readback is recorded
in `mg/pilot-n01-native-readback-v1.json`; cleanup is confirmed on both hosts.

N02 is still a development probe. Run 42716663487 passed N01 again, then failed
the N02 save-confirmation expectation on both hosts. Its captured screen shows
that mg wrote the file and printed a message containing its absolute path; the
spec expected `Wrote notes.txt`. The assertion timed out, and the runner's
bounded cleanup had to force-stop mg; workspace and workflow-input cleanup were
confirmed. Preserve both reports and screens in the raw scenario tree. Provider
artifact digests match their retained local ZIPs. Full attempt details are in
`mg/scenario-development-accounting-v1.json`.

The N02 contract now expects the host-independent `Wrote ` prefix. Local focused
checks pass (13 total, four POSIX-only checks skipped on Windows), the workflow
YAML parses, and `git diff --check` passes. The corrected native retry has not
run yet. No scenario beyond the single first-use N01 pilot has qualified.

## Next work

Run the corrected N02 contract on Linux and macOS and inspect its exact-state
assertion and graceful target cleanup. Keep the original failure. After N02,
review each remaining candidate workflow against the pinned mg source, build
distinct scenario contracts with independent exact-byte oracles, and retain
every baseline, failure, repair, and host result. Do not freeze the 20-case
matrix or count N02 until its full native evidence is audited.
