"""Prove the stopped archive is exactly reproducible from the complete packet."""
import gzip
import hashlib
import io
import json
import tarfile

from next20_check import RAW
from readiness_compact_native import physical_members, verify
from readiness_evidence import immutable_json, sha256


def main():
    root=RAW/'cz-cli'
    failed=root/'compaction-attempts/linux-limit16-first'
    original=failed/'packets.tar.gz';complete=root/'retained-native-v3'
    index=json.loads((complete/'index.json').read_text(encoding='utf-8'))
    verify(complete/'packets.tar.gz',index['files'])
    if sha256(complete/'packets.tar.gz')!=index['archive_sha256']:raise ValueError('complete archive changed')
    names=[];total=0
    with tarfile.open(original,'r:gz') as source:
        for member in source:
            total+=member.size
            if not member.isfile() or member.size>16*1024**2 or total>128*1024**2:raise ValueError('partial archive bound/type')
            row=index['files'][member.name]
            data=source.extractfile(member).read(16*1024**2+1)
            if member.size!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('partial payload not exact member of full retained packet')
            names.append(member.name)
    if names!=sorted(physical_members(index['files']))[:len(names)] or len(names)>=len(physical_members(index['files'])):
        raise ValueError('stopped archive is not the actual strict packing prefix')
    buffer=io.BytesIO()
    class StoppedPacking(Exception):pass
    try:
        with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as packed:
                with tarfile.open(complete/'packets.tar.gz','r|gz') as source:
                    for position,member in enumerate(source):
                        if member.name!=names[position]:raise ValueError('full packet member order differs')
                        info=tarfile.TarInfo(member.name);info.size=member.size;info.mode=0o644
                        packed.addfile(info,source.extractfile(member))
                        if buffer.tell()>24*1024**2:raise ValueError('partial reconstruction bound')
                        if position+1==len(names):raise StoppedPacking()
    except StoppedPacking:pass
    data=buffer.getvalue()
    if len(data)!=original.stat().st_size or hashlib.sha256(data).hexdigest()!=sha256(original):raise ValueError('stopped archive cannot be reconstructed byte exactly')
    immutable_json(failed/'subset-verified.json',dict(schema_version=1,
        original_partial_sha256=sha256(original),original_partial_bytes=len(data),physical_prefix_members=len(names),
        full_archive_sha256=index['archive_sha256'],full_index_sha256=sha256(complete/'index.json'),
        full_packet='cz-cli/retained-native-v3',source_helper_sha256=sha256(__file__),
        recipe='Take the first physical_prefix_members sorted physical members of the complete verified packet. Pack TarInfo(name), size and mode0644 in PAX_FORMAT tar stream, gzip filename empty/mtime0. Raise inside the tar context immediately after the last prefix member, reproducing the original stopped stream without a normal tar footer. The enclosing gzip context finalizes normally on exception. Verified actual gzip bytes exactly equal the original stopped attempt.',
        exact_reconstruction_verified=True,ordinary_credit=0,
        scope='Only duplicate stopped compaction payload may be removed after this proof; all original attempt events, failure and byte-exact reconstruction recipe remain.'))
    print('Verified byte-exact stopped archive reconstruction:',len(data),'bytes,',len(names),'physical prefix members.')


if __name__=='__main__':main()
