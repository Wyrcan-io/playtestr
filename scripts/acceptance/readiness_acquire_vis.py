"""Acquire reviewed project five; materialize only its exact pinned file aliases."""
import argparse
import json
import urllib.request

from readiness_acquire_plop import extract_source
from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_vis_source import ARCHIVE_SHA256,LINKS,PIN,materialize_archive


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-downloaded',action='store_true');args=parser.parse_args()
    base=RAW/'active';base.mkdir(parents=True,exist_ok=True);target=base/'vis'
    for ancestor in [RAW,base,target]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise RuntimeError('linked vis acquisition root')
    owner=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project='martanne/vis',pin=PIN)
    if args.resume_downloaded:
        if set(base.iterdir())!={target} or {p.name for p in target.iterdir()}!={'task-owned.json','source.tar.gz'}:
            raise RuntimeError('resume requires the exact untouched source-only failed acquisition')
        if json.loads((target/'task-owned.json').read_text())!=owner:raise RuntimeError('vis acquisition ownership mismatch')
    else:
        if any(base.iterdir()):raise RuntimeError('another active target exists')
        target.mkdir();immutable_json(target/'task-owned.json',owner)
        request=urllib.request.Request('https://api.github.com/repos/martanne/vis/tarball/'+PIN,headers={'User-Agent':'Playtestr-validation'})
        with urllib.request.urlopen(request,timeout=30) as response:data=response.read(8*1024**2+1)
        if len(data)>8*1024**2:raise RuntimeError('vis compressed source limit')
        (target/'source.tar.gz').write_bytes(data)
    archive=target/'source.tar.gz'
    if archive.stat().st_size>8*1024**2 or sha256(archive)!=ARCHIVE_SHA256:raise RuntimeError('vis archive differs from reviewed pinned source')
    normalized=materialize_archive(archive.read_bytes(),LINKS)
    count,total=extract_source(normalized,target/'src',expanded_limit=64*1024**2,entry_limit=10000,member_limit=16*1024**2)
    immutable_json(target/'acquisition.json',dict(pin=PIN,archive_sha256=sha256(archive),compressed_bytes=archive.stat().st_size,
        entries=count,extracted_source_bytes=total,build_hooks_executed=False,member_limit_bytes=16*1024**2,
        materialized_links=LINKS,profile='Reviewed internal symbolic file aliases copied as regular files; no host link creation or traversal. Original source archive retained unchanged.',
        initial_refused_attempt='Local d986bf98804e44ea80e0588e3c8ca739' if args.resume_downloaded else None))
    print('Acquired pinned vis source:',total,'bytes;',len(LINKS),'reviewed internal aliases materialized; no hooks executed.')


if __name__=='__main__':
    main()
