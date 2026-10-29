"""Materialize explicit local wizard contracts without reinstalling an active target."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

from next20_check import DOC, RAW, ROOT
from next20_python_host_profile import wizard_profile
from next20_python_runtime import python_runtime_root
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--profile',type=Path,required=True);args=parser.parse_args()
    if os.name!='nt' or not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('explicit Windows project required')
    package=DOC/args.project;target=RAW/'active'/args.project;profile=args.profile.resolve(strict=True);profile.relative_to(package.resolve(strict=True))
    value=json.loads(profile.read_text());frozen=json.loads((package/'development-test-freeze.json').read_text())
    if value['host']!='windows' or value['canonical_freeze_sha256']!=sha256(package/'development-test-freeze.json'):raise ValueError('local profile identity differs')
    if value['native_runtime_lock_sha256']!=sha256(package/'native-runtime-lock.json'):raise ValueError('local runtime lock differs')
    runtime=json.loads((target/'runtime.json').read_text());runtime_root=python_runtime_root(target,runtime)
    for name,digest in json.loads((target/'installed-inventory.json').read_text())['files'].items():
        if sha256(runtime_root/name)!=digest:raise ValueError('installed local runtime changed')
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('frozen input changed')
    contracts=RAW/args.project/'host-contracts';contracts.mkdir(exist_ok=False)
    declaration=json.loads((package/'scenarios.json').read_text());specs={c['spec'] for c in declaration['cases']}
    for name in frozen['directories']:(contracts/name).mkdir(parents=True,exist_ok=True)
    for name in frozen['inputs']:
        if name in specs:continue
        destination=contracts/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(package/name,destination)
    cases=[]
    for case in declaration['cases']:
        spec=json.loads((package/case['spec']).read_text())
        spec=wizard_profile(spec,dict(case,**value['case_profiles'].get(case['id'],{})),runtime['python'],'windows')
        spec['command'][0]=os.path.relpath(runtime['python'],contracts).replace('\\','/')
        immutable_json(contracts/case['spec'],spec)
        cases.append(dict(case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(contracts/case['spec'])))
    declaration['cases']=cases;declaration['host']='windows';immutable_json(contracts/'scenarios.json',declaration)
    inputs={p.relative_to(contracts).as_posix():sha256(p) for p in contracts.rglob('*') if p.is_file()}
    immutable_json(contracts/'development-test-freeze.json',dict(canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        explicit_profile_sha256=sha256(profile),inputs=inputs,profile=value['scope']))
    print('Materialized20 exact Windows host contracts; existing reviewed runtime reused; no execution/admission credit.')


if __name__=='__main__':main()
