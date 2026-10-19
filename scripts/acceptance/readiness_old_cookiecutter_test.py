"""Run preserved original native Cookiecutter cases with public v3 state proof."""
import asyncio
import json
import platform
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_old_cookiecutter_prepare import environment


async def main():
    host={'Windows':'windows','Linux':'linux'}.get(platform.system())
    if host is None:raise RuntimeError('undeclared original Cookiecutter native host')
    parent=RAW/'old-migration/cookiecutter'/host
    materialized=load(parent/'materialized.json');source=parent/'contracts'
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!=materialized['all_package_inputs']:raise RuntimeError('prepared original native package changed')
    target=RAW/'active/old-cookiecutter';build=load(target/'build.json');runtime=load(target/'runtime.json')
    if build['pin']!=materialized['pin'] or runtime['source_pin']!=build['pin']:raise RuntimeError('wrong original target pin')
    root=parent/'runs'/uuid.uuid4().hex;root.mkdir(parents=True)
    package=root/'contracts';shutil.copytree(source,package)
    changes=[]
    for row in materialized['cases']:
        path=package/(row['case']+'.json');contract=load(path);before=load(source/path.name)
        env=contract.setdefault('env',{})
        if env.get('PYTHONDONTWRITEBYTECODE') not in {None,'1'}:raise RuntimeError('conflicting original cache policy')
        env['PYTHONDONTWRITEBYTECODE']='1'
        path.write_text(json.dumps(contract,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        if contract['steps']!=before['steps']:raise RuntimeError('migration changed original public steps or saved-state assertions')
        changes.append(dict(case=row['case'],before_sha256=sha256(source/path.name),execution_sha256=sha256(path)))
    immutable_json(root/'execution-profile.json',dict(original_materialized_sha256=sha256(parent/'materialized.json'),
        target_build_sha256=sha256(target/'build.json'),changes=changes,
        operational_change='Explicit PYTHONDONTWRITEBYTECODE=1 prevents target imports writing to installed base-Python paths. Original commands, input/screen/exit steps, fixture/snapshot bytes and saved-state expectations remain unchanged.'))
    binary,candidate,cell=runner();env=environment()
    specs=[(package/(row['case']+'.json')).relative_to(ROOT) for row in materialized['cases']]
    listing=await execute([binary,'test','--list',*specs],'old-cookiecutter','migration-public-native-selection',
        env=env,timeout=30,campaign=Campaign())
    selection=root/'selected.txt';selection.write_text(listing['output'],encoding='utf-8',newline='\n')
    if listing['output'].splitlines()[0]!='Selected 10 specs:':raise RuntimeError('wrong original Cookiecutter native denominator')
    report=root/'results.json'
    result=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','old-cookiecutter',
        '--selection',selection.relative_to(ROOT),'--',binary,'test','--report',report.relative_to(ROOT),
        '--artifacts-dir',(root/'evidence').relative_to(ROOT),*specs],'old-cookiecutter','migration-original-ten-suite-parent',
        env=env,timeout=600,campaign=Campaign())
    outcome=load(report)
    if outcome['runner_version']!=candidate['version'] or outcome['summary']!=dict(total=10,passed=10,failed=0,cancelled=0,not_run=0):
        raise RuntimeError('original native migration suite incomplete')
    if len({r['invocation_id'] for r in outcome['results']})!=10:raise RuntimeError('duplicate original migration invocation')
    for row in outcome['results']:
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise RuntimeError('migration cleanup unconfirmed')
        for step in row['steps']:
            if step['status']!='passed':raise RuntimeError('incomplete migration action')
            if 'state' in step and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):
                raise RuntimeError('migration state came from another execution')
    immutable_json(root/'verified.json',dict(project='cookiecutter',host=host,cases=10,parent_attempt=result['id'],
        report_sha256=sha256(report),execution_profile_sha256=sha256(root/'execution-profile.json'),runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],target_pin=build['pin'],target_build_sha256=sha256(target/'build.json'),
        scope='Actual original native cases with public same-execution saved-state assertions. Corruption/recovery, second host and independent audit still required.',
        migrated_project_credit=0,final_archive_credit=0))
    print('Ten original native Cookiecutter cases passed with public same-execution state proof:',host)


if __name__=='__main__':asyncio.run(main())
