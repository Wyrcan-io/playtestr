"""Bounded source acquisition only; no third-party build hook executes."""
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

from readiness_evidence import RAW, ROOT, immutable_json, sha256


def acquire(slug, repository, pin):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',slug) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not re.fullmatch(r'[0-9a-f]{40}',pin):
        raise ValueError('invalid pinned source identity')
    active = RAW/'active'
    active.mkdir(parents=True,exist_ok=True)
    if any(active.iterdir()): raise RuntimeError('another active target exists; inspect its ownership/cleanup first')
    target = active/slug
    target.mkdir()
    immutable_json(target/'task-owned.json',dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',
                                               project=repository,pin=pin))
    request=urllib.request.Request('https://api.github.com/repos/'+repository+'/tarball/'+pin,
                                  headers={'User-Agent':'Playtestr-validation'})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(8*1024*1024+1)
    if len(data)>8*1024*1024: raise RuntimeError('source archive exceeds acquisition limit')
    archive=target/'source.tar.gz';archive.write_bytes(data)
    source=target/'src';source.mkdir()
    count=total=0
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as stream:
        members=stream.getmembers()
        if len(members)>10000: raise RuntimeError('source entry count exceeds limit')
        prefixes={PurePosixPath(m.name).parts[0] for m in members}
        if len(prefixes)!=1: raise RuntimeError('ambiguous archive root')
        for member in members:
            parts=PurePosixPath(member.name).parts[1:]
            if not parts:continue
            if any(p in {'','..','.'} or ':' in p or '\\' in p for p in parts):raise RuntimeError('unsafe archive path')
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):raise RuntimeError('unsupported source entry type')
            path=source.joinpath(*parts)
            path.resolve().relative_to(source.resolve())
            count+=1
            total+=member.size
            if total>64*1024*1024 or member.size>8*1024*1024:raise RuntimeError('extracted source byte limit')
            if member.isdir():path.mkdir(parents=True,exist_ok=True);continue
            path.parent.mkdir(parents=True,exist_ok=True)
            with stream.extractfile(member) as src,path.open('xb') as out:
                remaining=member.size
                while remaining:
                    chunk=src.read(min(65536,remaining))
                    if not chunk:raise RuntimeError('truncated archive member')
                    out.write(chunk);remaining-=len(chunk)
            if os.name!='nt':path.chmod(0o755 if member.mode&0o111 else 0o644)
    immutable_json(target/'acquisition.json',dict(pin=pin,archive_sha256=sha256(archive),
        compressed_bytes=len(data),extracted_source_bytes=total,entries=count,
        build_hooks_executed=False))
    print('Acquired pinned source only:',target.relative_to(ROOT),'bytes',total,'entries',count)


def main():
    acquire('plop','plopjs/plop','0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e')


if __name__=='__main__':main()
