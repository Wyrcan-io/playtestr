"""Three declared native batches; preserve every historical wizard attempt."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


class InvestigationAttempt(Campaign):
    def append(self,row):
        if row['event']=='started':self.attempt_id=row['id']
        super().append(row)


async def main():
    if os.name!='nt':raise RuntimeError('this incident requires native Windows')
    parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path);parser.add_argument('--target',type=Path)
    args=parser.parse_args()
    root=RAW/'historical-wizard'/uuid.uuid4().hex;root.mkdir(parents=True)
    runner=(args.binary or RAW/'bin/playtestr.exe').resolve(strict=True)
    target=(args.target or RAW/'bin/fixture.exe').resolve(strict=True)
    for binary in [runner,target]:
        binary.relative_to(ROOT)
        if not binary.is_file() or binary.stat().st_size>64*1024**2:raise ValueError('owned binary identity bound')
    original=ROOT/'examples/recorded/wizard.json'
    base=json.loads(original.read_text())
    shutil.copytree(original.parent/'fixtures/wizard',root/'fixture')
    shutil.copytree(original.parent/'snapshots',root/'snapshots')
    base['command']=[str(target),'wizard'];base['workspace']['fixture']='fixture'
    # Retain the historical reduced investigation budget rather than padding it.
    base['timeout_ms']=1000;base['run_timeout_ms']=5000
    schedule=[dict(batch='ordinary',trace=False,load=False),dict(batch='instrumented',trace=True,load=False),
              dict(batch='instrumented-contention',trace=True,load=True)]
    immutable_json(root/'declared-schedule.json',dict(batches=schedule,repetitions_each=50,
        delays_ms=[0,25,100,5,60,150,10,80,40,120],runner_sha256=sha256(runner),fixture_binary_sha256=sha256(target),
        historical_contract_sha256=sha256(original),cause_claim='No causal diagnosis of unlogged historical failure from later green repetitions'))
    failures=[];all_attempts=[]
    for batch in schedule:
        spec=json.loads(json.dumps(base))
        if batch['trace']:spec['inherit_env'].append('PLAYTESTR_WIZARD_TRACE')
        path=root/(batch['batch']+'.json');path.write_text(json.dumps(spec,indent=2)+'\n')
        for index in range(50):
            report=root/(batch['batch']+'-'+str(index)+'.json')
            env=dict(os.environ,PLAYTESTR_DELAY_MS=str([0,25,100,5,60,150,10,80,40,120][index%10]))
            if batch['trace']:env['PLAYTESTR_WIZARD_TRACE']=str(report.with_suffix('.trace'))
            row=dict(batch=batch['batch'],index=index)
            campaign=InvestigationAttempt()
            try:
                result=await execute([runner,'test','--report',report.relative_to(ROOT),
                    '--artifacts-dir',report.with_suffix('').relative_to(ROOT),path.relative_to(ROOT)],
                    'historical-wizard',batch['batch']+'-'+str(index),env=env,timeout=20,
                    load=batch['load'],campaign=campaign)
                row.update(id=result['id'],passed=True)
            except RuntimeError:
                if not report.exists():raise
                outcome=json.loads(report.read_text())['results'][0]
                if (not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned'] or
                    outcome['failure']['category'] in {'invalid_spec','launch_failure','workspace_setup_failure'}):
                    raise RuntimeError('stop investigation after setup or unconfirmed cleanup')
                row.update(id=campaign.attempt_id,passed=False,report=report.relative_to(ROOT).as_posix())
                failures.append(row)
            if batch['trace'] and report.with_suffix('.trace').exists() and report.with_suffix('.trace').stat().st_size>512*1024:
                raise RuntimeError('owned diagnostic trace bound exceeded')
            all_attempts.append(row)
            if index%10==9:print(batch['batch'],index+1,'completed; retained failures',len(failures),flush=True)
        immutable_json(root/(batch['batch']+'-outcomes.json'),dict(attempts=all_attempts[-50:]))
    immutable_json(root/'summary.json',dict(attempts=all_attempts,failures=failures,
        qualification='Reduced native Windows historical sequence only; not a general zero-flakiness or original-cause claim'))
    if failures:raise RuntimeError('historical investigation retained failures; inspect before qualification')
    print('Three native fifty-attempt wizard batches completed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
