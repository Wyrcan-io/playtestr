"""Prepare pinned yo with a declared, byte-accounted native host profile."""
import asyncio
import copy
import json
import os
import shutil
import sys

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign, owned_environment
from readiness_evidence import immutable_json, sha256
from readiness_storage import measure


async def main():
    package=DOC/'yo';target=RAW/'active/yo';campaign=NextCampaign()
    async def run(script,*args):
        return await execute([sys.executable,'-B',ROOT/'scripts/acceptance'/script,*args],'yo',
            'native-yo-'+script.removesuffix('.py'),cwd=ROOT,env=owned_environment(),timeout=1200,campaign=campaign)
    await run('next20_acquire.py','yo')
    await run('next20_yo_native_setup.py')
    await run('next20_yo_review.py','--native-review')
    runtime=json.loads((target/'runtime.json').read_text());node=runtime['node']
    host='windows' if os.name=='nt' else 'linux'
    contracts=RAW/'yo/host-contracts';contracts.mkdir(parents=True)
    frozen=json.loads((package/'development-test-freeze.json').read_text())
    declaration=json.loads((package/'scenarios.json').read_text());changes=[]
    for name,digest in frozen['inputs'].items():
        source=package/name
        if sha256(source)!=digest:raise ValueError('Canonical frozen input changed')
        if any(case['spec']==name for case in declaration['cases']):continue
        destination=contracts/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
    for name in frozen['directories']:(contracts/name).mkdir(parents=True,exist_ok=True)
    if host=='linux':
        snapshot=contracts/'snapshots/javascript-complete.txt';before=snapshot.read_bytes()
        anchor=b'create output\\project.json'
        if before.count(anchor)!=1:raise ValueError('Reviewed snapshot path separator anchor differs')
        snapshot.write_bytes(before.replace(anchor,b'create output/project.json'))
        changes.append(dict(path='snapshots/javascript-complete.txt',canonical_sha256=frozen['inputs']['snapshots/javascript-complete.txt'],
            host_sha256=sha256(snapshot),reason='Conflicter logs native file.relativePath; exactly one Windows path separator becomes POSIX slash. Other snapshot bytes unchanged.'))
    cases=[]
    for case in declaration['cases']:
        spec=json.loads((package/case['spec']).read_text());native_case=copy.deepcopy(case)
        spec['command'][0]=os.path.relpath(node,contracts).replace('\\','/')
        if spec['command'][2].count('../runtime/app/lib/cli.js')!=1:raise ValueError('Reviewed actual same-process yo entry routing changed')
        if host=='linux':
            spec['env']['GIT_CONFIG_GLOBAL']='/dev/null';spec['inherit_env']=[]
        immutable_json(contracts/case['spec'],spec)
        cases.append(dict(native_case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(contracts/case['spec'])))
    declaration['cases']=cases;declaration['host']=host
    immutable_json(contracts/'scenarios.json',declaration)
    immutable_json(contracts/'development-test-freeze.json',dict(canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        inputs={p.relative_to(contracts).as_posix():sha256(p) for p in contracts.rglob('*') if p.is_file()},
        directories=frozen['directories'],changes=changes,
        profile='Exact native owned Node path. Linux devnull/empty Windows inheritance and one declared logged file path separator. Cancellation retains canonical exact1: actual first Linux E03 exited1 through yo error handling. All original inputs/state predicates unchanged; actual complete native execution still required.'))
    immutable_json(RAW/'yo/native-prepared.json',dict(schema_version=1,host=host,pin=runtime['source_pin'],
        target_archive_sha256=sha256(target/'source.tar.gz'),runtime_sha256=sha256(target/'runtime.json'),
        build_sha256=sha256(target/'build.json'),host_contract_freeze_sha256=sha256(contracts/'development-test-freeze.json'),
        target_bytes=measure(target)['total_bytes'],new_project_admissions=0))
    print('Prepared actual reviewed native yo with explicit',host,'profile; no admission credit.')


if __name__=='__main__':asyncio.run(main())
