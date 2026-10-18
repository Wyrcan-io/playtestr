"""Relocate approved public exports, verify the ordinary suite, then freeze."""
import asyncio
import os
import json
from pathlib import Path
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_frogmouth_cases import environment,plan_hash,rows,serialise
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_frogmouth_first_use import runner as select_runner


async def main():
    package=RAW/'frogmouth/contracts';package.mkdir(exist_ok=False)
    (package/'snapshots').mkdir();approved=[]
    for row in rows():
        candidates=[]
        for candidate in (RAW/'frogmouth/authoring'/row['id']).glob('*/approved.json'):
            value=json.loads(candidate.read_text(encoding='utf-8-sig'))
            if value['plan_sha256']==plan_hash(row):candidates.append(candidate)
        if not candidates:raise RuntimeError('no approved current plan for '+row['id'])
        # Any passing unchanged plan is eligible; path order makes selection stable.
        approval_path=sorted(candidates)[0]
        approval=json.loads(approval_path.read_text(encoding='utf-8-sig'))
        source=approval_path.parent/'spec.json'
        if sha256(source)!=approval['spec_sha256']:raise RuntimeError('approved public export changed')
        value=json.loads(source.read_text(encoding='utf-8-sig'))
        destination='fixtures/'+row['id'];shutil.copytree(source.parent/'fixture',package/destination)
        value['workspace']['fixture']=destination;value['name']='frogmouth '+row['id']+': '+row['title']
        # Relocation and a readable name change no public action or expected byte.
        for step in value['steps']:
            if 'snapshot' in step:
                snapshot=step['snapshot'];shutil.copyfile(source.parent/'snapshots'/snapshot,package/'snapshots'/snapshot)
        path=package/(row['id']+'.json');path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        if json.loads(path.read_text())['steps']!=json.loads(source.read_text(encoding='utf-8-sig'))['steps']:
            raise RuntimeError('assembly changed an approved action')
        approved.append(dict(id=row['id'],approval_sha256=sha256(approval_path),export_sha256=approval['spec_sha256'],
            contract_sha256=sha256(path),plan_sha256=approval['plan_sha256']))
    root=RAW/'frogmouth/suites'/uuid.uuid4().hex;root.mkdir(parents=True)
    runner=select_runner()
    selected=await execute([runner,'test','--list',package.relative_to(ROOT)],'frogmouth','public-twenty-directory-list',
        env=environment(),timeout=30,campaign=Campaign())
    selection=root/'selected.txt';selection.write_text(selected['output'],encoding='utf-8',newline='\n')
    report=root/'results.json'
    suite=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','frogmouth','--selection',
        selection.relative_to(ROOT),'--',runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
        (root/'evidence').relative_to(ROOT),package.relative_to(ROOT)],'frogmouth','full-public-twenty-contract-suite-parent',
        env=environment(),timeout=600,campaign=Campaign())
    outcomes=json.loads(report.read_text(encoding='utf-8-sig'))
    if outcomes['summary']!=dict(total=20,passed=20,failed=0,cancelled=0,not_run=0):raise RuntimeError('full ordinary suite incomplete')
    for result in outcomes['results']:
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:raise RuntimeError('suite cleanup unconfirmed')
        for step in result['steps']:
            if 'state' in step:
                state=step['state']
                if state['invocation_id']!=result['invocation_id'] or state['workspace_id']!=result['workspace']['id']:
                    raise RuntimeError('cross-invocation state proof')
    files={path.relative_to(package).as_posix():sha256(path) for path in package.rglob('*') if path.is_file()}
    freeze=RAW/'frogmouth/reviewed-contract-freeze.json'
    immutable_json(freeze,dict(schema_version=1,contracts={r['id']+'.json':r['contract_sha256'] for r in approved},
        all_package_inputs=files,approvals=approved,normal_scenarios=8,edge_scenarios=12,
        ordinary_parent=suite['id'],ordinary_report_sha256=sha256(report),runner_sha256=sha256(runner),
        target_build_sha256=sha256(RAW/'active/frogmouth/build.json'),holdout='No source fault selected before this freeze.'))
    print('Twenty reviewed Markdown browsing contracts pass the ordinary public directory suite and are frozen before fault selection.')


if __name__=='__main__':asyncio.run(main())
