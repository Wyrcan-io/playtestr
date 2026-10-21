"""Execute the predeclared twelve-by-twenty exact-archive fff series."""
import argparse
import asyncio
import json
import platform
import shutil

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_fff_cases import environment
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--batch',type=int,choices=range(12))
    args=parser.parse_args()
    host={'Linux':'linux','Darwin':'macos'}.get(platform.system())
    if not host:
        raise RuntimeError('undeclared final fff native host')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    declaration=load(docs/'fff/final-series-declaration.json')
    binary,candidate,cell=runner('migration-v2')
    if sha256(docs/'migration-candidate-freeze.json')!=declaration['candidate_freeze_sha256']:
        raise RuntimeError('predeclared exact final candidate differs')
    source=RAW/'fff/host-contracts'
    profile=docs/'fff'/('native-profiles/macos' if host=='macos' else '.')
    freeze=load(profile/'reviewed-contract-freeze.json')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=freeze['all_package_inputs']:
        raise RuntimeError('reviewed native package changed')
    root=RAW/'fff/final-series'
    if args.batch is None:
        root.mkdir()
        build=load(RAW/'active/fff/build.json')
        immutable_json(root/'intent.json',dict(declaration_sha256=sha256(docs/'fff/final-series-declaration.json'),
            host=host,runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],
            target_build_sha256=sha256(RAW/'active/fff/build.json'),target_pin=build['pin'],
            canonical_package_inputs=freeze['all_package_inputs'],planned_batches=12,planned_scenarios_per_batch=20,
            final_archive_credit=0,scope='Prelaunch intent only; full native/fault/cleanup/auditor gates required.'))
        # Existing fault helpers consume this exact byte-for-byte archive copy.
        alias=RAW/'bin/playtestr'
        alias.parent.mkdir(exist_ok=True)
        shutil.copyfile(binary,alias)
        alias.chmod(0o755)
        if sha256(alias)!=cell['binary_sha256']:
            raise RuntimeError('exact archive alias differs')
        immutable_json(RAW/'fff-native-runner.json',dict(source_revision=candidate['source_revision'],
            candidate_sha256=cell['binary_sha256'],copied_sha256=sha256(alias),archive_sha256=cell['archive_sha256'],
            scope='Exact final candidate archive alias; no source rebuild.'))
        for batch in declaration['batches']:
            folder=root/str(batch['number'])
            folder.mkdir()
            package=folder/batch['package_directory']
            shutil.copytree(source,package)
            changes=[]
            for name in sorted(freeze['contracts']):
                path=package/name
                before=load(path)
                after=dict(before)
                if batch['input_chunks']:
                    steps=[]
                    for step in before['steps']:
                        if set(step)=={'text'} and len(step['text'])>batch['input_chunks']:
                            text=step['text'];size=batch['input_chunks']
                            steps.extend({'text':text[i:i+size]} for i in range(0,len(text),size))
                        else:
                            steps.append(step)
                    if len(steps)>1000:
                        raise RuntimeError('declared segmented input exceeds public step limit')
                    after['steps']=steps
                    path.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
                changes.append(dict(spec=name,canonical_sha256=freeze['contracts'][name],executed_sha256=sha256(path)))
            immutable_json(folder/'prepared.json',dict(batch=batch,changes=changes,
                package_inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}))
        print('Prepared twelve frozen native batches, twenty cases each; no execution credit.')
        return
    folder=root/str(args.batch)
    prepared=load(folder/'prepared.json');batch=prepared['batch'];package=folder/batch['package_directory']
    if {p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}!=prepared['package_inputs']:
        raise RuntimeError('final batch inputs changed')
    records=[]
    for number,name in enumerate(sorted(freeze['contracts'])):
        spec=package/name
        report=folder/(name+'.report.json')
        immutable_json(folder/(name+'.planned.json'),dict(batch=args.batch,number=number,spec=name,
            runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],spec_sha256=sha256(spec),
            prepared_sha256=sha256(folder/'prepared.json'),owned_two_second_worker=batch['contention']))
        result=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (folder/(name+'.evidence')).relative_to(ROOT),spec.relative_to(ROOT)],'fff',
            'final-batch-'+str(args.batch)+'-'+name,env=environment(),timeout=130,
            load=batch['contention'],campaign=Campaign())
        value=load(report);row=value['results'][0]
        if value['runner_version']!=candidate['version'] or value['summary']!=dict(total=1,passed=1,failed=0,cancelled=0,not_run=0):
            raise RuntimeError('failed/incomplete final scenario; this series is rejected, no retry')
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned'] or any(s['status']!='passed' for s in row['steps']):
            raise RuntimeError('final positive step evidence or cleanup incomplete')
        for step in row['steps']:
            if 'state' in step and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):
                raise RuntimeError('final saved state came from another execution')
        observed=dict(spec=name,attempt=result['id'],invocation_id=row['invocation_id'],report_sha256=sha256(report))
        immutable_json(folder/(name+'.observed.json'),observed)
        records.append(observed)
        print('Final fff',host,args.batch,name,'passed',flush=True)
    immutable_json(folder/'complete.json',dict(observed=20,records=records,
        scope='One observed batch; no project/cell final credit until independent complete-series audit.'))


if __name__=='__main__':
    asyncio.run(main())
