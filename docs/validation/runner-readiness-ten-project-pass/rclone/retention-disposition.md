# Native evidence retention correction

The previous two-host collection expanded 53,224,661 bytes while Rclone
already retained approximately 26,192,414 bytes. That combined footprint
exceeded the 64 MiB project evidence limit. The post-compaction storage
observation alone did not expose this intermediate excess. This is a
collection-policy failure; the limit has not been increased.

The complete failed packet was indexed, deduplicated, archived and verified
before its expanded copy was removed. Generations 1–3 then received a
lossless XZ encoding. Each conversion verified identical decoded tar bytes,
every physical member hash, complete logical path coverage and unchanged
selected restores before deleting only the redundant gzip encoding. Original
indexes, failed attempts and gzip archive hashes remain immutable; each
`reencoded.json` binds its original archive and replacement archive.

The three replacements occupy 252,304, 301,080 and 346,696 bytes instead of
3,678,067, 4,452,272 and 11,507,659 bytes. Storage check
314edda53c4b47be80eab779e1b71ccd measured 19,214,979 retained Rclone bytes,
with no active target locally. These are logical byte observations, not an
OS quota or proof of an exact peak.

Further native collection must retrieve and independently audit one host at
a time, archive and verify that packet, then remove its expanded copy before
retrieving the other. Both audited receipts must bind identical completed
job metadata and source before the combined freeze is published. A partial
host audit grants no two-host admission. Storage checks remain required before
each collection; growing acceptance stops if its measured footprint cannot fit.
