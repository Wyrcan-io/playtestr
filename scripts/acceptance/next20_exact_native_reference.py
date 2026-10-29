"""Retain a complete packet using already retained byte-identical payloads."""
import argparse
import gzip
import io
import json
import re
import tarfile

from next20_check import RAW
from next20_native_packet_reader import read_packet
from next20_packet_archive import verify, archive_path
from readiness_compact_native import inventory, physical_members
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--run',required=True)
    parser.add_argument('--base-generation',type=int,required=True);parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project) or not 1<=args.base_generation<args.generation<=1000:raise ValueError('unsafe exact reference scope')
    old,canonical=read_packet(args.project,args.base_generation)
    if old.get('external_exact_payloads') or old.get('runtime_frame_disposition') or old.get('solid_runtime_disposition'):raise ValueError('canonical reference must be standalone')
    base=RAW/args.project/('retained-native-v'+str(args.base_generation));matches={}
    for name,row in old['files'].items():matches.setdefault((row['bytes'],row['sha256']),name)
    original,total=inventory(RAW,[args.run],16*1024**2);files={};external={};seen={}
    for name,row in sorted(original.items()):
        match=matches.get((row['bytes'],row['sha256']))
        if match:
            if (RAW/name).read_bytes()!=canonical[match]:raise ValueError('hash match was not byte identical')
            external[name]=dict(row,canonical_logical_path=match)
        else:
            row=dict(row);member=seen.setdefault((row['bytes'],row['sha256']),name)
            if member!=name:row['member']=member
            files[name]=row
    if not external or not files:raise ValueError('need both real current bytes and actual exact canonical references')
    output=RAW/args.project/('retained-native-v'+str(args.generation));output.mkdir(exist_ok=False)
    archive=output/'packets.tar.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:
            with tarfile.open(fileobj=zipped,mode='w|',format=tarfile.PAX_FORMAT) as bundle:
                for name,row in physical_members(files).items():
                    path=RAW/name
                    if sha256(path)!=row['sha256']:raise ValueError('current packet changed')
                    member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
                    with path.open('rb') as stream:bundle.addfile(member,stream)
                    if raw.tell()>16*1024**2:raise ValueError('current retained archive bound')
    verify(archive,files)
    required=dict(generation=args.base_generation,index_sha256=sha256(base/'index.json'),archive_sha256=sha256(archive_path(base,old)))
    immutable_json(output/'index.json',dict(schema_version=3,project=args.project,generation=args.generation,runs=[args.run],
        files=files,external_exact_payloads=external,required_canonical_packet=required,
        expanded_bytes=total,logical_files=len(original),unique_payloads=len(physical_members(files)),
        archive_bytes=archive.stat().st_size,archive_sha256=sha256(archive),max_file_bytes=16*1024**2,
        scope='Every original logical payload is retained byte-exactly, current bytes plus mandatory standalone local canonical bytes. All references were compared byte-for-byte before retention. No network reference, delta, source mutation, changed report or admission credit.'))
    immutable_json(output/'verified.json',dict(index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(original),physical_members_verified=len(physical_members(files)),external_exact_members_verified=len(external),
        selected_restore_verified=0,expanded_removal_performed=False))
    restored_index,restored=read_packet(args.project,args.generation)
    if set(restored)!=set(original) or any((RAW/name).read_bytes()!=data for name,data in restored.items()):raise ValueError('complete actual restored packet differs')
    selected=next(name for name in restored if name.endswith('.report.json'));(output/'selected-restore.bin').write_bytes(restored[selected])
    immutable_json(output/'complete-readback.json',dict(schema_version=1,index_sha256=sha256(output/'index.json'),
        members_compared_byte_exact=len(restored),external_exact_members=len(external),selected_report=selected,
        selected_report_sha256=sha256(output/'selected-restore.bin'),required_canonical_packet=required))
    print('Read back all',len(restored),'exact logical payloads;',len(external),'reuse already retained bytes;',archive.stat().st_size,'new gzip bytes; checked removal pending.')


if __name__=='__main__':main()
