"""Verify one acquired target against its complete pinned primary Git tree."""
import argparse
import hashlib
import json
import re
import urllib.request

from next20_check import RAW,DOC,NAME
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('Invalid target slug')
    target=RAW/'active'/args.project;marker=json.loads((target/'task-owned.json').read_text())
    if marker['campaign']!=NAME or marker['slug']!=args.project:raise ValueError('Target ownership mismatch')
    repository=marker['project'];pin=marker['pin']
    if not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not re.fullmatch('[0-9a-f]{40}',pin):raise ValueError('Invalid pinned primary identity')
    destination=RAW/'screening/reviews'/repository.replace('/','--')/pin/'tree.json'
    if destination.exists():
        tree=json.loads(destination.read_text(encoding='utf-8'))
    else:
        url='https://api.github.com/repos/'+repository+'/git/trees/'+pin+'?recursive=1'
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
            data=response.read(4*1024**2+1)
        if len(data)>4*1024**2:raise ValueError('Primary tree metadata bound')
        tree=json.loads(data);immutable_json(destination,tree)
    if tree.get('truncated') or len(tree['tree'])>10000:raise ValueError('Incomplete/bounded primary source tree')
    blobs={r['path']:r for r in tree['tree'] if r['type']=='blob'}
    source=target/'src';actual={p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file()}
    if set(actual)!=set(blobs):raise ValueError('Source archive/primary Git tree coverage differs')
    for name,path in actual.items():
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed source link')
        data=path.read_bytes()
        if len(data)>8*1024**2 or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blobs[name]['sha']:
            raise ValueError('Pinned source content differs: '+name)
    package=DOC/args.project;package.mkdir(exist_ok=True)
    immutable_json(package/'source-provenance.json',dict(schema_version=1,repository=repository,pin=pin,
        primary_tree_sha256=sha256(destination),source_blobs_verified=len(actual),
        files={name:sha256(path) for name,path in actual.items()},
        git_modes={name:blobs[name]['mode'] for name in actual},
        scope='Exact pinned primary source content only. Does not approve install/build hooks or target execution.'))
    print('Verified exact pinned primary Git source blobs:',len(actual),args.project)


if __name__=='__main__':main()
