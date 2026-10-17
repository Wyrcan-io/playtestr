"""Reviewed vis source-only profile: materialize exact internal file aliases."""
import gzip
import io
from pathlib import PurePosixPath
import posixpath
import tarfile

PIN='10b630af09404cf2c887e2d7e6e24ecda9d05ea7'
ARCHIVE_SHA256='0f8895b2e3aacb6acd3f0add71da614b876a0735d496c5ce64b6c62281bdcd06'
LINKS={
    'lua/lexer.lua':'lexers/lexer.lua',
    'lua/themes/default.lua':'base-16.lua',
    'test/core/ccan/compiler/LICENSE':'../../licenses/CC0',
    'test/fuzz/dictionaries/text-libfuzzer.dict':'text-fuzzer.dict',
    'test/fuzz/inputs/text-libfuzzer/text-libfuzzer.in':'../text-fuzzer/text-fuzzer.in',
    **{'test/sam/commands/loop-lines'+str(n)+'.in':'loop-lines.in' for n in range(1,10)}}


def materialize_archive(data,reviewed_links):
    """Create a bounded in-memory regular-file view; never follow host links."""
    if len(data)>8*1024**2:raise RuntimeError('source archive bound')
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as source:
        members=[];total=0
        for member in source:
            members.append(member);total+=member.size
            if len(members)>10000 or member.size<0 or member.size>16*1024**2 or total>64*1024**2:
                raise RuntimeError('reviewed source expansion bounds')
        roots={PurePosixPath(m.name).parts[0] for m in members}
        if len(roots)!=1:raise RuntimeError('ambiguous materialized source root')
        root=next(iter(roots));by_name={m.name:m for m in members}
        if len(by_name)!=len(members):raise RuntimeError('duplicate materialized source member')
        actual={m.name.split('/',1)[1]:m.linkname for m in members if m.issym() and '/' in m.name}
        if actual!=reviewed_links:raise RuntimeError('source link profile differs from reviewed pin')
        plan=[]
        for member in members:
            if member.isdir():plan.append((member,member));continue
            payload=member
            if member.issym():
                relative=member.name.split('/',1)[1];link=member.linkname
                if link.startswith('/') or '\\' in link or ':' in link or '\x00' in link:
                    raise RuntimeError('unsafe reviewed source link')
                destination=posixpath.normpath(posixpath.join(posixpath.dirname(relative),link))
                if destination=='..' or destination.startswith('../') or destination.startswith('/'):
                    raise RuntimeError('escaping reviewed source link')
                payload=by_name.get(root+'/'+destination)
                if payload is None or not payload.isfile():raise RuntimeError('source link target must be a regular archive file')
                total+=payload.size
                if total>64*1024**2:raise RuntimeError('materialized source byte bound')
            elif not member.isfile():raise RuntimeError('unsupported reviewed source type')
            plan.append((member,payload))
        output=io.BytesIO()
        with gzip.GzipFile(fileobj=output,mode='wb',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
                for member,payload in plan:
                    entry=tarfile.TarInfo(member.name);entry.mode=payload.mode;entry.mtime=0
                    if member.isdir():entry.type=tarfile.DIRTYPE;target.addfile(entry);continue
                    entry.size=payload.size
                    with source.extractfile(payload) as stream:target.addfile(entry,stream)
        if output.tell()>8*1024**2:raise RuntimeError('materialized archive byte bound')
        return output.getvalue()
