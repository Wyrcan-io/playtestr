"""Retain primary release identities and inspect wheel hooks without importing them."""
import argparse
from email.parser import BytesParser
import hashlib
import json
import re
import urllib.parse
import urllib.request
import zipfile

from next20_check import RAW
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--revision',type=int,choices=[1,2],default=1);args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('unsafe project')
    target=RAW/'active'/args.project;target.resolve(strict=True).relative_to((RAW/'active').resolve())
    fetch=target/('dependency-fetch.json' if args.revision==1 else 'dependency-fetch-v2.json');inventory=json.loads(fetch.read_text())['wheels']
    if not 1<=len(inventory)<=64:raise ValueError('wheel inventory bound')
    root=target/'wheel-review-inputs';root.mkdir(exist_ok=True);rows=[];expanded=0
    for name,row in sorted(inventory.items()):
        if '/' in name or '\\' in name or not name.endswith('.whl'):raise ValueError('unsafe wheel name')
        path=target/'wheels'/name
        if path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:raise ValueError('fetched wheel changed')
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist();size=sum(i.file_size for i in infos);expanded+=size
            if len(infos)>10000 or size>128*1024**2 or expanded>256*1024**2:raise ValueError('expanded review bound')
            names=[i.filename for i in infos]
            if len(set(names))!=len(names):raise ValueError('duplicate wheel member')
            metadata=[n for n in names if n.endswith('.dist-info/METADATA') and len(n.split('/'))==2]
            if len(metadata)!=1:raise ValueError('ambiguous wheel identity')
            info=BytesParser().parsebytes(archive.read(metadata[0]));package=info['Name'];version=info['Version']
            if not all(re.fullmatch('[A-Za-z0-9_.+-]{1,100}',v) for v in [package,version]):raise ValueError('unsafe package identity')
            primary=root/(name+'.pypi.json')
            url='https://pypi.org/pypi/'+urllib.parse.quote(package,safe='')+'/'+urllib.parse.quote(version,safe='')+'/json'
            if primary.exists():data=primary.read_bytes()
            else:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:data=response.read(4*1024**2+1)
                if len(data)>4*1024**2:raise ValueError('primary metadata bound')
                with primary.open('xb') as stream:stream.write(data)
            release=json.loads(data);matches=[f for f in release['urls'] if f['filename']==name]
            if len(matches)!=1 or matches[0]['digests']['sha256']!=row['sha256'] or matches[0]['size']!=row['bytes']:raise ValueError('primary wheel identity differs')
            hooks={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names if n.endswith('.pth') or '.data/scripts/' in n}
            licenses={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names if 'license' in n.lower() or 'copying' in n.lower()}
            rows.append(dict(wheel=name,name=package,version=version,sha256=row['sha256'],bytes=row['bytes'],expanded_bytes=size,
                primary=url,primary_metadata_sha256=sha256(primary),hooks=hooks,license_members=licenses,
                license=info.get('License-Expression') or info.get('License'),entry_points=[n for n in names if n.endswith('.dist-info/entry_points.txt')]))
    immutable_json(root/('index.json' if args.revision==1 else 'index-v2.json'),dict(schema_version=1,dependency_fetch_sha256=sha256(fetch),wheels=rows,
        approved_for_install=False,scope='Primary identities and exact hook/license locations only; no imported wheel code or install/target execution approval.'))
    print('Verified',len(rows),'primary wheel identities;',expanded,'expanded bytes; install remains unapproved.')


if __name__=='__main__':main()
