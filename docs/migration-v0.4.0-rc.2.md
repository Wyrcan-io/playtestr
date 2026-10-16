# v0.4.0-rc.2 migration and rollback

Evidence availability: bulk raw records are local-only; see [the archive policy](validation/README.md).

The [published prerelease](releases/v0.4.0-rc.2.md) passed public installation and
upgrade checks on all three native hosts. Use the matching native archive with its
exact [manifest hash](../release/e5-candidate-manifest.json), install beside the
existing binary and verify `playtestr version` before changing PATH. Do not
rebuild or relabel qualified bytes. Public-download and immutable-action checks
are recorded in [publication verification](validation/e5-publication-2026-09-28.md).

V1 specs/reports stay the default; v2 workspace/mixed reports remain opt-in.
Minimum workspace/report-v2 reader is v0.4.0-rc.1; older strict readers may reject
v2 and cannot safely downgrade it by changing a version number. Source minimum
Go version remains the go.mod contract; candidate builds used Go 1.26.0.

The side-by-side record (`validation/e5-observations-2026-09-27.json`, local evidence) exercised
retained v0.3.0-rc.1, public v0.4.0-rc.1 and private v0.4.0-rc.2 against unchanged
v1 pass/failure/recovery, strict rejection of v2 by v0.3, v2 success in both v0.4
readers, and old-v1/new-v2 offline report rendering. Reviewed baseline bytes
remained unchanged. Those were private upgrade-preparation checks; the subsequent native public
old-to-new upgrade separately passed and is linked above.

The source installer repair bounds stalled and slow-drip body reads; its action
commit and binary version are independent pins. Verified public action:
`Wyrcan-io/playtestr/setup-playtestr@ae97c62022966cde9699b26169b4dc6ef0a12439`,
`version: v0.4.0-rc.2`. Native invalid/corrupt/partial/network/stale-PATH/rollback
gates passed. Existing published action evidence remains attributed to its old
immutable commit and bytes.

Rollback by restoring the previous executable and PATH entry. Preserve v1
fixtures, reviewed baselines and failure evidence. Do not overwrite a tag,
release asset or baseline as a rollback. Wide-cell layout remains excluded
even if an individual Windows MICRO-08 attempt passes; use the separately
qualified basic-character route or a justified exact-state oracle instead.
