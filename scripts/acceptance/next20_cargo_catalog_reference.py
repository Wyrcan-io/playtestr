"""Alias identical source-catalog bytes already in the audited retained packet."""
import hashlib
import json
import tarfile
from next20_check import RAW
from next20_packet_archive import verify
from readiness_evidence import immutable_json,sha256


def main():
    root=RAW/'cargo-generate';retained=root/'retained-native-v2';index_path=retained/'index.json';index=json.loads(index_path.read_text())
    archive=retained/'packets.tar.gz';local=root/'retained-source/dependency-source-catalog.json'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('required canonical retained packet changed')
    verify(archive,index['files'])
    name='native/40467049451/next20-cargo-linux-preflight/active/cargo-generate/dependency-source-catalog.json'
    expected=index['files'][name]
    with tarfile.open(archive,'r:gz') as stream:
        member=stream.getmember(name)
        if not member.isfile() or member.size!=expected['bytes'] or member.size>4*1024**2:raise ValueError('canonical source catalog member bound')
        data=stream.extractfile(member).read(4*1024**2+1)
    if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256'] or local.read_bytes()!=data:raise ValueError('local catalog not exact already-retained canonical bytes')
    immutable_json(root/'retained-source/dependency-source-catalog.reference.json',dict(schema_version=1,logical_file='retained-source/dependency-source-catalog.json',
        bytes=len(data),sha256=expected['sha256'],required_archive=archive.relative_to(RAW).as_posix(),required_archive_sha256=sha256(archive),
        required_index=index_path.relative_to(RAW).as_posix(),required_index_sha256=sha256(index_path),member=name,
        scope='Exact identical source catalog shared across native hosts, not unlike runtime/executable bytes. Required retained native packet remains counted, full independently verified, and must not be removed. Expanded duplicate removal pending.'))
    print('Verified full canonical native packet and exact identical source catalog; prepared mandatory alias, native duplicate removal pending')


if __name__=='__main__':main()
