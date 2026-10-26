"""Read back the original stopped gzip bytes after checked duplicate removal."""
import gzip
import hashlib
import io
import json
import tarfile

from next20_check import RAW
from readiness_compact_native import physical_members,verify
from readiness_evidence import immutable_json,sha256


def readback():
    failed=RAW/'cz-cli/compaction-attempts/linux-limit16-first'
    proof=json.loads((failed/'subset-verified.json').read_text(encoding='utf-8'))
    removed=json.loads((failed/'partial-payload-removed.json').read_text(encoding='utf-8-sig'))
    retained=RAW/proof['full_packet'];retained.resolve(strict=True).relative_to(RAW/'cz-cli')
    if proof['full_packet']!='cz-cli/retained-native-v3' or not removed['removed_duplicate_payload']:
        raise ValueError('unsafe stopped archive readback reference')
    if sha256(failed/'subset-verified.json')!=removed['reconstruction_proof_sha256']:
        raise ValueError('changed stopped compaction proof')
    index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
    if sha256(retained/'packets.tar.gz')!=proof['full_archive_sha256'] or sha256(retained/'index.json')!=proof['full_index_sha256']:
        raise ValueError('changed full stopped-prefix backing packet')
    verify(retained/'packets.tar.gz',index['files'])
    count=proof['physical_prefix_members'];names=sorted(physical_members(index['files']))[:count]
    if not 0<count<10000:raise ValueError('stopped prefix count bound')
    buffer=io.BytesIO()
    class StopPrefix(Exception):pass
    try:
        with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as packed:
                with tarfile.open(retained/'packets.tar.gz','r|gz') as source:
                    for position,member in enumerate(source):
                        if member.name!=names[position]:raise ValueError('stopped-prefix source order changed')
                        info=tarfile.TarInfo(member.name);info.size=member.size;info.mode=0o644
                        packed.addfile(info,source.extractfile(member))
                        if buffer.tell()>24*1024**2:raise ValueError('stopped readback bound')
                        if position+1==count:raise StopPrefix()
    except StopPrefix:pass
    data=buffer.getvalue()
    if len(data)!=proof['original_partial_bytes'] or hashlib.sha256(data).hexdigest()!=proof['original_partial_sha256']:
        raise ValueError('original stopped gzip bytes not exactly recovered')
    if (failed/'packets.tar.gz').exists():raise ValueError('stopped duplicate expansion still exists')
    return dict(original_partial_bytes=len(data),original_partial_sha256=hashlib.sha256(data).hexdigest(),
                full_archive_sha256=proof['full_archive_sha256'],exact_readback_verified=True)


def main():
    result=readback()
    immutable_json(RAW/'cz-cli/compaction-attempts/linux-limit16-first/read-back-verified.json',dict(schema_version=1,**result))
    print('Recovered exact original stopped gzip bytes from retained evidence:',result['original_partial_bytes'])


if __name__=='__main__':main()
