"""Run each declared jrnl development scenario once and retain every outcome."""
import asyncio
import argparse
import json
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from next20_candidate import executable,SERIES


async def main(project='jrnl',candidate_series='rc5'):
    package=DOC/project;target=RAW/'active'/project;campaign=NextCampaign()
    declaration=json.loads((package/'scenarios.json').read_text())
    env=environment(target)
    installed=json.loads((target/'installed-inventory.json').read_text());inventory=installed['files']
    runtime_root=ROOT/installed['runtime_root'] if 'runtime_root' in installed else target/'venv'
    runtime_root.resolve(strict=True).relative_to(target.resolve(strict=True))
    catalog_path=target/'launch-runtime-catalog.json'
    def dependencies():
        for name,digest in inventory.items():
            if sha256(runtime_root/name)!=digest:raise ValueError('installed dependencies changed: '+name)
        if 'runtime_root' in installed:
            catalog=json.loads(catalog_path.read_text())
            if ROOT/catalog['runtime_root']!=runtime_root:raise ValueError('Actual compiled runtime root differs')
            for name,digest in catalog['files'].items():
                if sha256(runtime_root/name)!=digest:raise ValueError('compiled/runtime dependency changed: '+name)
    dependencies()
    root=RAW/project/'development'/uuid.uuid4().hex;root.mkdir(parents=True)
    runner=executable(candidate_series)
    results=[]
    for case in declaration['cases']:
        spec=package/case['spec']
        if sha256(spec)!=case['spec_sha256']:raise ValueError('undeclared development contract change')
        report=root/(case['id']+'.report.json')
        planned=dict(project=project,case=case['id'],phase='development',spec=spec.relative_to(ROOT).as_posix(),
            spec_sha256=sha256(spec),runner_sha256=sha256(runner),runtime_sha256=sha256(target/'runtime.json'),
            source_build_sha256=sha256(target/'build.json'),expected_runner_exit=0)
        immutable_json(root/(case['id']+'.planned.json'),planned)
        try:
            result=await execute([runner,'test','--report',report,spec],project,'development-'+case['id'],
                cwd=ROOT,env=env,timeout=140,campaign=campaign)
            eid=result['id']
        except RuntimeError as error:
            eid=getattr(error,'evidence_id',None)
            if not eid or not report.exists():raise
            finish=json.loads((RAW/'events'/(eid+'-finished.json')).read_text())
            if finish['category']!='exit_mismatch':raise
        report_data=json.loads(report.read_text())
        if len(report_data['results'])!=1:raise ValueError('development individual report count')
        row=report_data['results'][0]
        observation=dict(case=case['id'],attempt=eid,status=row['status'],
            category=row.get('failure',{}).get('category'),report=report.relative_to(ROOT).as_posix(),
            report_sha256=sha256(report),spec_sha256=sha256(spec),
            invocation=row.get('invocation_id'),workspace_cleaned=row.get('workspace',{}).get('cleaned'),
            target_exited=row.get('cleanup',{}).get('confirmed_exited'))
        results.append(observation)
        immutable_json(root/(case['id']+'.observation.json'),observation)
        print(case['id'],row['status'],observation['category'],flush=True)
        if not observation['workspace_cleaned'] or not observation['target_exited']:
            raise ValueError('stop development after unconfirmed target/workspace cleanup')
    dependencies()
    immutable_json(root/'summary.json',dict(schema_version=1,phase='development',
        declaration_sha256=sha256(package/'scenarios.json'),results=results,
        passed=sum(r['status']=='passed' for r in results),failed=sum(r['status']!='passed' for r in results),
        project_admissions=0,final_ordinary_credit=0))
    if any(r['status']!='passed' for r in results):raise ValueError('development cases failed; inspect preserved individual reports')
    print('All twenty declared development cases passed once; final repetition/fault/native admission remains open.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='jrnl')
    parser.add_argument('--candidate-series',choices=SERIES,default='rc5');args=parser.parse_args()
    if not (DOC/args.project/'source-provenance.json').is_file() or '/' in args.project or '\\' in args.project:
        raise ValueError('undeclared project')
    asyncio.run(main(args.project,args.candidate_series))
