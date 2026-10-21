"""Run preserved original native nnn cases with public v3 state proof."""
import asyncio
import json
import platform
from pathlib import Path
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_old_nnn_environment import environment


async def main():
    host={'Linux':'linux','Darwin':'macos'}.get(platform.system())
    if host is None:raise RuntimeError('undeclared original nnn native host')
    parent=RAW/'old-migration/nnn'/host
    materialized=load(parent/'materialized.json');source=parent/'contracts'
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!=materialized['all_package_inputs']:raise RuntimeError('prepared original native package changed')
    target=RAW/'active/old-nnn';build=load(target/'build.json');runtime=load(target/'runtime.json')
    if build['pin']!=materialized['pin']:raise RuntimeError('wrong original target pin')
    root=parent/'runs'/uuid.uuid4().hex;root.mkdir(parents=True)
    package=root/'contracts';shutil.copytree(source,package)
    header=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn/owned-path-header-review.json')
    source_review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn/source-review.json')
    if any(source_review['reviewed_inputs'][name]!=digest for name,digest in header['source_oracle'].items()):
        raise RuntimeError('reviewed path abbreviation source changed')
    env=environment();tempbase=Path(env['TMPDIR']).resolve(strict=True)
    if len(str(tempbase/'workspace'/'fixture').encode('utf-8'))+16<=100:
        raise RuntimeError('declared long-path header context is absent')
    if (len(tempbase.parts)+3)*2+16+max(len(e['context_expect'].split('/')[-1].encode('utf-8')) for e in header['entries'])>100:
        raise RuntimeError('declared context may truncate the final path component')
    changes=[]
    for name in sorted({e['spec'] for e in header['entries']}):
        path=package/name;prepared=sha256(path);contract=load(path)
        entries=[e for e in header['entries'] if e['spec']==name]
        if contract['width']!=100 or contract['workspace']['home']!='temporary':
            raise RuntimeError('undeclared path/header viewport or home context')
        for entry in entries:
            if (prepared!=entry['prepared_spec_sha256'][host]
                    or contract['steps'][entry['step']-1]!={'expect':entry['original_expect']}):
                raise RuntimeError('original reviewed path checkpoint changed')
            contract['steps'][entry['step']-1]={'expect':entry['context_expect']}
        path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(spec=name,prepared_sha256=prepared,executed_sha256=sha256(path),steps=[e['step'] for e in entries]))
    immutable_json(root/'execution-profile.json',dict(original_materialized_sha256=sha256(parent/'materialized.json'),
        target_build_sha256=sha256(target/'build.json'),changes=changes,
        header_review_sha256=sha256(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn/owned-path-header-review.json'),
        operational_change='Ten source-reviewed positive path-header anchors reflect long owned pathname abbreviation. All original snapshots, fixtures, remaining actions and saved-state expectations unchanged.'))
    binary,candidate,cell=runner('migration-v2')
    specs=[(package/(row['case']+'.json')).relative_to(ROOT) for row in materialized['cases']]
    listing=await execute([binary,'test','--list',*specs],'old-nnn','migration-public-native-selection',
        env=env,timeout=30,campaign=Campaign())
    selection=root/'selected.txt';selection.write_text(listing['output'],encoding='utf-8',newline='\n')
    if listing['output'].splitlines()[0]!='Selected 17 specs:':raise RuntimeError('wrong original nnn native denominator')
    report=root/'results.json'
    result=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','old-nnn',
        '--selection',selection.relative_to(ROOT),'--',binary,'test','--report',report.relative_to(ROOT),
        '--artifacts-dir',(root/'evidence').relative_to(ROOT),*specs],'old-nnn','migration-original-seventeen-suite-parent',
        env=env,timeout=600,campaign=Campaign())
    outcome=load(report)
    if outcome['runner_version']!=candidate['version'] or outcome['summary']!=dict(total=17,passed=17,failed=0,cancelled=0,not_run=0):
        raise RuntimeError('original native migration suite incomplete')
    if len({r['invocation_id'] for r in outcome['results']})!=17:raise RuntimeError('duplicate original migration invocation')
    for row in outcome['results']:
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise RuntimeError('migration cleanup unconfirmed')
        for step in row['steps']:
            if step['status']!='passed':raise RuntimeError('incomplete migration action')
            if 'state' in step and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):
                raise RuntimeError('migration state came from another execution')
    immutable_json(root/'verified.json',dict(project='nnn',host=host,cases=17,parent_attempt=result['id'],
        report_sha256=sha256(report),execution_profile_sha256=sha256(root/'execution-profile.json'),runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],target_pin=build['pin'],target_build_sha256=sha256(target/'build.json'),
        scope='Actual original native cases with public same-execution saved-state assertions. Corruption/recovery, second host and independent audit still required.',
        migrated_project_credit=0,final_archive_credit=0))
    print('Seventeen original native nnn cases passed with public same-execution state proof:',host)


if __name__=='__main__':asyncio.run(main())
