"""Install an official pinned Go SDK only below this job's owned campaign root."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import tarfile
import time
import urllib.request
import zipfile

from readiness_evidence import RAW, ROOT, immutable_json

VERSION='go1.25.0'


def main(*, owned=None):
    host={'Linux':'linux','Darwin':'darwin','Windows':'windows'}[platform.system()]
    machine=platform.machine().lower()
    arch={'x86_64':'amd64','amd64':'amd64','arm64':'arm64','aarch64':'arm64'}[machine]
    extension='.zip' if host=='windows' else '.tar.gz'
    name=f'{VERSION}.{host}-{arch}{extension}'
    owned=RAW/'toolchain' if owned is None else Path(owned)
    owned=owned.resolve()
    owned.relative_to((ROOT/'artifacts').resolve())
    for parent in [owned,*owned.parents]:
        if parent==ROOT:break
        if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise RuntimeError('linked owned SDK ancestor')
    owned.mkdir(parents=True,exist_ok=True)
    if (owned/'go').exists():raise RuntimeError('refuse to overwrite an existing SDK')
    started=time.monotonic()
    request=urllib.request.Request('https://go.dev/dl/?mode=json&include=all',headers={'User-Agent':'Playtestr-validation'})
    with urllib.request.urlopen(request,timeout=30) as response:metadata=response.read(4*1024*1024+1)
    if len(metadata)>4*1024*1024:raise RuntimeError('official release index size bound')
    releases=json.loads(metadata)
    release=next(r for r in releases if r['version']==VERSION)
    descriptor=next(f for f in release['files'] if f['filename']==name and f['kind']=='archive')
    if descriptor['size']>100*1024*1024:raise RuntimeError('SDK archive size bound')
    url='https://go.dev/dl/'+name
    digest=hashlib.sha256();archive=owned/name
    with urllib.request.urlopen(url,timeout=45) as response,archive.open('xb') as out:
        total=0
        while block:=response.read(65536):
            total+=len(block)
            if total>descriptor['size'] or time.monotonic()-started>300:raise RuntimeError('SDK download byte/time bound')
            digest.update(block);out.write(block)
    if total!=descriptor['size'] or digest.hexdigest()!=descriptor['sha256']:raise RuntimeError('official SDK checksum mismatch')
    entries=0;expanded=0
    def destination(name,size):
        nonlocal entries,expanded
        path=PurePosixPath(name)
        if not path.parts or path.parts[0]!='go' or path.is_absolute() or any(p in {'.','..'} or ':' in p or '\\' in p for p in path.parts):raise RuntimeError('unsafe SDK archive path')
        entries+=1;expanded+=size
        if entries>30000 or expanded>512*1024*1024 or size>64*1024*1024:raise RuntimeError('SDK extraction bound')
        if time.monotonic()-started>300:raise RuntimeError('SDK setup deadline')
        result=owned.joinpath(*path.parts)
        result.resolve().relative_to(owned.resolve())
        return result
    if extension=='.zip':
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target=destination(member.filename,member.file_size)
                if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                if (member.external_attr>>16)&0o170000==0o120000:raise RuntimeError('linked SDK member')
                target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(member) as source,target.open('xb') as out:
                    while block:=source.read(65536):out.write(block)
    else:
        with tarfile.open(archive,'r:gz') as bundle:
            for member in bundle:
                target=destination(member.name,member.size)
                if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
                if not member.isfile():raise RuntimeError('linked or special SDK member')
                target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member) as source,target.open('xb') as out:
                    while block:=source.read(65536):out.write(block)
                target.chmod(0o755 if member.mode&0o111 else 0o644)
    immutable_json(owned/'sdk.json',dict(version=VERSION,host=host,architecture=arch,url=url,
        official_index='https://go.dev/dl/?mode=json&include=all',sha256=digest.hexdigest(),
        compressed_bytes=total,expanded_bytes=expanded,entries=entries))
    print('Verified workspace-owned SDK:',VERSION,host,arch,digest.hexdigest(),flush=True)


if __name__=='__main__':main()
