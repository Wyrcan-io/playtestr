"""Verify and remove only Skim's exact workflow-owned compiler/cache roots."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import shutil
import uuid

from next20_check import DOC, NAME, RAW, ROOT
from readiness_evidence import immutable_json, sha256
from next20_target_cleanup import source_inventory


CACHE_ROOTS=('cargo-home','cargo-target','go-mod-cache','home','rustup-home','tmp')
MAX_FILES=250000
MAX_BYTES=4*1024**3


def inventory_cache(root, target):
    """Hash a bounded cache tree without following links or special files."""
    root=Path(root);target=Path(target).resolve(strict=True)
    resolved=root.resolve(strict=True)
    resolved.relative_to(target)
    if resolved==target or root.is_symlink() or getattr(root,'is_junction',lambda:False)():
        raise ValueError('invalid owned cache root')
    files=0;total=0;links=[];special=[];digest=hashlib.sha256();pending=[root]
    while pending:
        directory=pending.pop()
        entries=sorted(os.scandir(directory),key=lambda item:item.name)
        for entry in entries:
            path=Path(entry.path);relative=path.relative_to(root).as_posix()
            info=entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode) or getattr(info,'st_reparse_tag',0)==getattr(stat,'IO_REPARSE_TAG_MOUNT_POINT',0xA0000003):
                try:destination=path.resolve(strict=True);destination.relative_to(resolved)
                except (OSError,ValueError) as error:
                    raise ValueError('owned cache link escapes or is unresolved: '+relative) from error
                links.append(dict(path=relative,target=destination.relative_to(resolved).as_posix(),bytes=info.st_size))
                total+=info.st_size
                digest.update(f'L\0{relative}\0{links[-1]["target"]}\0{info.st_size}\n'.encode())
            elif stat.S_ISDIR(info.st_mode):
                pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                files+=1;total+=info.st_size
                if files>MAX_FILES or info.st_size>128*1024**2 or total>MAX_BYTES:
                    raise ValueError('owned cache inventory bound: files=%d bytes=%d at %s'%(files,total,relative))
                digest.update(f'F\0{relative}\0{info.st_size}\0{sha256(path)}\n'.encode())
            elif stat.S_ISFIFO(info.st_mode) or stat.S_ISSOCK(info.st_mode):
                kind='fifo' if stat.S_ISFIFO(info.st_mode) else 'socket'
                special.append(dict(path=relative,kind=kind,metadata_bytes=info.st_size))
                total+=info.st_size
                digest.update(f'S\0{relative}\0{kind}\0{info.st_size}\n'.encode())
            else:
                raise ValueError('unsupported owned cache entry: '+relative+' mode='+oct(info.st_mode))
            if files>MAX_FILES or total>MAX_BYTES:
                raise ValueError('owned cache inventory bound: files=%d bytes=%d'%(files,total))
    return dict(files=files,bytes=total,tree_sha256=digest.hexdigest(),links=links,special_entries=special)


def prune(target, roots=CACHE_ROOTS):
    """Remove declared cache roots after complete in-root inventories exist."""
    target=Path(target).resolve(strict=True)
    if set(roots)-set(CACHE_ROOTS) or len(set(roots))!=len(roots):
        raise ValueError('undeclared or duplicate Skim cache root')
    inventories={}
    for name in roots:
        path=target/name
        if path.exists():
            inventories[name]=inventory_cache(path,target)
        else:
            inventories[name]=dict(present=False,files=0,bytes=0,tree_sha256=None,links=[],special_entries=[])
    for name in roots:
        path=target/name
        if not path.exists():continue
        record=inventories[name]
        for link in sorted(record['links'],key=lambda row:row['path'],reverse=True):
            entry=path/Path(link['path'])
            resolved=entry.resolve(strict=True)
            if resolved.relative_to(path.resolve(strict=True)).as_posix()!=link['target']:
                raise ValueError('owned cache link changed after inventory: '+link['path'])
            if not (entry.is_symlink() or getattr(entry,'is_junction',lambda:False)()):
                raise ValueError('owned cache link type changed after inventory: '+link['path'])
            entry.unlink()
        shutil.rmtree(path)
        if path.exists():raise ValueError('owned cache root remains after checked removal: '+name)
    return inventories


def main():
    target=RAW/'active'/'skim'
    resolved=target.resolve(strict=True);resolved.relative_to((RAW/'active').resolve(strict=True))
    for path in [ROOT/'artifacts',RAW,RAW/'active',target]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('linked cache-cleanup ancestor')
    owner=json.loads((target/'task-owned.json').read_text(encoding='utf-8'))
    if owner.get('workspace')!=str(ROOT) or owner.get('campaign')!=NAME or owner.get('slug')!='skim':
        raise ValueError('foreign Skim cache-cleanup ownership marker')
    source=json.loads((target/'acquisition.json').read_text(encoding='utf-8'))
    provenance=json.loads((DOC/'skim'/'source-provenance.json').read_text(encoding='utf-8'))
    if source.get('pin')!=provenance.get('pin') or source.get('source_files')!=provenance.get('files'):
        raise ValueError('Skim cache cleanup source provenance differs')
    if source_inventory(target/'src')!=provenance['files']:
        raise ValueError('Skim cache cleanup requires exact restored source bytes')
    if os.name != 'nt':
        observed=subprocess.run(['ps','-axo','pid=,args='],capture_output=True,timeout=5,check=True)
        if len(observed.stdout)>1024**2:
            raise ValueError('native Skim process observer bound')
        matching=[line.split(None,1)[0].decode() for line in observed.stdout.splitlines()
                  if str(target).encode() in line]
        if matching:
            raise ValueError('Skim target process remains before cache removal: '+','.join(matching))
    build_path=target/'build.json'
    build=None
    if build_path.is_file():
        build=json.loads(build_path.read_text(encoding='utf-8'))
        binary=target/build.get('binary_relative_path','')
        if build.get('pin')!=provenance['pin'] or not binary.is_file() or sha256(binary)!=build.get('binary_sha256'):
            raise ValueError('Skim cache cleanup target build identity differs')
    destination=RAW/'skim'/'cache-cleanup'/uuid.uuid4().hex
    inventories={}
    for name in CACHE_ROOTS:
        path=target/name
        inventories[name]=inventory_cache(path,target) if path.exists() else dict(
            present=False,files=0,bytes=0,tree_sha256=None,links=[],special_entries=[])
    immutable_json(destination/'prepared.json',dict(schema_version=1,project='skim',owned_target=str(target),
        owner_sha256=sha256(target/'task-owned.json'),source_manifest_sha256=sha256(DOC/'skim'/'source-provenance.json'),
        build_sha256=sha256(build_path) if build else None,caches=inventories,
        scope='Bounded per-file SHA-256 inventory of exact workflow-owned build/cache roots. No source, target executable, candidate reports, or case evidence is removed.'))
    removed=prune(target)
    if removed!=inventories:raise ValueError('removed cache inventory differs from prepared evidence')
    immutable_json(destination/'removed.json',dict(schema_version=1,project='skim',owned_target=str(target),
        prepared_sha256=sha256(destination/'prepared.json'),removed_roots=list(CACHE_ROOTS),
        scope='Only the declared compiler/cache roots were removed after exact in-root inventory and source/build identity checks.'))
    print('Verified and removed Skim workflow caches:',sum(row['files'] for row in inventories.values()),
          'files,',sum(row['bytes'] for row in inventories.values()),'bytes; source/runtime preserved.')


if __name__=='__main__':main()
