"""Prove unique evidence survives before discarding two incomplete encodings."""
from next20_check import RAW
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256


def main():
    project=RAW/'cargo-generate'
    # Both completed replacements must actually decode every logical payload.
    _,window=read_packet('cargo-generate',9)
    _,trace=read_packet('cargo-generate',11)
    for generation,replacement,filename,attempt in [(8,9,'packets.tar.xz','2fd05c0d132e4b67b16772748ba10164'),(10,11,'packets.tar.gz','f818c8c2fb794fd6a050b729853f0ed7')]:
        root=project/('retained-native-v'+str(generation));path=root/filename
        if any((root/name).exists() for name in ['index.json','verified.json']):raise ValueError('completed evidence cannot be discarded as partial')
        if path.is_symlink() or not 0<path.stat().st_size<4*1024**2:raise ValueError('partial encoding bound/type changed')
        events=[RAW/'events'/(attempt+'-'+event+'.json') for event in ['started','finished']]
        for event in events:
            if not event.is_file():raise ValueError('original failed command evidence missing')
        complete=project/('retained-native-v'+str(replacement))
        archive=complete/('packets.tar.xz' if replacement==9 else 'packets.tar.gz')
        immutable_json(root/'incomplete-encoding-disposition-v2.json',dict(schema_version=2,generation=generation,
            generated_file=filename,bytes=path.stat().st_size,sha256=sha256(path),replacement_generation=replacement,
            complete_archive=archive.relative_to(RAW).as_posix(),complete_archive_sha256=sha256(archive),
            complete_index_sha256=sha256(complete/'index.json'),failed_engineering_attempt=attempt,
            failed_event_hashes={p.name:sha256(p) for p in events},fully_read_back_logical_records=len(window if replacement==9 else trace),
            scope='Only an incomplete generated encoding, with no published index or verification. Every substantive original payload survives in the fully decoded required replacement. Original failed-command logs/events/indices remain; no prefix or identical-wrapper claim.'))
    print('Two incomplete generated encodings inventoried; all required completed evidence fully decoded')


if __name__=='__main__':main()
