"""Explicit target preparation/restoration for the generated jrnl CI journey."""
import argparse
import asyncio
import json
import os
import shutil
import sys

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign, owned_environment
from next20_jrnl_native_prepare import main as prepare
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','cleanup'])
    args=parser.parse_args()
    mode=os.environ.get('JRNLCI_MODE');route=os.environ.get('JRNLCI_ROUTE')
    if mode not in {'baseline','fault','recovered'} or route not in {'source','private-archive'}:
        raise ValueError('Explicit declared delivered-CI mode/route required')
    target=RAW/'active/jrnl';evidence=RAW/'jrnl/delivered-ci';evidence.mkdir(parents=True,exist_ok=True)
    fault=json.loads((DOC/'jrnl/fault-declaration.json').read_text())['faults'][2]
    source=target/'src'/fault['path'];campaign=NextCampaign()
    async def run(argv,label,timeout=180):
        return await execute(argv,'jrnl',label,cwd=ROOT,env=owned_environment(),timeout=timeout,campaign=campaign)
    if args.stage=='prepare':
        await prepare()
        original=source.read_bytes()
        if original.count(fault['before'].encode())!=1:raise ValueError('CI source mutation anchor mismatch')
        if mode=='fault':source.write_bytes(original.replace(fault['before'].encode(),fault['after'].encode()))
        runner=os.environ['PLAYTESTR_BIN']
        if route=='private-archive':
            host='windows' if os.name=='nt' else 'linux';target_id=host+'-amd64'
            extension='zip' if os.name=='nt' else 'tar.gz'
            folder=RAW/'candidate-download'
            await run(['gh','run','download','39450029736','--name',
                'private-candidate-'+('Windows' if os.name=='nt' else 'Linux'),'--dir',folder],
                'delivered-explicit-private-archive-retrieval')
            archive=folder/'candidate-packages/migration-v2'/target_id/'dist'/('playtestr_0.4.0-rc.5_'+host+'_amd64.'+extension)
            await run([sys.executable,'-B',ROOT/'scripts/acceptance/next20_candidate_install.py',
                '--archive',archive.relative_to(ROOT)],'delivered-explicit-private-archive-install')
            runner=str(RAW/'candidate'/host/('playtestr.exe' if os.name=='nt' else 'playtestr'))
            with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as stream:stream.write('PLAYTESTR_BIN='+runner+'\n')
        immutable_json(evidence/'prepared.json',dict(schema_version=1,mode=mode,route=route,
            ci_run_id=os.environ['GITHUB_RUN_ID'],source_original_sha256=__import__('hashlib').sha256(original).hexdigest(),
            source_executed_sha256=sha256(source),runner_sha256=sha256(runner),
            source_files={p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()},
            runtime_sha256=sha256(target/'runtime.json'),installed_inventory_sha256=sha256(target/'installed-inventory.json'),
            spec_sha256=sha256(RAW/'jrnl/host-contracts/normal-delete.json'),new_project_credit=0))
    else:
        record=json.loads((evidence/'prepared.json').read_text())
        if sha256(source)!=record['source_executed_sha256']:raise ValueError('Executed CI source changed before restoration')
        original=source.read_bytes()
        if mode=='fault':
            if original.count(fault['after'].encode())!=1:raise ValueError('CI restoration anchor mismatch')
            source.write_bytes(original.replace(fault['after'].encode(),fault['before'].encode()))
        if sha256(source)!=record['source_original_sha256']:raise ValueError('CI exact original restoration failed')
        report=ROOT/'artifacts/playtestr/results.json';data=json.loads(report.read_text(encoding='utf-8'))
        if len(data['results'])!=1:raise ValueError('Wrong generated suite selection')
        row=data['results'][0]
        if mode=='fault':
            if row['status']!='failed' or row['failure']['category']!='state_assertion_failure':raise ValueError('Real saved corruption not rejected by delivered route')
            index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
            if not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('CI source fault failed before saved-state checkpoint')
        elif row['status']!='passed':raise ValueError('Generated baseline/recovery did not pass')
        shutil.copyfile(report,evidence/'results.json')
        if os.name=='nt':
            await run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                ROOT/'scripts/acceptance/next20_target_process_proof.ps1','-Project','jrnl'],'delivered-native-process-proof',120)
        argv=[sys.executable,'-B',ROOT/'scripts/acceptance/next20_target_cleanup.py','--project','jrnl']
        if os.name=='nt':argv+=['--prepare-only']
        await run(argv,'delivered-retain-restored-source',240)
        if os.name=='nt':
            await run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                ROOT/'scripts/acceptance/next20_remove_target.ps1','-Project','jrnl'],'delivered-checked-source-removal',240)
        immutable_json(evidence/'restored.json',dict(schema_version=1,source_restored_exact=True,
            source_sha256=record['source_original_sha256'],target_absent=not target.exists(),
            report_sha256=sha256(report),mode=mode,route=route))


if __name__=='__main__':asyncio.run(main())
