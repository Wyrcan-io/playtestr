"""Twelve declared fresh native repetitions using exact archive bytes."""
import argparse
import asyncio
import copy
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--batch',type=int,required=True);args=parser.parse_args()
    if not 0<=args.batch<12:raise ValueError('undeclared final batch')
    host='windows' if os.name=='nt' else 'linux'
    declaration=json.loads((DOC/'jrnl/final-series-declaration.json').read_text())
    if host not in declaration['hosts']:raise ValueError('undeclared host')
    root=RAW/'jrnl/final-series'/str(args.batch)
    root.mkdir(parents=True,exist_ok=False)
    canonical=RAW/'jrnl/host-contracts';package=root/('relocated café 雪' if args.batch==5 else 'contracts')
    shutil.copytree(canonical,package)
    source=RAW/'active/jrnl';runtime=json.loads((source/'runtime.json').read_text());python=Path(runtime['python'])
    inventory=json.loads((source/'installed-inventory.json').read_text())['files']
    def dependencies():
        for name,digest in inventory.items():
            if sha256(source/'venv'/name)!=digest:raise ValueError('native installed dependency changed: '+name)
    dependencies()
    # Cold means a newly materialized, hash-verified runtime copy, followed by
    # reuse in its paired warm batch. It does not claim a flushed OS file cache.
    if args.batch in {0,2}:
        clone=source/('venv-pair-'+str(args.batch//2))
        shutil.copytree(source/'venv',clone,symlinks=True)
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('fresh runtime copy mismatch')
        immutable_json(clone/'copy-identity.json',dict(source_inventory_sha256=sha256(source/'installed-inventory.json'),
            source_relative_path='venv',cold_scope='First use of a newly materialized verified runtime, not OS-cache eviction'))
    if args.batch<4:
        clone=source/('venv-pair-'+str(args.batch//2))
        if not clone.exists():raise ValueError('warm repetition missing preceding cold runtime preparation')
        python=clone/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        if sha256(python)!=runtime['python_sha256']:raise ValueError('copied executed interpreter differs')
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('actual copied dependency changed: '+name)
    actual_runtime=clone if args.batch<4 else source/'venv'
    actual_runtime_files={name:sha256(actual_runtime/name) for name in inventory}
    if actual_runtime_files!=inventory:raise ValueError('actual selected runtime does not match installed dependency bytes')
    runtime_catalog=dict(schema_version=1,runtime_root=actual_runtime.relative_to(ROOT).as_posix(),
        files=actual_runtime_files,executable=python.relative_to(ROOT).as_posix(),executable_sha256=sha256(python),
        source_inventory_sha256=sha256(source/'installed-inventory.json'))
    immutable_json(root/'runtime-catalog.json',runtime_catalog)
    shutil.copyfile(root/'runtime-catalog.json',source/'launch-runtime-catalog.json')
    cases=json.loads((canonical/'scenarios.json').read_text())['cases'];changes=[]
    for case in cases:
        before=package/case['spec'];value=json.loads(before.read_text())
        if sha256(canonical/case['spec'])!=case['spec_sha256']:raise ValueError('native base contract changed')
        value['command'][0]=os.path.relpath(python,package).replace('\\','/')
        if args.batch==4:value.update(width=value['width']+10,height=value['height']+2)
        if args.batch==7:
            steps=[]
            for step in value['steps']:
                if set(step)=={'text'} and len(step['text'])>1 and all(ord(c)>=32 and ord(c)!=127 for c in step['text']):
                    steps.extend({'text':step['text'][i:i+3]} for i in range(0,len(step['text']),3))
                else:steps.append(step)
            value['steps']=steps
        if args.batch==10 and case['id']=='N01':value['height']=12
        if args.batch==11:value['startup_timeout_ms']=2000
        before.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(case=case['id'],spec=case['spec'],canonical_sha256=case['canonical_sha256'],
            native_base_sha256=case['spec_sha256'],executed_spec_sha256=sha256(before)))
    runner=RAW/'candidate'/host/('playtestr.exe' if os.name=='nt' else 'playtestr')
    install=json.loads((runner.parent/'installed.json').read_text())
    if sha256(runner)!=install['binary_sha256']:raise ValueError('wrong final archive binary')
    env=environment(source);campaign=NextCampaign(phase='final-archive')
    immutable_json(root/'prepared.json',dict(schema_version=1,host=host,batch=args.batch,
        declaration_sha256=sha256(DOC/'jrnl/final-series-declaration.json'),changes=changes,
        runner_sha256=sha256(runner),archive_sha256=install['archive_sha256'],
        actual_python=python.relative_to(ROOT).as_posix(),actual_python_sha256=sha256(python),
        actual_runtime_catalog_sha256=sha256(root/'runtime-catalog.json'),
        installed_inventory_sha256=sha256(source/'installed-inventory.json')))
    observations=[]
    for case in cases:
        spec=package/case['spec'];report=root/(case['id']+'.report.json')
        planned=dict(schema_version=1,phase='final-archive',host=host,batch=args.batch,case=case['id'],
            spec=spec.relative_to(ROOT).as_posix(),spec_sha256=sha256(spec),runner_sha256=sha256(runner),
            archive_sha256=install['archive_sha256'],target_runtime_sha256=sha256(source/'runtime.json'),
            variation=declaration['batches'][args.batch],expected_runner_exit=0)
        immutable_json(root/(case['id']+'.planned.json'),planned)
        # No per-case retries: any failure rejects this series, with all existing
        # attempts preserved. Replacement requires an explicit new declaration.
        result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'jrnl','final-batch-'+str(args.batch)+'-'+case['id'],
            cwd=ROOT,env=env,timeout=140,load=args.batch in {8,9},campaign=campaign)
        row=json.loads(report.read_text())['results'][0]
        if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']):raise ValueError('nonpositive final steps')
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('incomplete final target/workspace cleanup')
        if any(s.get('state') and (s['state']['invocation_id']!=row['invocation_id'] or s['state']['workspace_id']!=row['workspace']['id']) for s in row['steps']):
            raise ValueError('cross-invocation final saved state')
        observations.append(dict(case=case['id'],attempt=result['id'],invocation=row['invocation_id'],
            report_sha256=sha256(report),spec_sha256=sha256(spec),passed=True))
        print(host,args.batch,case['id'],'passed',flush=True)
    dependencies()
    if args.batch<4:
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('copied runtime changed during final batch: '+name)
    immutable_json(root/'summary.json',dict(schema_version=1,phase='final-archive',host=host,batch=args.batch,
        observations=observations,ordinary_executions=20,runner_sha256=sha256(runner),archive_sha256=install['archive_sha256'],
        new_project_admissions=0,scope='One complete twenty-case fresh batch; all twelve and source faults/native audit/cleanup still required.'))


if __name__=='__main__':asyncio.run(main())
