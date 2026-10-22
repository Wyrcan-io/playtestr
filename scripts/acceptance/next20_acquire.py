"""Acquire one declared pinned target; reuse the checked historical extractor."""
import argparse
import json
import urllib.request

from next20_check import NAME,RAW,ROOT,DOC
from readiness_acquire_plop import extract_source
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    declaration=json.loads((DOC/'selection-declaration.json').read_text())
    matches=[p for p in declaration['selected'] if p['id']==args.project]
    if len(matches)!=1:raise ValueError('not a selected target')
    selected=matches[0]
    if selected['late_transfer']:raise ValueError('late transfer target cannot be acquired before provisional freeze')
    rows=json.loads((DOC/'screening-decisions.json').read_text())['rows']
    row=next(r for r in rows if r.get('repository')==selected['repository'])
    old=ROOT/'artifacts/runner-readiness-ten-project-pass'
    if any((old/'active').iterdir()):raise ValueError('original campaign has an active target')
    active=RAW/'active';active.mkdir(exist_ok=True)
    if any(active.iterdir()):raise ValueError('active target already exists; resume/clean it before acquisition')
    before=measure(RAW);old_size=measure(old)['total_bytes']
    if before['total_bytes']+64*1024**2>4*1024**3 or before['total_bytes']+old_size+64*1024**2>6*1024**3:
        raise ValueError('insufficient declared acquisition headroom')
    target=active/args.project;target.mkdir()
    immutable_json(target/'task-owned.json',dict(workspace=str(ROOT),campaign=NAME,
        project=selected['repository'],slug=args.project,pin=row['pin'],
        storage_before_bytes=before['total_bytes'],source_only=True))
    url='https://api.github.com/repos/'+selected['repository']+'/tarball/'+row['pin']
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
        data=response.read(8*1024**2+1)
    if len(data)>8*1024**2:raise ValueError('compressed source exceeds declaration')
    archive=target/'source.tar.gz'
    with archive.open('xb') as stream:stream.write(data)
    count,total=extract_source(data,target/'src',expanded_limit=64*1024**2,
        entry_limit=10000,member_limit=8*1024**2)
    immutable_json(target/'acquisition.json',dict(repository=selected['repository'],pin=row['pin'],url=url,
        archive_sha256=sha256(archive),compressed_bytes=len(data),expanded_bytes=total,entries=count,
        build_hooks_executed=False,source_files={p.relative_to(target/'src').as_posix():sha256(p)
            for p in sorted((target/'src').rglob('*')) if p.is_file()}))
    print('Acquired source only:',args.project,row['pin'],'files',count,'bytes',total)


if __name__=='__main__':main()
