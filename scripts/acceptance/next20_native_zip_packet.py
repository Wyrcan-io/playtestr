"""Retain provider ZIP payloads directly, without a large disk expansion."""
import argparse
import asyncio
import gzip
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import re
import stat
import subprocess
import tarfile
import zipfile

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from readiness_compact_native import verify,physical_members
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure

ZIP_LIMIT=32*1024**2
FILE_LIMIT=16*1024**2
LOGICAL_LIMIT=128*1024**2
INDEX_LIMIT=2*1024**2


def payload_name(name):
    if not isinstance(name,str) or len(name)>4096 or name.startswith('/') or any(p in {'','.','..'} or ':' in p or '\\' in p or '\0' in p for p in name.split('/')):raise ValueError('unsafe provider ZIP member path')
    return PurePosixPath(name).as_posix()


def download(command,limit):
    """Capture binary acquisition in bounded memory; never print its contents."""
    process=subprocess.Popen(command,cwd=ROOT,env=owned_environment(),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=bytearray()
    try:
        while block:=process.stdout.read(65536):
            if len(output)+len(block)>limit:raise ValueError('provider artifact acquisition byte bound')
            output.extend(block)
        status=process.wait(timeout=10)
        if status!=0:raise ValueError('provider artifact acquisition failed, exit '+str(status))
        return bytes(output)
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=10)
        process.stdout.close()


def retain_zip(payload,output,project,run,artifact,archive_limit):
    if len(payload)>ZIP_LIMIT or not 0<archive_limit<=16*1024**2:raise ValueError('provider ZIP/retained archive bound')
    output.resolve().relative_to((RAW/project).resolve())
    for ancestor in [output.parent,RAW/project,RAW,RAW.parent]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked direct retention ancestor')
    output.mkdir(exist_ok=False);archive=output/'packets.tar.gz';files={};canonical={};folded=set();total=0;selected=None;selected_data=None
    class Bounded:
        def __init__(self,stream):self.stream=stream
        def write(self,value):
            if self.stream.tell()+len(value)>archive_limit:raise ValueError('retained archive would exceed measured project headroom')
            return self.stream.write(value)
        def flush(self):return self.stream.flush()
    with zipfile.ZipFile(io.BytesIO(payload)) as source,archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=Bounded(raw),mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as destination:
        if len(source.infolist())>20000:raise ValueError('provider ZIP entry bound')
        for entry in source.infolist():
            name=payload_name(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
            if entry.flag_bits&1 or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('encrypted/linked provider payload')
            if entry.is_dir():continue
            relative='native/'+run+'/'+artifact+'/'+name
            if relative.casefold() in folded or len(files)>=10000 or entry.file_size>FILE_LIMIT:raise ValueError('duplicate/oversized provider logical file')
            folded.add(relative.casefold());total+=entry.file_size
            if total>LOGICAL_LIMIT:raise ValueError('provider logical evidence bound')
            with source.open(entry) as member:data=member.read(FILE_LIMIT+1)
            if len(data)!=entry.file_size:raise ValueError('provider member expansion/CRC differs')
            record=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());key=(record['bytes'],record['sha256'])
            physical=canonical.setdefault(key,relative)
            if physical!=relative:record['member']=physical
            else:
                info=tarfile.TarInfo(relative);info.size=len(data);info.mode=0o644;destination.addfile(info,io.BytesIO(data))
            files[relative]=record
            if selected is None and (name.endswith('.report.json') or name.endswith('/report.json')):
                selected=relative;selected_data=data
    if not files or selected is None:raise ValueError('provider packet lacks actual report evidence')
    verify(archive,files);physical_members(files)
    restore=output/'selected-restore.bin'
    with tarfile.open(archive,'r:gz') as restored:
        actual=restored.extractfile(files[selected].get('member',selected)).read(FILE_LIMIT+1)
    restore.write_bytes(actual)
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('actual selected report restore differs')
    index=dict(schema_version=2,project=project,generation=int(output.name.removeprefix('retained-native-v')),runs=[run],files=files,
        expanded_bytes=total,unique_payloads=len(canonical),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        selected_restore=[selected],max_file_bytes=FILE_LIMIT,provider_zip_sha256=hashlib.sha256(payload).hexdigest(),provider_zip_bytes=len(payload),
        scope='Every original provider logical file/hash retained directly from bounded in-memory ZIP; exact aliases stay in-archive. No expanded packet or source payload deletion, no qualification credit.')
    encoded=(json.dumps(index,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    if len(encoded)>INDEX_LIMIT:raise ValueError('direct retained evidence index bound')
    immutable_json(output/'index.json',index)
    immutable_json(output/'verified.json',dict(schema_version=1,index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(files),physical_members_verified=len(canonical),selected_restore_verified=1,
        expanded_removal_performed=False,expanded_payload_created=False,selected_restore_logical_path=selected,
        selected_restore_sha256=sha256(restore)))
    return index


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--run',required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--artifact',required=True);parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project) or not (DOC/args.project/'source-provenance.json').is_file() or not re.fullmatch('[0-9]{1,20}',args.run) or not re.fullmatch('[0-9a-f]{40}',args.revision) or not re.fullmatch('[A-Za-z0-9_.-]{1,120}',args.artifact) or not 1<=args.generation<=1000:raise ValueError('invalid exact direct acquisition scope')
    destination=RAW/args.project/('retained-native-v'+str(args.generation))
    if destination.exists():raise ValueError('preserve existing retained generation')
    provider_result=await execute(['gh','run','view',args.run,'--repo','Wyrcan-io/playtestr','--json','status,conclusion,headSha,jobs'],
        'core','direct-native-provider-'+args.run,cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(provider_result['output'])
    if provider['headSha']!=args.revision or provider['status']!='completed':raise ValueError('provider source/run not complete and exact')
    metadata=json.loads(await asyncio.to_thread(download,['gh','api','repos/Wyrcan-io/playtestr/actions/runs/'+args.run+'/artifacts'],1024**2))
    artifacts=[a for a in metadata['artifacts'] if a['name']==args.artifact and not a['expired']]
    if len(artifacts)!=1 or artifacts[0]['size_in_bytes']>ZIP_LIMIT:raise ValueError('missing/ambiguous/oversized current provider artifact')
    project_size=measure(RAW/args.project)['total_bytes'];headroom=64*1024**2-project_size-INDEX_LIMIT-65536
    limit=min(16*1024**2,headroom)
    if limit<=0:raise ValueError('insufficient bounded retained project headroom')
    payload=await asyncio.to_thread(download,['gh','api','repos/Wyrcan-io/playtestr/actions/artifacts/'+str(artifacts[0]['id'])+'/zip'],ZIP_LIMIT)
    index=await asyncio.to_thread(retain_zip,payload,destination,args.project,args.run,args.artifact,limit)
    immutable_json(destination/'provider.json',provider)
    immutable_json(destination/'acquisition.json',dict(schema_version=1,run=args.run,revision=args.revision,artifact=args.artifact,artifact_id=artifacts[0]['id'],
        provider_zip_bytes=len(payload),provider_zip_sha256=index['provider_zip_sha256'],compressed_archive_stop_bytes=limit,
        project_bytes_before=project_size,expanded_native_payload_written=False,qualification_credit=0))
    print('Direct verified native retention:',len(index['files']),'logical files,',index['expanded_bytes'],'logical bytes ->',index['archive_bytes'],'retained bytes; no disk expansion')


if __name__=='__main__':asyncio.run(main())
