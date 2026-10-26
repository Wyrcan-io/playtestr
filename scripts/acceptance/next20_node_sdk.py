"""Acquire one owned Windows Node prerequisite from official checksummed bytes."""
import argparse
import io
import json
import re
import urllib.request
import zipfile

from next20_check import RAW,NAME
from readiness_evidence import immutable_json,sha256
import hashlib


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',required=True);args=parser.parse_args()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',args.version):raise ValueError('unsafe Node SDK version')
    version='v'+args.version;name='node-'+version+'-win-x64'
    root=RAW/'toolchain/node-sdk'/name
    if root.exists():raise ValueError('Existing prerequisite must be verified/reused, not overwritten')
    root.mkdir(parents=True)
    def fetch(url,bound):
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
            data=response.read(bound+1)
        if len(data)>bound:raise ValueError('Node SDK download bound')
        return data
    base='https://nodejs.org/dist/'+version+'/'
    sums=fetch(base+'SHASUMS256.txt',256*1024);checksum=root/'SHASUMS256.txt';checksum.write_bytes(sums)
    entries=[line.split() for line in sums.decode('ascii').splitlines()]
    matches=[row[0] for row in entries if len(row)==2 and row[1]==name+'.zip']
    if len(matches)!=1 or not re.fullmatch('[0-9a-f]{64}',matches[0]):raise ValueError('Missing exact official SDK checksum')
    archive=root/(name+'.zip');data=fetch(base+name+'.zip',64*1024**2)
    if hashlib.sha256(data).hexdigest()!=matches[0]:raise ValueError('Actual Node SDK differs from official checksum')
    archive.write_bytes(data);expanded=0;files={};folded=set()
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        members=source.infolist()
        if len(members)>10000:raise ValueError('Node SDK entry bound')
        for member in members:
            relative=member.filename
            if not relative.startswith(name+'/') or relative.startswith('/') or any(p in {'..','.'} or ':' in p or '\\' in p for p in relative.split('/')):
                raise ValueError('Unsafe Node SDK member')
            if relative.casefold() in folded:raise ValueError('Ambiguous Node SDK member')
            folded.add(relative.casefold());mode=(member.external_attr>>16)&0o170000
            if mode not in {0,0o040000,0o100000}:raise ValueError('Unreviewed SDK special entry')
            expanded+=member.file_size
            if expanded>256*1024**2 or member.file_size>128*1024**2:raise ValueError('Node SDK expansion bound')
            destination=root/relative;destination.resolve().relative_to(root.resolve())
            if member.is_dir():destination.mkdir(parents=True,exist_ok=True);continue
            destination.parent.mkdir(parents=True,exist_ok=True)
            with source.open(member) as stream,destination.open('xb') as output:
                remaining=member.file_size
                while block:=stream.read(min(65536,remaining+1)):
                    remaining-=len(block)
                    if remaining<0:raise ValueError('SDK member exceeded declared size')
                    output.write(block)
                if remaining:raise ValueError('SDK member incomplete')
            files[relative]=sha256(destination)
    node=root/name/'node.exe'
    immutable_json(root/'task-owned.json',dict(schema_version=1,campaign=NAME,kind='shared-node-prerequisite',version=version,
        archive_url=base+name+'.zip',checksum_url=base+'SHASUMS256.txt',checksum_manifest_sha256=sha256(checksum),
        archive_sha256=sha256(archive),node_sha256=sha256(node),node_relative_path=node.relative_to(RAW).as_posix(),
        files=files,expanded_bytes=expanded,execution_approved=False,
        scope='Official checksum-verified owned prerequisite data only. No global install or SDK execution. Preserve shared prerequisite after individual target cleanup.'))
    print('Acquired checksum-verified Node prerequisite data:',version,'files',len(files),'expanded',expanded,'node_sha256',sha256(node),'not yet executed')


if __name__=='__main__':main()
