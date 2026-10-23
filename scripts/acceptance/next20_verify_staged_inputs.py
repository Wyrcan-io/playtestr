"""Verify frozen exact inputs against Git's staged bytes and Git reconstruction."""
import argparse
import base64
import hashlib
import json
import subprocess
import uuid

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    package=DOC/args.project
    package.resolve(strict=True).relative_to(DOC.resolve())
    frozen=json.loads((package/'development-test-freeze.json').read_text(encoding='utf-8'))
    declaration=json.loads((package/'fixture-git.json').read_text(encoding='utf-8'))
    prefix=package.relative_to(ROOT).as_posix()+'/'
    ordinary=git_inputs=0
    for name,digest in frozen['inputs'].items():
        if name.startswith('/') or '..' in name.split('/') or ':' in name:raise ValueError('unsafe frozen input')
        if '/.git/' in name:
            root,relative=name.split('/.git/',1)
            if root not in declaration.get('fixture_roots',['fixture']):raise ValueError('unknown reconstructed Git fixture')
            data=base64.b64decode(declaration['files'][relative],validate=True)
            git_inputs+=1
        else:
            data=subprocess.check_output(['git','show',':'+prefix+name],cwd=ROOT)
            ordinary+=1
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('staged frozen input byte mismatch: '+name)
    staged_manifest=subprocess.check_output(['git','show',':'+prefix+'fixture-git.json'],cwd=ROOT)
    if json.loads(staged_manifest)!=declaration:raise ValueError('staged fixture reconstruction differs')
    staged_freeze=subprocess.check_output(['git','show',':'+prefix+'development-test-freeze.json'],cwd=ROOT)
    if staged_freeze!=(package/'development-test-freeze.json').read_bytes():raise ValueError('staged freeze differs')
    for root in declaration.get('fixture_roots',['fixture']):
        actual=set(subprocess.check_output(['git','ls-files','-z','--',prefix+root+'/'],cwd=ROOT).decode().split('\0'))-{''}
        expected={prefix+n for n in frozen['inputs'] if n.startswith(root+'/') and '/.git/' not in n}
        if actual!=expected:raise ValueError('staged fixture has extra/missing data: '+root)
        required={root+'/.git/'+n for n in declaration['directories']}
        if not required<=set(frozen['directories']):raise ValueError('frozen Git directories incomplete')
    destination=RAW/args.project/'staging-audits'/uuid.uuid4().hex
    immutable_json(destination/'verified.json',dict(schema_version=1,project=args.project,
        frozen_inputs_sha256=sha256(package/'development-test-freeze.json'),ordinary_staged_files=ordinary,
        exact_reconstructed_git_files=git_inputs,total_frozen_inputs=ordinary+git_inputs,
        fixture_git_manifest_sha256=hashlib.sha256(staged_manifest).hexdigest(),
        scope='Exact index bytes; Git metadata reconstructed from the staged base64 declaration, empty directories from the staged freeze. No scenario/native admission credit.'))
    print('Verified exact staged inputs:',ordinary,'ordinary files +',git_inputs,'reconstructed Git files =',ordinary+git_inputs)


if __name__=='__main__':main()
