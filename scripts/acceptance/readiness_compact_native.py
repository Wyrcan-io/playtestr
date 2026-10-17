"""Verified, self-contained compaction of selected owned native evidence packets."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile

from readiness_evidence import RAW, immutable_json, sha256


def inventory(root,runs,max_file_bytes=4*1024**2):
    files={};folded=set();total=0
    for run in runs:
        if not re.fullmatch(r'[0-9]{1,20}',run):raise ValueError('invalid native run')
        selected=root/'native'/run
        for ancestor in [root,root/'native',selected]:
            if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked native evidence root')
        if not selected.is_dir():raise ValueError('missing native evidence root')
        for directory,dirs,names in os.walk(selected,followlinks=False):
            for name in dirs+names:
                path=Path(directory,name)
                if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked native evidence entry')
            for name in names:
                path=Path(directory,name);relative=path.relative_to(root).as_posix()
                if not path.is_file() or path.stat().st_size>max_file_bytes:raise ValueError('native evidence type or file bound')
                if relative.casefold() in folded:raise ValueError('ambiguous native evidence path')
                folded.add(relative.casefold());size=path.stat().st_size;total+=size
                if len(files)>=40000 or total>128*1024**2:raise ValueError('native compaction inventory bound')
                files[relative]={'bytes':size,'sha256':sha256(path)}
    return files,total


def physical_members(files):
    """Resolve one-level in-archive aliases; no external dictionary or chains."""
    members={}
    for name,record in files.items():
        member=record.get('member',name)
        for value in [name,member]:
            if not isinstance(value,str) or len(value)>4096 or value.startswith('/') or any(
                p in {'','.','..'} or ':' in p or '\\' in p or '\x00' in p for p in value.split('/')):
                raise ValueError('unsafe archive alias path')
        if member not in files:raise ValueError('archive alias lacks canonical member')
        canonical=files[member]
        if canonical.get('member',member)!=member:raise ValueError('archive alias chain/cycle')
        if record['bytes']!=canonical['bytes'] or record['sha256']!=canonical['sha256']:
            raise ValueError('archive alias payload mismatch')
        members[member]=canonical
    return members


def verify(archive,files):
    members=physical_members(files)
    seen=set()
    with tarfile.open(archive,'r:gz') as source:
        for member in source:
            if member.name not in members or member.name in seen or not member.isfile():raise ValueError('archive coverage/type mismatch')
            expected=members[member.name]
            if member.size!=expected['bytes']:raise ValueError('archive size mismatch')
            digest=hashlib.sha256();size=0
            with source.extractfile(member) as stream:
                while block:=stream.read(65536):
                    size+=len(block)
                    if size>expected['bytes']:raise ValueError('archive payload bound')
                    digest.update(block)
            if size!=expected['bytes'] or digest.hexdigest()!=expected['sha256']:raise ValueError('archive payload mismatch')
            seen.add(member.name)
    if seen!=set(members):raise ValueError('archive omitted evidence')
    with gzip.open(archive,'rb') as stream:
        total=0
        while block:=stream.read(65536):
            total+=len(block)
            if total>256*1024**2:raise ValueError('archive stream bound')


def compact(root,project,runs,max_file_bytes=4*1024**2,*,generation=1):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',project) or len(set(runs))!=len(runs) or not 1<=generation<=1000:raise ValueError('invalid compaction scope')
    for ancestor in [root,root/project]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked compaction destination')
    (root/project).resolve().relative_to(root.resolve())
    files,total=inventory(root,runs,max_file_bytes)
    canonical={}
    for relative,record in sorted(files.items()):
        key=(record['sha256'],record['bytes'])
        member=canonical.setdefault(key,relative)
        if member!=relative:record['member']=member
    members=physical_members(files)
    output=root/project/('retained-native-v'+str(generation));output.mkdir(exist_ok=False)
    archive=output/'packets.tar.gz'
    with archive.open('xb') as destination:
        with gzip.GzipFile(filename='',mode='wb',fileobj=destination,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
                for relative,record in sorted(members.items()):
                    path=root/relative
                    if sha256(path)!=record['sha256']:raise ValueError('source evidence changed')
                    member=tarfile.TarInfo(relative);member.size=record['bytes'];member.mode=0o644
                    with path.open('rb') as source:target.addfile(member,source)
                    if destination.tell()>16*1024**2:raise ValueError('compressed evidence bound')
        destination.flush();os.fsync(destination.fileno())
    if archive.stat().st_size>16*1024**2:raise ValueError('compressed evidence bound')
    verify(archive,files)
    selected=[]
    for run in runs:
        matches=sorted(name for name in files if name.startswith('native/'+run+'/') and name.endswith('/playtestr/results.json'))
        selected.extend(matches[:1] or sorted(name for name in files if name.startswith('native/'+run+'/'))[:1])
    restore=output/'selected-restore';restore.mkdir()
    with tarfile.open(archive,'r:gz') as source:
        for relative in selected:
            target=restore/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with source.extractfile(files[relative].get('member',relative)) as stream,target.open('xb') as destination:
                while block:=stream.read(65536):destination.write(block)
            if sha256(target)!=files[relative]['sha256']:raise ValueError('selected restore mismatch')
    index=output/'index.json'
    immutable_json(index,dict(schema_version=2,project=project,generation=generation,runs=runs,files=files,expanded_bytes=total,
        unique_payloads=len(members),
        archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,selected_restore=selected,max_file_bytes=max_file_bytes,
        scope='Every logical path/hash retained; identical bytes alias one verified in-archive member. No external dictionary or remote-only reference.'))
    immutable_json(output/'verified.json',dict(index_sha256=sha256(index),archive_sha256=sha256(archive),
        members_verified=len(files),physical_members_verified=len(members),selected_restore_verified=len(selected),expanded_removal_performed=False))
    print('Verified native compaction:',len(files),'logical files;',len(members),'unique payloads;',total,'expanded bytes;',archive.stat().st_size,'archive bytes.')
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--runs',nargs='+',required=True)
    parser.add_argument('--max-file-mib',type=int,choices=[4,16],default=4)
    parser.add_argument('--generation',type=int,choices=range(1,1001),default=1)
    args=parser.parse_args();compact(RAW,args.project,args.runs,args.max_file_mib*1024**2,generation=args.generation)


if __name__=='__main__':main()
