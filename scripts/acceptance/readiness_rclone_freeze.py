"""Run and freeze twenty reviewed Rclone public contracts before fault selection."""
import asyncio
import copy
import json
import os
import platform
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import plan_hash, require
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_rclone_cases import rows


async def main():
    package=RAW/'rclone/contracts'
    package.mkdir(exist_ok=False)
    (package/'snapshots').mkdir()
    approvals=[]
    for row in rows():
        approval_path=RAW/'rclone/approved'/(row['id']+'.json')
        approval=load(approval_path)
        require(approval['plan_sha256']==plan_hash(row),'approved native plan changed')
        source=ROOT/approval['spec']
        require(sha256(source)==approval['spec_sha256'],'approved public export changed')
        contract=load(source)
        original_steps=copy.deepcopy(contract['steps'])
        fixture='fixtures/'+row['id']
        shutil.copytree(source.parent/'fixture',package/fixture)
        contract['workspace']['fixture']=fixture
        contract['name']='Rclone '+row['id']+': '+row['title']
        renamed={}
        for step in contract['steps']:
            if 'snapshot' not in step:continue
            name=step['snapshot']
            require(name in {'final.txt','invalid-menu.txt'},'unreviewed snapshot reference')
            destination=row['id']+'-'+name
            shutil.copyfile(source.parent/'snapshots'/name,package/'snapshots'/destination)
            renamed[destination]=name
            step['snapshot']=destination
        comparable=copy.deepcopy(contract['steps'])
        for step in comparable:
            if 'snapshot' in step:step['snapshot']=renamed[step['snapshot']]
        require(comparable==original_steps,'reference relocation changed public behavior/expectations')
        path=package/(row['id']+'.json')
        path.write_text(json.dumps(contract,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        approvals.append(dict(id=row['id'],approval_sha256=sha256(approval_path),plan_sha256=plan_hash(row),
            exported_spec_sha256=sha256(source),contract_sha256=sha256(path),reference_relocation=renamed))
    binary,frozen,cell=runner()
    env=environment(RAW/'active/rclone')
    env['PATH']=str(RAW/'active/rclone/bin')+os.pathsep+env.get('PATH','')
    root=RAW/'rclone/suites'/uuid.uuid4().hex
    root.mkdir(parents=True)
    listing=await execute([binary,'test','--list',package.relative_to(ROOT)],'rclone','public-twenty-directory-list',
                          env=env,timeout=30,campaign=Campaign())
    selection=root/'selected.txt'
    selection.write_text(listing['output'],encoding='utf-8',newline='\n')
    report=root/'results.json'
    suite=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','rclone',
        '--selection',selection.relative_to(ROOT),'--',binary,'test','--report',report.relative_to(ROOT),
        '--artifacts-dir',(root/'evidence').relative_to(ROOT),package.relative_to(ROOT)],'rclone',
        'full-public-twenty-contract-suite-parent',env=env,timeout=600,campaign=Campaign())
    outcome=load(report)
    require(outcome['runner_version']==frozen['version'] and outcome['summary']==
            dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'full public twenty-case suite incomplete')
    for result in outcome['results']:
        require(result['status']=='passed' and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'],'suite process/workspace cleanup unconfirmed')
        for step in result['steps']:
            require(step['status']=='passed','suite step incomplete')
            if 'state' in step:
                require(step['state']['invocation_id']==result['invocation_id']
                        and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state proof')
    immutable_json(RAW/'rclone/reviewed-contract-freeze.json',dict(schema_version=1,
        host=platform.system(),architecture=cell['architecture'],normal_scenarios=8,edge_scenarios=12,
        contracts={r['id']+'.json':r['contract_sha256'] for r in approvals},
        all_package_inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()},
        approvals=approvals,ordinary_parent=suite['id'],ordinary_report_sha256=sha256(report),
        runner_sha256=cell['binary_sha256'],provisional_archive_sha256=cell['archive_sha256'],
        source_revision=frozen['source_revision'],target_build_sha256=sha256(RAW/'active/rclone/build.json'),
        fault_selection='No source fault selected before this complete twenty-case freeze.',final_archive_credit=0))
    print('Twenty real Rclone public exports pass as a directory suite; frozen before source fault selection.')


if __name__=='__main__':asyncio.run(main())
