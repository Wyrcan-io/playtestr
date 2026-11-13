# Runner readiness continuation checkpoint v150

## Audited count

The campaign remains at **17/30 admitted projects**. Pick is not admitted. Its rc.8 v10 development matrix is useful evidence but is one execution per scenario per host, with no project credit. Preserve all earlier admissions and the rc.7 E11 failures.

## Exact candidate

- Branch: `work/p0-p2-implementation`
- Runner fix and pinned candidate source: `78252c770635ec429e63e4b618e9c319af89c343`
- Candidate declaration/packet-audit commit: `7a67a796` (full revision in Git history)
- Three-host candidate receipt/Pick v10 commit: `178dcb2fc93a713b3b3bf5969db9fc1d1dda0865`
- Candidate installer fix/first Pick attempt receipt: `4a715c5ed6af207334e75581244672be85fdf088`
- Private candidate: `v0.4.0-rc.8`, series `native-exit-v3`, workflow run `43330369205`; Linux, macOS and Windows source/test/vet/race/package jobs passed. Per-host provider artifacts, exact archive/binary hashes, source readbacks and zero-credit freeze are recorded under this campaign's validation directory.

The runner fix encodes arrow keys as SS3 while application cursor mode is active and CSI in normal mode. A real-PTY regression exercises the actual mode switch. Pick v10 E11 now pages through the viewport and observes `item29` before selection.

## Pick v10 development evidence

- First attempt: run `43332960895` failed before scenarios because the candidate-series selector stopped at v2. Both hosts built Pick, passed upstream tests, downloaded rc.8, restored exact source and completed cleanup/storage checks; no scenario launched. The failed attempt receipt and both exact provider artifacts are retained, and their credit is zero.
- Corrected attempt: run `43333839727`, workflow head `4a715c5ed6af207334e75581244672be85fdf088`.
- Linux artifact `13996281785`, 1,285,076 bytes, SHA256 `d275922b219af178ea94c3a6c2342b73777840b8e9c586af4a9998411095e1f9`; 20/20 one-time scenarios passed. Pick source archive SHA256 `e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653`; built target SHA256 `687dcd78dacd8b4ca96eddb31e5bf308ca1d60dcd2731838589a67013ec38b7c`; rc.8 archive/binary hashes are recorded in the provider manifest.
- macOS artifact `13996432258`, 1,285,350 bytes, SHA256 `a3296940860c768fae783f75a3152a40db662c735c56c45a5532b79eb543e64e`; 20/20 one-time scenarios passed. Same exact source archive; built target SHA256 `8dacc5183cf65e276294c6bcfcdb76808232aa557a6acce4e27939a1e78aeaf9`.
- Both hosts completed upstream tests, installed the exact rc.8 archive, restored the source, confirmed no target processes remained, and reported empty active/failed storage inventories.
- Independent readback: `pick/development-audit-run43333839727-v1.json`; its auditor verifies provider ZIP identity and safety, 40 exact reports/events/consoles, scenario and fixture hashes, command identity binding for rc.8 and Pick's native build, positive steps/exact exits, source restoration, and cleanup. Auditor negative controls reject a mismatched provider hash and a traversal ZIP member.

## Owned retained packets and storage

Successful and failed Pick development provider ZIPs are retained locally only under `.runner-readiness-compaction-tmp/`; they are not public links and were not added to Git. The provider artifacts remain available from run `43333839727` through their recorded retention date. Current hosted observations: Linux combined raw 1,919,361,480 bytes / retained 999,279,002; macOS combined raw 1,919,031,478 / retained 998,949,000. These are per-host observations, not one additive peak.

## Next actions

1. Continue Pick package: attempt its reviewed public authoring path, validate the independent oracle, design and execute three real minimal faults with restoration, and complete variations and ordinary 12-repetition native matrices on the exact rc.8 archive.
2. Keep all first failures and raw packets; add independent receipts before counting any project.
3. Continue the remaining new-project packages and affected original-ten, old-migration, delivered-CI, archive-control, fresh-checkout, adversarial-auditor, storage and cleanup gates. Do not transfer rc.5/rc.7 credit to rc.8 without same-candidate evidence.
