"""Preserve the rejected Windows window and predeclare one finite startup probe."""
import asyncio
import json
import os
from pathlib import Path
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    package=DOC/'pdm';target=RAW/'active/pdm';original=RAW/'pdm/final-series-native-exit-v1'
    reports=sorted(original.glob('*/*.report.json'));observations=[]
    for path in reports:
        row=json.loads(path.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('original Windows cleanup incomplete')
        observations.append(dict(report=path.relative_to(RAW).as_posix(),sha256=sha256(path),status=row['status'],
            category=row.get('failure',{}).get('category'),invocation=row['invocation_id']))
    if len(observations)!=227 or sum(r['status']=='passed' for r in observations)!=226 or [(r['report'],r['category']) for r in observations if r['status']!='passed']!=[('pdm/final-series-native-exit-v1/11/N07.report.json','assertion_timeout')]:
        raise ValueError('original Windows window differs')
    failed=json.loads((original/'11/N07.report.json').read_text())['results'][0]
    spec=json.loads((original/'11/contracts/n07.json').read_text())
    if spec['startup_timeout_ms']!=2000 or any(s['status']!='not_run' for s in failed['steps']) or 'waiting for first output' not in failed['failure']['message']:
        raise ValueError('original failure was not the declared first-output budget')
    screen=ROOT/failed['evidence']['screen_path']
    if not screen.is_file():raise ValueError('original startup screen missing')
    ended=json.loads((RAW/'events/76fcc374f4674c2b9774aa75f15b3f06-finished.json').read_text())
    if ended['exit_code']!=1 or ended['cleanup_errors'] or ended['harness_cleanup']!='harness_process_reaped':raise ValueError('failed series harness not reaped')
    immutable_json(package/'windows-first-final-rejection.json',dict(schema_version=1,ordinary_attempted=227,ordinary_passed=226,ordinary_failed=1,
        completed_batches=11,partial_batch=11,failed_case='N07',failed_attempt='e98dc38d5df4423a9b17c17bd7ce471f',
        report_sha256=sha256(original/'11/N07.report.json'),screen_sha256=sha256(screen),observations=observations,
        wrapper='76fcc374f4674c2b9774aa75f15b3f06',wrapper_elapsed_seconds=ended['seconds'],
        final_qualification_credit=0,fresh_final_calibrations=0,all_reported_target_workspace_cleanup=True,
        disposition='The optional two-second startup boundary did not receive first output. Runner rejected it with confirmed forced job-tree and workspace cleanup. Cause of delay unknown; no target-readiness-after-two-seconds or runner-repair claim. Preserve the whole rejected window; no per-case retry can complete it.'))
    root=RAW/'pdm/startup-probe-v1';root.mkdir(exist_ok=False)
    fixture=RAW/'pdm/host-contracts/fixtures/n07';shutil.copytree(fixture,root/'fixture')
    selected=json.loads((RAW/'pdm/host-contracts/n07.json').read_text());runtime=json.loads((target/'runtime.json').read_text())
    selected['workspace']['fixture']='fixture';selected['command'][0]=os.path.relpath(runtime['python'],root).replace('\\','/')
    selected['startup_timeout_ms']=5000;immutable_json(root/'spec.json',selected)
    immutable_json(root/'planned.json',dict(schema_version=1,classification='R3-startup-budget-experiment',phase='development',
        hypothesis='A five-second explicit target startup contract supplies headroom beyond the observed two-second first-output refusal. Underlying startup delay cause remains unknown.',
        original_rejection_sha256=sha256(package/'windows-first-final-rejection.json'),spec_sha256=sha256(root/'spec.json'),
        maximum_batches=1,executions=50,harness_command_ceiling_seconds=600,load='ordinary; no artificial worker',
        startup_timeout_ms=5000,scenario_timeout_ms=selected['run_timeout_ms'],
        scope='Exact existing N07 steps and saved-state oracles; only owned fixture/interpreter routing and the explicit startup limit differ. No product deadline/default change, retries, final/scenario/fault/admission credit or claimed causal diagnosis.'))
    env=environment(target);campaign=NextCampaign();runner=executable('native-exit-v1');rows=[]
    for number in range(50):
        report=root/(str(number)+'.report.json')
        try:
            result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),
                (root/'spec.json').relative_to(ROOT)],'pdm','r3-startup-five-second-'+str(number),cwd=ROOT,env=env,timeout=140,campaign=campaign)
            eid=result['id']
        except RuntimeError as error:
            eid=getattr(error,'evidence_id',None)
            if not eid or not report.is_file():raise
        row=json.loads(report.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('startup probe cleanup unconfirmed')
        rows.append(dict(number=number,attempt=eid,status=row['status'],category=row.get('failure',{}).get('category'),
            report_sha256=sha256(report),duration_ms=row['duration_ms'],invocation=row['invocation_id']))
        if number%10==9:print('Startup budget probe',number+1,'/50 completed',flush=True)
    immutable_json(root/'summary.json',dict(schema_version=1,planned_sha256=sha256(root/'planned.json'),observations=rows,
        passed=sum(r['status']=='passed' for r in rows),failed=sum(r['status']!='passed' for r in rows),
        final_qualification_credit=0,project_admissions=0,scope='One finite50-execution diagnostic; does not repair or replace the failed final window.'))
    if any(r['status']!='passed' for r in rows):raise ValueError('five-second startup probe has failures; inspect before replacement declaration')
    print('All50 bounded five-second startup probes passed; original227-report final window remains rejected and unchanged.')


if __name__=='__main__':asyncio.run(main())
