"""Verify reviewed selected Python source and primary wheel digests before install."""
import argparse
from email.parser import BytesParser
import hashlib
import json
import re
import tomllib
import urllib.parse
import urllib.request
import zipfile

from next20_check import RAW, DOC
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    declaration_path=DOC/args.project/'setup-declaration.json'
    declaration=json.loads(declaration_path.read_text());target=RAW/'active'/args.project
    target.resolve(strict=True).relative_to((RAW/'active').resolve())
    source=target/'src';marker=json.loads((target/'task-owned.json').read_text())
    if marker['slug']!=args.project or marker['project']!=declaration['repository'] or marker['pin']!=declaration['pin']:
        raise ValueError('selected reviewed Python source ownership mismatch')
    tree_path=RAW/'screening/reviews'/declaration['repository'].replace('/','--')/marker['pin']/'tree.json'
    tree=json.loads(tree_path.read_text());expected={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
    actual={p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file()}
    if tree.get('truncated') or set(expected)!=set(actual):raise ValueError('pinned Git tree/archive coverage mismatch')
    for name,path in actual.items():
        data=path.read_bytes()
        if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=expected[name]:
            raise ValueError('pinned source bytes mismatch: '+name)
    metadata=tomllib.loads((source/'pyproject.toml').read_text())
    if metadata['build-system']['build-backend']!=declaration['backend']:raise ValueError('reviewed build backend changed')
    review=json.loads((target/'dependency-review.json').read_text());inventory=json.loads((target/'wheels.json').read_text())
    if len(inventory)>64 or set(inventory)!={r['wheel'] for r in review['wheels']} or any(r['startup_hooks'] for r in review['wheels']):
        raise ValueError('unknown dependency/startup review inputs')
    dependencies=[];primary=target/'dependency-review/primary';primary.mkdir()
    for filename,row in inventory.items():
        wheel=target/'wheels'/filename
        if sha256(wheel)!=row['sha256']:raise ValueError('reviewed dependency bytes changed')
        with zipfile.ZipFile(wheel) as archive:
            names=[n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            if len(names)!=1:raise ValueError('ambiguous wheel package metadata')
            info=BytesParser().parsebytes(archive.read(names[0]));name=info['Name'];version=info['Version']
        if not all(re.fullmatch('[A-Za-z0-9_.+-]{1,100}',value) for value in [name,version]):raise ValueError('unsafe package primary lookup')
        url='https://pypi.org/pypi/'+urllib.parse.quote(name,safe='')+'/'+urllib.parse.quote(version,safe='')+'/json'
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
            data=response.read(4*1024**2+1)
        if len(data)>4*1024**2:raise ValueError('primary release metadata bound')
        release=json.loads(data);matches=[f for f in release['urls'] if f['filename']==filename]
        if len(matches)!=1 or matches[0]['digests']['sha256']!=row['sha256'] or matches[0]['size']!=row['bytes']:
            raise ValueError('wheel does not match primary release digest: '+filename)
        retained=primary/(filename+'.json')
        with retained.open('xb') as stream:stream.write(data)
        dependencies.append(dict(name=name,version=version,wheel=filename,sha256=row['sha256'],
            primary=url,primary_metadata_sha256=sha256(retained),license=info.get('License-Expression') or info.get('License'),
            license_files=info.get_all('License-File',[])))
    reviewed={name:sha256(source/name) for name in declaration['reviewed_source']}
    approval=dict(schema_version=1,approved=True,review_sha256=sha256(target/'dependency-review.json'),
        setup_declaration_sha256=sha256(declaration_path),reviewed_source=reviewed,pinned_tree_sha256=sha256(tree_path),
        source_blobs_verified=len(actual),dependencies=dependencies,backend=declaration['backend'],
        execution_scope=declaration['execution_scope'],wheel_script_approval_sha256=sha256(target/'wheel-script-approval.json') if (target/'wheel-script-approval.json').exists() else None)
    immutable_json(target/'install-approval.json',approval);immutable_json(DOC/args.project/'source-review.json',approval)
    immutable_json(DOC/args.project/'source-provenance.json',dict(schema_version=1,pin=marker['pin'],
        repository=declaration['repository'],files={name:sha256(path) for name,path in actual.items()}))
    print('Verified complete pinned source:',len(actual),'blobs and',len(dependencies),'primary-release wheel digests. Approved explicit offline owned build.')


if __name__=='__main__':main()
