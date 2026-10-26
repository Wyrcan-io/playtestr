"""Acquire primary npm metadata and integrity-checked source for review only."""
import argparse
import base64
import hashlib
import json
import re
import urllib.parse
import urllib.request

from next20_check import RAW
from readiness_acquire_plop import extract_source
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('package')
    parser.add_argument('--version',default='latest');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project) or not re.fullmatch(r'(?:@[a-z0-9_.-]+/)?[a-z0-9_.-]+',args.package) or not re.fullmatch('[a-zA-Z0-9_.+-]{1,80}',args.version):
        raise ValueError('unsafe dependency research identity')
    target=RAW/'active'/args.project
    if json.loads((target/'task-owned.json').read_text(encoding='utf-8'))['slug']!=args.project:raise ValueError('wrong owned target')
    def fetch(url,bound):
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
            data=response.read(bound+1)
        if len(data)>bound:raise ValueError('registry research payload bound')
        return data
    url='https://registry.npmjs.org/'+urllib.parse.quote(args.package,safe='')+'/'+urllib.parse.quote(args.version,safe='')
    metadata=json.loads(fetch(url,1024**2))
    if metadata['name']!=args.package or not re.fullmatch('[0-9][a-zA-Z0-9_.+-]{0,79}',metadata['version']):raise ValueError('primary package metadata identity mismatch')
    root=target/'dependency-research'/args.package.replace('/','--')/metadata['version'];root.mkdir(parents=True)
    immutable_json(root/'registry.json',metadata)
    dist=metadata['dist'];tarball=dist['tarball']
    if not tarball.startswith('https://registry.npmjs.org/'):raise ValueError('unreviewed package source host')
    data=fetch(tarball,8*1024**2);algorithm,encoded=dist['integrity'].split('-',1)
    if algorithm!='sha512' or hashlib.sha512(data).digest()!=base64.b64decode(encoded,validate=True):raise ValueError('actual primary package source integrity mismatch')
    archive=root/'source.tgz';archive.write_bytes(data)
    entries,expanded=extract_source(data,root/'src',expanded_limit=32*1024**2,entry_limit=10000,member_limit=4*1024**2)
    immutable_json(root/'acquired.json',dict(schema_version=1,package=args.package,version=metadata['version'],
        requested_version=args.version,metadata_url=url,metadata_sha256=sha256(root/'registry.json'),
        source_url=tarball,source_sha256=sha256(archive),upstream_integrity=dist['integrity'],
        archive_entries=entries,expanded_bytes=expanded,execution_approved=False,new_project_credit=0,
        scope='Dependency source only for review; no installation, lifecycle hook, package or target execution.'))
    print('Acquired primary dependency source only:',args.package,metadata['version'],'entries',entries,'expanded',expanded,
          'license',metadata.get('license'),'engines',metadata.get('engines'),'scripts',metadata.get('scripts'))


if __name__=='__main__':main()
