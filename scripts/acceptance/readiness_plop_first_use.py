"""Documentation-only public first-use route after task-owned Plop installation."""
import asyncio
import json
import os

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    campaign=Campaign()
    suffix='.exe' if os.name=='nt' else ''
    runner=RAW/'bin'/('playtestr'+suffix)
    env=dict(os.environ)
    env['PATH']=str(RAW/'active/plop/bin')+os.pathsep+env['PATH']
    env['PYTHONIOENCODING']='utf-8'
    for name,folder in [('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),('GOCACHE','go-cache')]:
        path=RAW/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    async def run(argv,label,input=None):
        return await execute(argv,'plop',label,cwd=ROOT,env=env,input=input,timeout=120,campaign=campaign)
    await run(['go','build','-o',runner,'./cmd/playtestr'],'build-first-use-runner')
    version=await run([runner,'--version'],'first-use-check-version')
    package=ROOT/'docs/validation/runner-readiness-ten-project-pass/plop'
    spec=package/'normal-artifact.json'
    if spec.exists():raise RuntimeError('preserve existing first attempt; do not overwrite it')
    target=['cmd.exe','/d','/s','/c','plop --no-progress'] if os.name=='nt' else ['plop','--no-progress']
    commands='\n'.join(['/expect Artifact name','/text "alpha"','/key Enter','/expect alpha.txt',
                        '/exit 0','/snapshot normal-artifact.txt','/file out/alpha.txt',
                        '/entries out','/review','/replay','/save',''])
    capture=await run([runner,'record','--output',spec.relative_to(ROOT).as_posix(),
                       '--fixture','fixture','--temporary-home','--temporary-temp',
                       '--timeout-ms','10000','--run-timeout-ms','120000','--',*target],
                      'first-documentation-record-review-replay-export',commands)
    reviewed=json.loads(spec.read_text(encoding='utf-8'))
    file_step=next(step['state'] for step in reviewed['steps'] if step.get('state',{}).get('kind')=='file')
    # The independent expected bytes come from the reviewed template, not the
    # production output function or a second execution's filesystem state.
    assert file_step['bytes_base64']=='bmFtZT1hbHBoYQo='
    report=RAW/'plop'/'first-ordinary-report.json'
    ordinary=await run([runner,'test','--report',report.relative_to(ROOT).as_posix(),
                        spec.relative_to(ROOT).as_posix()],'first-reviewed-ordinary-test')
    data=json.loads(report.read_text(encoding='utf-8'))
    result=data['results'][0]
    assert result['status']=='passed' and result['workspace']['cleaned'] and result['cleanup']['confirmed_exited']
    route_labels={'first-use-check-version':0,'first-documentation-record-review-replay-export':11,
                  'first-reviewed-ordinary-test':0,'startup-probe-shell-launcher':3,'startup-probe-node-direct':3}
    history=[]
    for path in (RAW/'events').glob('*-started.json'):
        event=json.loads(path.read_text(encoding='utf-8'))
        if event['project']=='plop' and event['label'] in route_labels:history.append(event)
    total_controls=sum(route_labels[event['label']] for event in history)
    immutable_json(package/'first-use.json',dict(schema_version=1,status='development-route-passed-not-admitted',
        repaired_route_shell_invocations=3,repaired_route_recorder_controls=11,
        all_invocations_to_first_test=len(history),all_recorder_controls=total_controls,
        route_attempts=[event['id'] for event in history],
        original_false_green='first exported input-only test rejected by independent calibration; preserved',
        initial_engineering_count_targets_met=len(history)<=5 and total_controls<=20,
        handwritten_playtestr_json=False,
        source_setup='synthetic documented plopfile; pinned Yarn install with scripts disabled',
        runner_sha256=sha256(runner),spec_sha256=sha256(spec),target_build_sha256=sha256(RAW/'active/plop/build.json'),
        version_attempt=version['id'],capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],
        command_elapsed_seconds=capture['seconds'],human_authoring_time='unmeasured',
        confounders=['prepared synthetic target configuration','prior operator familiarity','warm runner/build caches'],
        report_sha256=sha256(report),remaining=['twenty scenarios','faults/restorations','native cells','final archive series','maintenance','relocation','free workflow']))
    print('Plop repaired prepared route passed: 3 invocations, 11 controls. All-route totals:',len(history),total_controls,'No project admission.')


if __name__=='__main__':asyncio.run(main())
