"""Verify self-contained retained packet payloads after lossless re-encoding."""
import argparse
import hashlib
import lzma
import tarfile

from readiness_compact_native import physical_members
from readiness_evidence import RAW, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def verify_retained(root):
    index=load(root/'index.json',maximum=8*1024**2);verified=load(root/'verified.json')
    encoded=load(root/'reencoded.json');removed=load(root/'expanded-removed.json')
    digest=sha256(root/'index.json')
    if (digest!=verified['index_sha256'] or digest!=encoded['original_index_sha256'] or digest!=removed['index_sha256']
            or index['archive_sha256']!=verified['archive_sha256'] or index['archive_sha256']!=encoded['original_archive_sha256']
            or index['archive_sha256']!=removed['archive_sha256']):raise RuntimeError('retained index/encoding/removal identity differs')
    if encoded['replacement']!='packets.tar.xz' or sha256(root/'packets.tar.xz')!=encoded['replacement_archive_sha256']:
        raise RuntimeError('replacement archive changed')
    if not removed['all_expanded_removed'] or set(removed['removed_runs'])!=set(index['runs']):raise RuntimeError('expanded removal scope differs')
    if any((RAW/'native'/run).exists() for run in index['runs']):raise RuntimeError('expanded native evidence remains')
    stream_hash=hashlib.sha256();total=0
    with lzma.open(root/'packets.tar.xz','rb') as source:
        while block:=source.read(65536):
            total+=len(block)
            if total>256*1024**2:raise RuntimeError('decoded archive exceeds bound')
            stream_hash.update(block)
    if total!=encoded['tar_bytes'] or stream_hash.hexdigest()!=encoded['tar_sha256']:raise RuntimeError('decoded tar bytes changed')
    members=physical_members(index['files']);seen=set()
    with tarfile.open(root/'packets.tar.xz','r:xz') as source:
        for member in source:
            if member.name not in members or member.name in seen or not member.isfile():raise RuntimeError('archive payload coverage differs')
            expected=members[member.name]
            if member.size!=expected['bytes']:raise RuntimeError('archive member size differs')
            result=hashlib.sha256();count=0
            with source.extractfile(member) as stream:
                while block:=stream.read(65536):
                    count+=len(block)
                    if count>expected['bytes']:raise RuntimeError('archive member exceeds bound')
                    result.update(block)
            if count!=expected['bytes'] or result.hexdigest()!=expected['sha256']:raise RuntimeError('archive payload bytes changed')
            seen.add(member.name)
    if seen!=set(members) or len(seen)!=encoded['physical_members_verified'] or len(index['files'])!=encoded['logical_members_retained']:
        raise RuntimeError('archive payload denominator differs')
    for name in index['selected_restore']:
        if sha256(packet_file(root/'selected-restore',name,4*1024**2))!=index['files'][name]['sha256']:
            raise RuntimeError('selected restore changed')
    return index


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['rclone'],required=True)
    parser.add_argument('--generation',type=int,choices=range(1,101),required=True);args=parser.parse_args()
    index=verify_retained(RAW/args.project/('retained-native-v'+str(args.generation)))
    print('Verified self-contained XZ packet retention:',len(index['files']),'logical payloads')


if __name__=='__main__':main()
