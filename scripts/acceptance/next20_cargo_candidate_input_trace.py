"""Trace actual private-archive PTY traffic; diagnostic repetitions earn no credit."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment
from next20_candidate import executable
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',type=Path,required=True);args=parser.parse_args()
    campaign=NextCampaign(phase='development')
    async def command(argv,label,timeout=90):return await execute(argv,'cargo-generate',label,cwd=ROOT,env=owned_environment(),timeout=timeout,campaign=campaign)
    await command([sys.executable,'-B',ROOT/'scripts/acceptance/next20_cargo_input_diagnostic.py','--packet',args.packet,'--prepare-only'],'native-candidate-input-trace-prepare')
    await command([sys.executable,'-B',ROOT/'scripts/acceptance/next20_cargo_host_contracts.py'],'native-candidate-input-trace-frozen-profile')
    tracer=shutil.which('strace')
    if not tracer:raise ValueError('read-only strace prerequisite missing; no global installation allowed')
    tracer=Path(tracer).resolve(strict=True);runner=executable('native-exit-v1');target=RAW/'active/cargo-generate';binary=target/'bin/cargo-generate'
    root=RAW/'cargo-generate/candidate-input-trace/v1';root.mkdir(parents=True,exist_ok=False)
    immutable_json(root/'tool-and-runtime.json',dict(schema_version=1,tracer=str(tracer),tracer_sha256=sha256(tracer),
        actual_runner_sha256=sha256(runner),actual_target_sha256=sha256(binary),maximum_executions=20,maximum_trace_bytes=8*1024**2,
        scope='Actual exact private archive, unchanged native N01 and source-built target. Diagnostic observations only; stop after first failure, no final-series credit.'))
    observations=[]
    for number in range(20):
        folder=root/str(number);folder.mkdir();report=folder/'report.json';spec=RAW/'cargo-generate/host-contracts/normal-project.json'
        immutable_json(folder/'planned.json',dict(schema_version=1,number=number,runner_sha256=sha256(runner),target_sha256=sha256(binary),
            spec_sha256=sha256(spec),tracer_sha256=sha256(tracer),timeout_seconds=15,qualification_credit=0))
        argv=[tracer,'-ff','-ttt','-yy','-s','2048','-e','trace=read,write,ioctl','-o',folder/'syscalls',runner,'test',
            '--report',report.relative_to(ROOT),'--artifacts-dir',(folder/'evidence').relative_to(ROOT),spec.relative_to(ROOT)]
        task=asyncio.create_task(execute(argv,'cargo-generate','native-candidate-pty-syscall-trace-'+str(number),cwd=ROOT,env=environment(target),timeout=15,campaign=campaign))
        try:
            while not task.done():
                files=list(root.glob('*/syscalls.*'))
                if len(files)>640 or sum(p.stat().st_size for p in files)>8*1024**2:raise ValueError('aggregate diagnostic trace output bound')
                await asyncio.sleep(.05)
            try:
                outcome=await task;attempt=outcome['id']
            except RuntimeError as error:
                directory=getattr(error,'evidence_directory',None)
                if not report.is_file() or directory is None:raise
                attempt=Path(directory).name
            finish=json.loads((RAW/'events'/(attempt+'-finished.json')).read_text())
            if finish['exit_code'] not in {0,1} or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':raise ValueError('incomplete actual traced-command exit/cleanup')
        finally:
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
        data=json.loads(report.read_text());row=data['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('candidate diagnostic target/workspace cleanup incomplete')
        traces={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in folder.glob('syscalls.*')}
        if not traces or len(traces)>32 or sum(p.stat().st_size for p in root.glob('*/syscalls.*'))>8*1024**2:raise ValueError('missing/excess actual trace streams')
        observations.append(dict(number=number,attempt=attempt,status=row['status'],category=row.get('failure',{}).get('category'),
            report_sha256=sha256(report),traces=traces,invocation=row['invocation_id']))
        immutable_json(folder/'observed.json',observations[-1]);print(number,row['status'],row.get('failure',{}).get('category'),flush=True)
        if row['status']=='failed':break
    immutable_json(root/'summary.json',dict(schema_version=1,observations=observations,executions=len(observations),
        qualification_credit=0,scope='Actual exact-candidate syscall diagnostic, stopped at first failed observation or20 bounded runs. Does not replace the rejected final window.'))
    inventory={};total=0
    for path in target.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked diagnostic target payload')
        if path.is_file():
            total+=path.stat().st_size
            if len(inventory)>=1000 or total>80*1024**2:raise ValueError('diagnostic cleanup inventory bound')
            inventory[path.relative_to(target).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    immutable_json(root/'cleanup-inventory.json',dict(schema_version=1,owned_target=str(target),files=inventory,bytes=total))
    for name,row in inventory.items():
        if sha256(target/name)!=row['sha256']:raise ValueError('diagnostic target changed before removal')
    if json.loads((target/'task-owned.json').read_text())['workspace']!=str(ROOT):raise ValueError('foreign diagnostic source/runtime owner')
    shutil.rmtree(target)
    if target.exists():raise ValueError('diagnostic target source/runtime remains')
    immutable_json(root/'cleanup-removed.json',dict(schema_version=1,target_payload_removed=True,
        inventory_sha256=sha256(root/'cleanup-inventory.json'),all_actual_target_workspace_cleanups_confirmed=True,qualification_credit=0))
    print('Exact-candidate trace completed and target payload removed; zero final-series credit')


if __name__=='__main__':asyncio.run(main())
