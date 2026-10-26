"""Retain canonical registry source once; verify exact native duplicate references."""
import argparse
import json

from next20_check import RAW, DOC, ROOT
from readiness_evidence import immutable_json, sha256


def cache_inventory(root):
    RAW.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    root.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    for ancestor in [root,*root.parents]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('Linked canonical registry ancestor')
        if ancestor==RAW:break
    files={};total=0
    for path in root.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Linked registry cache')
        if not path.is_file():continue
        size=path.stat().st_size;total+=size
        if len(files)>=1000 or size>16*1024**2 or total>32*1024**2:raise ValueError('Canonical registry source bound')
        with path.open('rb') as stream:
            if stream.read(2)!=b'\x1f\x8b':raise ValueError('Non-package bytes remain outside metadata retention')
        files[path.relative_to(root).as_posix()]=dict(bytes=size,sha256=sha256(path))
    return files,total


def canonical_payloads():
    declaration=json.loads((DOC/'yo/registry-payloads.json').read_text())
    cache=RAW/'yo/retained-source/npm-cache'
    files,total=cache_inventory(cache)
    if files!=declaration['files'] or total!=declaration['total_bytes']:
        raise ValueError('Retained canonical registry payload closure missing/changed')
    return {'yo/retained-source/npm-cache/'+name:(cache/name).read_bytes() for name in files}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--declare',action='store_true');args=parser.parse_args()
    retained=RAW/'yo/retained-source';cache=retained/'npm-cache'
    if (RAW/'active/yo').exists():raise ValueError('Checked target source/runtime cleanup required first')
    files,total=cache_inventory(cache)
    if args.declare:
        immutable_json(DOC/'yo/registry-payloads.json',dict(schema_version=1,project='yo',
            source_pin=json.loads((DOC/'yo/source-provenance.json').read_text())['pin'],
            framework_lock_sha256=sha256(DOC/'yo/generator-package-lock.json'),files=files,total_bytes=total,
            scope='Canonical SRI-verified registry source retained once inside this project closure. Native duplicates may reference only these exact bytes after full native setup/cleanup inventory verification; missing local payloads reject audit. Counts against the64MiB all-generation gate.'))
        print('Declared canonical registry source retained once:',len(files),'payloads,',total,'bytes.')
        return
    approved=json.loads((DOC/'yo/registry-payloads.json').read_text())
    if files!=approved['files'] or total!=approved['total_bytes']:raise ValueError('Native cache payloads differ from retained canonical source')
    cleanup=json.loads((retained/'cleanup-inventory.json').read_text())
    removed=json.loads((retained/'removed.json').read_text(encoding='utf-8-sig'))
    if not removed['removed'] or removed['cleanup_inventory_sha256']!=sha256(retained/'cleanup-inventory.json'):
        raise ValueError('Native source/runtime cleanup not verified')
    for name,row in files.items():
        if cleanup['files']['npm-cache/'+name]!=row or cleanup['retained']['npm-cache/'+name]!=row['sha256']:
            raise ValueError('Native canonical package bytes not bound by actual cleanup inventory')
        path=cache/name;path.resolve(strict=True).relative_to(cache.resolve(strict=True))
    reference=retained/'registry-source-reference.json'
    immutable_json(reference,dict(schema_version=1,project='yo',
        canonical_declaration_sha256=sha256(DOC/'yo/registry-payloads.json'),
        files=files,total_bytes=total,native_cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json'),
        source_dependency='yo/retained-source/npm-cache in the local project evidence closure; every canonical payload mandatory and counted once.',
        scope='Exact native duplicate package source removed only after full hash equality and checked native source/runtime cleanup. No external-only dictionary or package compatibility inference.'))
    for name,row in files.items():
        if sha256(cache/name)!=row['sha256']:raise ValueError('Native cache changed before duplicate removal')
    for name in files:(cache/name).unlink()
    if any(path.is_file() for path in cache.rglob('*')):raise ValueError('Unaccounted native package payload remains')
    print('Verified native registry package source references:',len(files),'exact canonical payloads; full local dependency required for audit.')


if __name__=='__main__':main()
