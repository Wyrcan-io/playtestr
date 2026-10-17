"""Declare native Ruby prerequisite and actual diff/resize workflow explicitly."""
import base64
import copy
import json
from readiness_evidence import immutable_json, sha256
from readiness_rubygems_cases import PACKAGE, SENTINEL, state


def save(path,spec):
    path.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    receipt=PACKAGE/'contract-revision-3.json'
    if receipt.exists():raise RuntimeError('preserve reviewed revision')
    p=PACKAGE/'edge-build-missing.json';before=sha256(p);spec=json.loads(p.read_text())
    spec['inherit_env'].append('SystemDrive')
    spec['command'].insert(5,'--norc')
    save(p,spec)
    revisions=[dict(spec=p.name,before=before,after=sha256(p),reason='actual Ruby Windows shell-folder SystemDrive prerequisite; gem common options follow subcommand')]
    p=PACKAGE/'edge-resize-collision.json';before=sha256(p);spec=json.loads(p.read_text())
    original=b''.join(f'# reviewed original dependency line {n:04d}\n'.encode() for n in range(1200))
    assert len(original)<=65536
    fixture=PACKAGE/'diff-fixture';(fixture/'atlas').mkdir(parents=True,exist_ok=False)
    (fixture/'sentinel.txt').write_bytes(SENTINEL);(fixture/'atlas/Gemfile').write_bytes(original)
    checks=copy.deepcopy(json.loads((PACKAGE/'edge-decline-overwrite.json').read_text())['steps'][5:])
    assert checks[0]['state']['path']=='atlas/Gemfile'
    checks[0]=state('atlas/Gemfile',original)
    spec['workspace']['fixture']='diff-fixture'
    spec['env']['THOR_DIFF']='git --no-pager diff --no-index --'
    spec['steps']=[{'expect':'Overwrite'},{'text':'d'},{'key':'Enter'},{'expect':'@@'},
        {'resize':{'width':40,'height':12}},{'resize':{'width':100,'height':28}},
        {'expect':'Overwrite'},{'text':'n'},{'key':'Enter'},
        {'expect':"Gem 'atlas' was successfully created."},{'exit':0},*checks]
    save(p,spec)
    revisions.append(dict(spec=p.name,before=before,after=sha256(p),
        reason='real supported diff child with bounded dirty data; resizing while output is available; original quiet-resize failure retained and excluded',fixture_bytes=len(original)))
    immutable_json(receipt,dict(revisions=revisions,qualification='authored only; requires actual unchanged public runs'))
    print('Declared actual diff/resize route and explicit native Ruby prerequisite.')


if __name__=='__main__':main()
