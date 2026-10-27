"""Verify all captured engineering helper/module/schema inputs against exact Git source."""
import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile

from next20_check import RAW,ROOT,DOC
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256
from next20_replacement_audit import hashes


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',choices=['darwin','linux','windows'],required=True)
    p.add_argument('--run',required=True);p.add_argument('--generation',type=int,required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    if not re.fullmatch('[0-9]{1,20}',args.run) or not re.fullmatch('[0-9a-f]{40}',args.revision) or not 1<=args.generation<=1000:raise ValueError('invalid source readback scope')
    retained=RAW/'replacement-candidate'/('retained-native-v'+str(args.generation))
    index=json.loads((retained/'index.json').read_text());archive=retained/'packets.tar.gz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('packet digest differs')
    verify(archive,index['files'])
    code=subprocess.check_output(['git','archive',args.revision,'scripts/acceptance','scripts/ci','schema','go.mod','go.sum'],cwd=ROOT,timeout=60)
    if len(code)>64*1024**2:raise ValueError('qualification source archive bound')
    expected={}
    with tarfile.open(fileobj=io.BytesIO(code)) as stream:
        for member in stream:
            if member.isfile() and (member.name.endswith('.py') or member.name.startswith('schema/') and member.name.endswith('.json') or member.name in {'go.mod','go.sum'}):
                expected[member.name]=hashes(stream.extractfile(member).read())
    prefix='native/'+args.run+'/next20-private-replacement-'+{'darwin':'macOS','linux':'Linux','windows':'Windows'}[args.host]+'/'
    observed=[]
    with tarfile.open(archive,'r:gz') as stream:
        def read(name):
            row=index['files'][name];data=stream.extractfile(row.get('member',name)).read(row['bytes']+1)
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('retained logical member mismatch')
            return json.loads(data)
        for name in sorted(index['files']):
            if not name.startswith(prefix+'events/') or not name.endswith('-identified.json'):continue
            row=read(name);ref=row['identity']
            reference=ref['manifest'].replace('\\','/')
            if any(part in {'','.','..'} for part in reference.split('/')):raise ValueError('unsafe identity reference')
            manifest_name=prefix+reference
            if index['files'][manifest_name]['sha256']!=ref['sha256']:raise ValueError('original identity reference differs')
            manifest=read(manifest_name);files=manifest['files']
            if any(n not in files or files[n] not in allowed for n,allowed in expected.items()):
                raise ValueError('complete engineering helper/schema/module source binding mismatch')
            observed.append(dict(attempt=row['id'],manifest_sha256=ref['sha256'],matched_qualification_inputs=len(expected)))
    if len(observed)!=12:raise ValueError('expected twelve original native command identities')
    immutable_json(DOC/('replacement-source-readback-'+args.host+'-'+args.run+'.json'),dict(schema_version=1,
        host=args.host,run=args.run,qualification_revision=args.revision,retained_generation=args.generation,
        retained_archive_sha256=sha256(archive),qualification_inputs=len(expected),commands=observed,
        comparison='Every captured Python helper under scripts/acceptance and scripts/ci, root module files and root JSON schemas match exact qualification Git blobs; LF/CRLF source spelling accepted. Candidate production inputs separately verified by original native archive auditor. No spec/fixture/report normalization.',
        project_credits=0))
    print('Verified complete helper/module/schema binding for12 original commands:',args.host,len(expected),'Git inputs each')


if __name__=='__main__':main()
