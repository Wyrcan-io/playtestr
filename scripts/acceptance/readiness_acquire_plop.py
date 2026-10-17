"""Bounded source acquisition only; no third-party build hook executes."""
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

from readiness_evidence import RAW, ROOT, immutable_json, sha256


def extract_source(data, source, *, expanded_limit, entry_limit, member_limit):
    """Validate the entire bounded member plan before creating any output."""
    source=Path(source)
    source.parent.resolve().relative_to(ROOT)
    if source.exists() or source.is_symlink():raise RuntimeError('source destination already exists')
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as stream:
        members=[];declared_bytes=0
        for member in stream:
            if len(members)>=entry_limit:raise RuntimeError('source entry count exceeds limit')
            declared_bytes+=member.size
            if member.size<0 or member.size>member_limit or declared_bytes>expanded_limit:
                raise RuntimeError('extracted source byte limit')
            members.append(member)
        prefixes={PurePosixPath(m.name).parts[0] for m in members}
        if len(prefixes)!=1 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,200}',next(iter(prefixes))):
            raise RuntimeError('ambiguous or unsafe archive root')
        plan=[];total=0;seen=set();file_paths=set()
        for member in members:
            name=PurePosixPath(member.name);parts=name.parts[1:]
            if name.is_absolute() or any(p in {'','..','.'} or ':' in p or '\\' in p for p in name.parts):
                raise RuntimeError('unsafe archive path')
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise RuntimeError('unsupported source entry type')
            if not parts:
                if not member.isdir():raise RuntimeError('archive root is not a directory')
                continue
            key='/'.join(parts).casefold() if os.name=='nt' else '/'.join(parts)
            if key in seen:raise RuntimeError('duplicate source member')
            seen.add(key)
            if member.isfile():file_paths.add(key)
            total+=member.size
            if member.size<0 or total>expanded_limit or member.size>member_limit:
                raise RuntimeError('extracted source byte limit')
            plan.append((member,parts))
        for _,parts in plan:
            for i in range(1,len(parts)):
                parent='/'.join(parts[:i]);parent=parent.casefold() if os.name=='nt' else parent
                if parent in file_paths:raise RuntimeError('source member has a file ancestor')
        source.mkdir()
        for member,parts in plan:
            path=source.joinpath(*parts)
            if member.isdir():path.mkdir(parents=True,exist_ok=True);continue
            path.parent.mkdir(parents=True,exist_ok=True)
            with stream.extractfile(member) as src,path.open('xb') as out:
                remaining=member.size
                while remaining:
                    chunk=src.read(min(65536,remaining))
                    if not chunk:raise RuntimeError('truncated archive member')
                    out.write(chunk);remaining-=len(chunk)
            if os.name!='nt':path.chmod(0o755 if member.mode&0o111 else 0o644)
    return len(plan),total


def acquire(slug, repository, pin, *, archive_limit=8*1024**2, expanded_limit=64*1024**2,
            entry_limit=10000, member_limit=8*1024**2, resume=False):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',slug) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not re.fullmatch(r'[0-9a-f]{40}',pin):
        raise ValueError('invalid pinned source identity')
    active = RAW/'active'
    active.mkdir(parents=True,exist_ok=True)
    target = active/slug
    owner=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project=repository,pin=pin)
    if resume:
        if list(active.iterdir())!=[target] or list(target.iterdir())!=[target/'task-owned.json']:
            raise RuntimeError('resume requires exactly the failed acquisition ownership marker')
        if json.loads((target/'task-owned.json').read_text())!=owner:
            raise RuntimeError('failed acquisition ownership mismatch')
    else:
        if any(active.iterdir()):raise RuntimeError('another active target exists; inspect its ownership/cleanup first')
        target.mkdir()
        immutable_json(target/'task-owned.json',owner)
    request=urllib.request.Request('https://api.github.com/repos/'+repository+'/tarball/'+pin,
                                  headers={'User-Agent':'Playtestr-validation'})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(archive_limit+1)
    if len(data)>archive_limit: raise RuntimeError('source archive exceeds acquisition limit')
    archive=target/'source.tar.gz';archive.write_bytes(data)
    count,total=extract_source(data,target/'src',expanded_limit=expanded_limit,
                               entry_limit=entry_limit,member_limit=member_limit)
    immutable_json(target/'acquisition.json',dict(pin=pin,archive_sha256=sha256(archive),
        compressed_bytes=len(data),extracted_source_bytes=total,entries=count,
        build_hooks_executed=False))
    print('Acquired pinned source only:',target.relative_to(ROOT),'bytes',total,'entries',count)


def main():
    acquire('plop','plopjs/plop','0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e')


if __name__=='__main__':main()
