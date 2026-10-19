"""Re-encode verified packet payloads with a larger lossless dictionary."""
import argparse
import gzip
import hashlib
import lzma
import tarfile

from readiness_evidence import RAW, immutable_json, sha256
from readiness_compact_native import physical_members
from readiness_new_control_matrix import read_json as load


def reencode(root):
    root.resolve().relative_to(RAW.resolve())
    if root.is_symlink() or getattr(root,'is_junction',lambda:False)():raise RuntimeError('linked retention root')
    index=load(root/'index.json',maximum=8*1024**2)
    verified=load(root/'verified.json')
    original=root/'packets.tar.gz'
    if (sha256(root/'index.json')!=verified['index_sha256']
            or sha256(original)!=index['archive_sha256']):raise RuntimeError('original archive changed')
    replacement=root/'packets.tar.xz'
    stream_hash=hashlib.sha256();total=0
    with gzip.open(original,'rb') as source,replacement.open('xb') as raw:
        with lzma.LZMAFile(raw,'w',preset=6) as destination:
            while block:=source.read(65536):
                total+=len(block)
                if total>256*1024**2:raise RuntimeError('decoded archive exceeds bound')
                stream_hash.update(block);destination.write(block)
    check=hashlib.sha256();observed=0
    with lzma.open(replacement,'rb') as source:
        while block:=source.read(65536):
            observed+=len(block)
            if observed>total:raise RuntimeError('replacement decoded bound')
            check.update(block)
    if observed!=total or check.digest()!=stream_hash.digest():raise RuntimeError('tar bytes differ')
    members=physical_members(index['files']);seen=set()
    with tarfile.open(replacement,'r:xz') as archive:
        for member in archive:
            if member.name not in members or member.name in seen or not member.isfile():
                raise RuntimeError('replacement payload coverage differs')
            expected=members[member.name];digest=hashlib.sha256();count=0
            with archive.extractfile(member) as source:
                while block:=source.read(65536):
                    count+=len(block)
                    if count>expected['bytes']:raise RuntimeError('replacement member bound')
                    digest.update(block)
            if count!=expected['bytes'] or digest.hexdigest()!=expected['sha256']:
                raise RuntimeError('replacement member bytes differ')
            seen.add(member.name)
    if seen!=set(members):raise RuntimeError('replacement omitted payloads')
    if replacement.stat().st_size>=original.stat().st_size:raise RuntimeError('no storage saving')
    immutable_json(root/'reencoded.json',dict(original_index_sha256=sha256(root/'index.json'),
        original_archive_sha256=sha256(original),replacement_archive_sha256=sha256(replacement),
        replacement='packets.tar.xz',tar_sha256=check.hexdigest(),tar_bytes=total,
        physical_members_verified=len(seen),logical_members_retained=len(index['files']),
        original_bytes=original.stat().st_size,replacement_bytes=replacement.stat().st_size,
        selected_restore='Original selected-restore payloads and their index remain unchanged.',
        preservation='Every tar byte and every logical payload hash preserved; only compression changes.'))
    # Both complete encodings were verified above. Remove only this exact owned
    # replaceable encoding; all original indexes and failures remain immutable.
    original.unlink()
    print('Verified lossless packet re-encoding:',replacement.stat().st_size,'bytes')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',choices=['rclone'],required=True)
    parser.add_argument('--generation',type=int,choices=range(1,101),required=True)
    args=parser.parse_args()
    reencode(RAW/args.project/('retained-native-v'+str(args.generation)))


if __name__=='__main__':main()
