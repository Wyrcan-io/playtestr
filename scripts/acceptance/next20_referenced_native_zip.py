"""Retain native ZIP members directly with exact standalone local references."""
import argparse
import gzip
import hashlib
import io
import json
import lzma
import re
import stat
import tarfile
import zipfile

from next20_check import RAW
from next20_native_packet_reader import read_packet
from next20_native_zip_packet import download,payload_name
from next20_packet_archive import archive_path,verify
from readiness_compact_native import physical_members
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


ZIP_LIMIT=64*1024**2
FILE_LIMIT=32*1024**2
LOGICAL_LIMIT=128*1024**2
ARCHIVE_LIMIT=24*1024**2


def retain(payload,output,project,run,artifact,base_generation):
    if (not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',project) or not re.fullmatch('[0-9]{1,20}',run) or
        not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',artifact) or len(payload)>ZIP_LIMIT):raise ValueError('direct exact-reference scope/ZIP bound')
    match=re.fullmatch('retained-native-v([0-9]{1,4})',output.name)
    if not match or not 1<=base_generation<int(match[1])<=1000:raise ValueError('unsafe direct canonical generation')
    output.resolve().relative_to((RAW/project).resolve())
    for path in [RAW,RAW/project,output.parent]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked direct exact-reference root')
    base_index,base_payloads=read_packet(project,base_generation);base=RAW/project/('retained-native-v'+str(base_generation))
    if any(base_index.get(k) for k in ['external_exact_payloads','runtime_frame_disposition','solid_runtime_disposition']):raise ValueError('canonical reference chains not allowed')
    lookup={}
    for name,body in base_payloads.items():lookup.setdefault((len(body),hashlib.sha256(body).hexdigest()),name)
    headroom=min(ARCHIVE_LIMIT,64*1024**2-measure(RAW/project)['total_bytes']-2*1024**2)
    if headroom<=0:raise ValueError('no project-retained headroom for direct archive/index')
    output.mkdir(exist_ok=False);archive=output/'packets.tar.xz';files={};external={};canonical={};folded=set();total=0
    class Bounded:
        def __init__(self,stream):self.stream=stream
        def write(self,body):
            if self.stream.tell()+len(body)>headroom:raise ValueError('current archive exceeds measured retained-project headroom')
            return self.stream.write(body)
        def flush(self):return self.stream.flush()
    with zipfile.ZipFile(io.BytesIO(payload)) as source,archive.open('xb') as raw:
        if len(source.infolist())>20000:raise ValueError('provider entry count bound')
        with lzma.LZMAFile(Bounded(raw),'w',preset=6) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
                for entry in source.infolist():
                    name=payload_name(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
                    if entry.flag_bits&1 or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('encrypted/linked provider member')
                    if entry.is_dir():continue
                    logical='native/'+run+'/'+artifact+'/'+name
                    if logical.casefold() in folded or len(folded)>=10000 or entry.file_size>FILE_LIMIT:raise ValueError('duplicate or oversized provider member')
                    folded.add(logical.casefold());total+=entry.file_size
                    if total>LOGICAL_LIMIT:raise ValueError('provider logical payload bound')
                    with source.open(entry) as stream:body=stream.read(FILE_LIMIT+1)
                    if len(body)!=entry.file_size:raise ValueError('provider member length differs')
                    digest=hashlib.sha256(body).hexdigest();row=dict(bytes=len(body),sha256=digest);key=(len(body),digest)
                    reference=lookup.get(key)
                    if reference is not None:
                        if base_payloads[reference]!=body:raise ValueError('same-hash canonical payload byte comparison differs')
                        external[logical]=dict(row,canonical_logical_path=reference)
                    else:
                        if len(body)>16*1024**2:raise ValueError('unreferenced XZ payload exceeds explicit16MiB current-member bound')
                        member=canonical.setdefault(key,logical)
                        if member!=logical:row['member']=member
                        else:
                            info=tarfile.TarInfo(logical);info.size=len(body);info.mode=0o644;target.addfile(info,io.BytesIO(body))
                        files[logical]=row
                    if raw.tell()>ARCHIVE_LIMIT:raise ValueError('current exact-reference archive bound')
    if archive.stat().st_size>ARCHIVE_LIMIT or not folded:raise ValueError('empty/oversized current packet')
    verify(archive,files)
    required=dict(generation=base_generation,index_sha256=sha256(base/'index.json'),archive_sha256=sha256(archive_path(base,base_index)))
    index=dict(schema_version=3 if external else 2,compression='tar.xz',project=project,generation=int(match[1]),runs=[run],files=files,
        expanded_bytes=total,logical_files=len(folded),unique_payloads=len(physical_members(files)),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        max_file_bytes=16*1024**2,max_archive_bytes=ARCHIVE_LIMIT,measured_archive_headroom_bytes=headroom,
        provider_zip_sha256=hashlib.sha256(payload).hexdigest(),provider_zip_bytes=len(payload),
        expanded_payload_created=False,original_provider_zip_wrapper_retained=False,
        scope='Every actual provider logical payload retained exactly, current bytes plus mandatory standalone canonical bytes when referenced. Full original ZIP-member byte comparisons; no remote dictionary, reexecuted target or qualification decision.',
        **(dict(external_exact_payloads=external,required_canonical_packet=required) if external else {}))
    immutable_json(output/'index.json',index)
    immutable_json(output/'verified.json',dict(schema_version=1,index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(folded),physical_members_verified=len(physical_members(files)),external_exact_members_verified=len(external),selected_restore_verified=0,expanded_payload_created=False,expanded_removal_performed=False))
    _,restored=read_packet(project,int(match[1]))
    with zipfile.ZipFile(io.BytesIO(payload)) as original:
        expected={}
        for entry in original.infolist():
            if entry.is_dir():continue
            name='native/'+run+'/'+artifact+'/'+payload_name(entry.filename)
            body=original.read(entry)
            if restored.get(name)!=body:raise ValueError('complete direct original ZIP byte readback differs')
            expected[name]=True
    if set(restored)!=set(expected):raise ValueError('complete direct logical coverage differs')
    selected=next((n for n in restored if n.endswith('/N01.report.json') and len(restored[n])<=4*1024**2),
        next((n for n in restored if len(restored[n])<=4*1024**2),None))
    if selected is not None:(output/'selected-restore.bin').write_bytes(restored[selected])
    immutable_json(output/'complete-readback.json',dict(schema_version=1,index_sha256=sha256(output/'index.json'),members_compared_byte_exact=len(restored),
        external_exact_members=len(external),expanded_bytes_compared=total,selected_actual_payload=selected,
        selected_restore_sha256=sha256(output/'selected-restore.bin') if selected is not None else None,
        provider_zip_sha256=hashlib.sha256(payload).hexdigest(),expanded_payload_created=False))
    return index


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--artifact-id',required=True)
    parser.add_argument('--artifact',required=True);parser.add_argument('--generation',type=int,required=True);parser.add_argument('--base-generation',type=int,required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9]{1,20}',args.artifact_id):raise ValueError('unsafe provider artifact ID')
    output=RAW/'hatch'/('retained-native-v'+str(args.generation))
    if output.exists():raise ValueError('preserve existing native generation; no completed packet redownload')
    payload=download(['gh','api','/repos/Wyrcan-io/playtestr/actions/artifacts/'+args.artifact_id+'/zip'],ZIP_LIMIT)
    index=retain(payload,output,'hatch',args.run,args.artifact,args.base_generation)
    print('Direct original ZIP retained:',index['logical_files'],'logical files;',len(index.get('external_exact_payloads',{})),'exact canonical references;',index['archive_bytes'],'new XZ bytes; no disk expansion or admission.')


if __name__=='__main__':main()
