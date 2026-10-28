"""Inventory an unusable generated encoding; every original input remains retained."""
import json
from next20_check import RAW
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256


def main():
    root=RAW/'cargo-generate';partial=root/'retained-native-v7/packets.tar.xz'
    if (partial.parent/'index.json').exists() or (partial.parent/'verified.json').exists():raise ValueError('completed retained packet cannot be disposed as incomplete')
    for generation in [2,6]:read_packet('cargo-generate',generation)
    if partial.is_symlink() or not 0<partial.stat().st_size<2*1024**2:raise ValueError('incomplete encoding ownership/bound differs')
    immutable_json(partial.parent/'incomplete-encoding-disposition.json',dict(schema_version=1,
        generated_file='packets.tar.xz',bytes=partial.stat().st_size,sha256=sha256(partial),
        complete_source_archive='cargo-generate/retained-native-v6/packets.tar.gz',complete_source_archive_sha256=sha256(root/'retained-native-v6/packets.tar.gz'),
        complete_source_index_sha256=sha256(root/'retained-native-v6/index.json'),canonical_dictionary_archive_sha256=sha256(root/'retained-native-v2/packets.tar.gz'),
        failed_engineering_attempt='0e69b6a25b324ff7b834b78caef43cc0',source_payload_and_first_failures_preserved=True,
        scope='Unusable partial output of an aborted compaction, never a completed packet or unique target/report input. Original complete source archive and canonical dictionary are fully verified. Original failed-command events/console remain; remove only this disposable generated partial file.'))
    print('Inventoried unusable partial encoding; every original report/input/runtime source remains fully retained')


if __name__=='__main__':main()
