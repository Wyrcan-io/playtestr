"""Prepare reviewed cz-cli source/runtime and the explicit native host profile."""
import asyncio
import copy
import json
import os
import shutil
import sys

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from next20_fixture_git import reconstruct
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


async def main():
    project='cz-cli';package=DOC/project;target=RAW/'active'/project;campaign=NextCampaign()
    async def run(script,*args):
        return await execute([sys.executable,'-B',ROOT/'scripts/acceptance'/script,*args],project,
            'native-'+project+'-'+script.removesuffix('.py'),cwd=ROOT,env=owned_environment(),timeout=1200,campaign=campaign)
    await run('next20_acquire.py',project)
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    source=target/'src'
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:
        raise ValueError('Native acquired source differs from all reviewed pinned Git blobs')
    await run('next20_cz_cli_lock.py','--verify-declaration')
    await run('next20_cz_cli_setup.py')
    # Preserve bounded actual setup metadata even if the subsequent build guard
    # refuses it. No active executable, npm cache or installed tree is copied.
    setup=RAW/project/'native-setup';setup.mkdir(parents=True)
    for name in ['task-owned.json','acquisition.json','dependency-fetch.json','node-prerequisite.json','build-lock-derivation.json']:
        shutil.copyfile(target/name,setup/name)
        if sha256(target/name)!=sha256(setup/name):raise ValueError('Native setup metadata copy differs')
    shutil.copytree(target/'npm-installed-locks',setup/'npm-installed-locks')
    await run('next20_cz_cli_build.py','--native-review')
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'));node=runtime['node']
    host='windows' if os.name=='nt' else 'linux'
    reconstruct(package)
    contracts=RAW/project/'host-contracts';contracts.mkdir(parents=True)
    frozen=json.loads((package/'development-test-freeze.json').read_text(encoding='utf-8'))
    declaration=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    for name,digest in frozen['inputs'].items():
        source_input=package/name
        if sha256(source_input)!=digest:raise ValueError('Canonical frozen input changed before native preparation')
        if any(c['spec']==name for c in declaration['cases']):continue
        destination=contracts/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_input,destination)
    for name in frozen['directories']:(contracts/name).mkdir(parents=True,exist_ok=True)
    cases=[]
    for case in declaration['cases']:
        spec=json.loads((package/case['spec']).read_text(encoding='utf-8'))
        spec['command'][0]=os.path.relpath(node,contracts).replace('\\','/')
        if spec['command'][2].count('../app-v2/bin/git-cz')!=1:raise ValueError('Reviewed same-process standard entry launcher changed')
        spec['command'][2]=spec['command'][2].replace('../app-v2/bin/git-cz','../'+runtime['app_relative_path']+'/bin/git-cz')
        native_case=copy.deepcopy(case)
        if host=='linux':
            spec['env']['PATH']='/usr/bin:/bin';spec['env']['GIT_CONFIG_GLOBAL']='/dev/null';spec['inherit_env']=[]
            if case['id'] in {'E01','E02'}:
                for step in spec['steps']:
                    if 'exit' in step:
                        if step['exit']!=1:raise ValueError('Reviewed Windows interrupt code changed')
                        step['exit']=130
                native_case['expected_exit']=130
        immutable_json(contracts/case['spec'],spec)
        cases.append(dict(native_case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(contracts/case['spec'])))
    declaration['cases']=cases;declaration['host']=host;immutable_json(contracts/'scenarios.json',declaration)
    immutable_json(contracts/'development-test-freeze.json',dict(canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        inputs={p.relative_to(contracts).as_posix():sha256(p) for p in contracts.rglob('*') if p.is_file()},
        directories=frozen['directories'],profile='Exact native owned Node path and same-process standard entry location. Linux explicit Git PATH/devnull, empty inherited Windows names, self-SIGINT130 instead of observed Windows1. All inputs, other actions, file bytes and snapshot stay exact; native outcomes must verify the planned profile.'))
    immutable_json(RAW/project/'native-prepared.json',dict(schema_version=1,host=host,pin=provenance['pin'],
        target_archive_sha256=sha256(target/'source.tar.gz'),runtime_sha256=sha256(target/'runtime.json'),
        build_sha256=sha256(target/'build.json'),host_contract_freeze_sha256=sha256(contracts/'development-test-freeze.json'),
        target_bytes=measure(target)['total_bytes'],new_project_admissions=0))
    print('Prepared actual reviewed native cz-cli and explicit',host,'profile; no execution/admission credit.')


if __name__=='__main__':asyncio.run(main())
