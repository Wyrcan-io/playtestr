"""Verify one acquired target against its complete pinned primary Git tree."""
import argparse
import hashlib
import json
import os
import re
import stat
import urllib.request
from pathlib import Path

from next20_check import RAW,DOC,NAME
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--omitted-documentation-links',type=Path);parser.add_argument('--verify-existing',action='store_true');parser.add_argument('--verify-from-frozen-provenance',action='store_true');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('Invalid target slug')
    target=RAW/'active'/args.project;marker=json.loads((target/'task-owned.json').read_text())
    if marker['campaign']!=NAME or marker['slug']!=args.project:raise ValueError('Target ownership mismatch')
    repository=marker['project'];pin=marker['pin']
    if not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not re.fullmatch('[0-9a-f]{40}',pin):raise ValueError('Invalid pinned primary identity')
    if args.verify_from_frozen_provenance:
        if args.omitted_documentation_links:raise ValueError('Frozen-provenance mode does not support link omission')
        package=DOC/args.project;expected=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
        acquisition=json.loads((target/'acquisition.json').read_text(encoding='utf-8'))
        archive=target/'source.tar.gz';source=target/'src'
        if expected.get('repository')!=repository or expected.get('pin')!=pin or acquisition.get('repository')!=repository or acquisition.get('pin')!=pin:
            raise ValueError('Acquired source and frozen provenance identities differ')
        if acquisition.get('url')!='https://api.github.com/repos/'+repository+'/tarball/'+pin or acquisition.get('archive_sha256')!=sha256(archive):
            raise ValueError('Acquisition URL/archive identity differs from the pinned source')
        actual={};modes={}
        for path in source.rglob('*'):
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed source link')
            if not path.is_file():continue
            name=path.relative_to(source).as_posix()
            if path.stat().st_size>8*1024**2:raise ValueError('Source member exceeds bound: '+name)
            actual[name]=sha256(path)
            modes[name]='100755' if path.stat().st_mode&stat.S_IXUSR else '100644'
        if actual!=expected.get('files') or actual!=acquisition.get('source_files') or modes!=expected.get('git_modes'):
            raise ValueError('Acquired source files or Git modes differ from the frozen exact primary provenance')
        print('Verified acquired pinned source against frozen primary provenance:',len(actual),args.project)
        return
    destination=RAW/'screening/reviews'/repository.replace('/','--')/pin/'tree.json'
    if destination.exists():
        tree=json.loads(destination.read_text(encoding='utf-8'))
    else:
        url='https://api.github.com/repos/'+repository+'/git/trees/'+pin+'?recursive=1'
        headers={'User-Agent':'Playtestr-validation'}
        token=os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if token:headers['Authorization']='Bearer '+token
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:
            data=response.read(4*1024**2+1)
        if len(data)>4*1024**2:raise ValueError('Primary tree metadata bound')
        tree=json.loads(data);immutable_json(destination,tree)
    if tree.get('truncated') or len(tree['tree'])>10000:raise ValueError('Incomplete/bounded primary source tree')
    blobs={r['path']:r for r in tree['tree'] if r['type']=='blob'}
    omitted={}
    if args.omitted_documentation_links:
        from next20_source_links import policy
        _,links=policy(args.omitted_documentation_links,args.project,pin)
        for name,target_name in links.items():
            body=target_name.encode();entry=blobs.get(name)
            if entry is None or entry['mode']!='120000' or entry['sha']!=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest() or target_name not in blobs or blobs[target_name]['mode']!='100644':raise ValueError('primary Git documentation alias differs')
            omitted[name]=dict(target=target_name,git_blob_sha1=entry['sha'],git_mode=entry['mode'],representation='Original link retained inside source archive; omitted from extracted execution tree, never followed.')
        blobs={n:r for n,r in blobs.items() if n not in omitted}
    source=target/'src';actual={p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file()}
    if set(actual)!=set(blobs):raise ValueError('Source archive/primary Git tree coverage differs')
    for name,path in actual.items():
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed source link')
        data=path.read_bytes()
        if len(data)>8*1024**2 or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blobs[name]['sha']:
            raise ValueError('Pinned source content differs: '+name)
    package=DOC/args.project;package.mkdir(exist_ok=True)
    provenance=dict(schema_version=1,repository=repository,pin=pin,
        primary_tree_sha256=sha256(destination),source_blobs_verified=len(actual),
        files={name:sha256(path) for name,path in actual.items()},
        git_modes={name:blobs[name]['mode'] for name in actual},
        **(dict(omitted_documentation_links=omitted,documentation_link_policy_sha256=sha256(args.omitted_documentation_links)) if omitted else {}),
        scope='Exact pinned primary source content only. Does not approve install/build hooks or target execution.')
    if args.verify_existing:
        if json.loads((package/'source-provenance.json').read_text())!=provenance:raise ValueError('fresh native primary provenance differs from canonical')
    else:immutable_json(package/'source-provenance.json',provenance)
    print('Verified exact pinned primary Git source blobs:',len(actual),args.project)


if __name__=='__main__':main()
