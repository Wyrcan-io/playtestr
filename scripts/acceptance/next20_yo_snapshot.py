"""Author a second ordinary yo route and reviewed screen through public controls."""
import asyncio
import base64
import hashlib
import json

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    package=DOC/'yo';raw=RAW/'yo';target=RAW/'active/yo';spec=package/'normal-javascript.json'
    if spec.exists() or (package/'snapshot-authoring.json').exists():raise ValueError('Preserve existing technical authoring outcome')
    first=json.loads((package/'normal-project.json').read_text(encoding='utf-8'))
    planned=json.loads((raw/'first-use-planned.json').read_text(encoding='utf-8'))
    if sha256(package/'fixture/generator/index.js')!=planned['plugin_fixture_sha256']:raise ValueError('Original real generator fixture changed')
    catalog=json.loads((target/'launch-runtime-catalog.json').read_text(encoding='utf-8'))
    for name,digest in catalog['files'].items():
        if sha256(ROOT/catalog['runtime_root']/name)!=digest:raise ValueError('Reviewed runtime dependency changed')
    controls=['/expect Project label','/text "Synthetic JavaScript"','/key Enter','/expect Project language',
        '/key ArrowDown','/key Enter','/expect Include README','/text "n"','/key Enter','/expect Scaffold complete',
        '/exit 0','/file output/project.json','/missing output/README.md','/file sentinel.txt','/entries output',
        '/snapshot javascript-complete.txt','/review','/replay','/save']
    expected=(json.dumps(dict(label='Synthetic JavaScript',language='JavaScript'),indent=2)+'\n').encode()
    immutable_json(raw/'snapshot-authoring-planned.json',dict(schema_version=1,controls=controls,
        expected_message_base64=base64.b64encode(expected).decode(),source_spec_sha256=sha256(package/'normal-project.json'),
        target_command=first['command'],handwritten_playtestr_json=False,scope='Separate technical public route; no first-use or native/admission credit.'))
    runner=RAW/'candidate/windows/playtestr.exe';env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(command,label,input=None):
        result=await execute(command,'yo',label,cwd=ROOT,env=env,input=input,timeout=180,campaign=campaign)
        attempts.append(result['id']);return result
    await run([runner,'--version'],'technical-snapshot-runner-version')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in first['env'].items():argv+=['--env',name+'='+value]
    for name in first['inherit_env']:argv+=['--inherit-env',name]
    await run([*argv,'--',*first['command']],'technical-public-record-javascript',input='\n'.join(controls+['']))
    approved=json.loads(spec.read_text(encoding='utf-8'))
    actual=next(s['state'] for s in approved['steps'] if s.get('state',{}).get('path')=='output/project.json')
    if base64.b64decode(actual['bytes_base64'])!=expected:raise ValueError('Technical recorder approved unintended file bytes')
    report=raw/'snapshot-ordinary-report.json'
    await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(raw/'snapshot-evidence').relative_to(ROOT),spec.relative_to(ROOT)],'technical-snapshot-ordinary-replay')
    row=json.loads(report.read_text(encoding='utf-8'))['results'][0]
    if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:
        raise ValueError('Technical route lacks positive snapshot/file/cleanup evidence')
    immutable_json(package/'snapshot-authoring.json',dict(schema_version=1,attempts=attempts,shell_invocations=3,recorder_controls=len(controls),
        spec_sha256=sha256(spec),report_sha256=sha256(report),snapshot_sha256=sha256(package/'snapshots/javascript-complete.txt'),
        independent_expected_file_sha256=hashlib.sha256(expected).hexdigest(),handwritten_playtestr_json=False,
        human_time='unmeasured',first_use_credit=0,new_project_admissions=0))
    print('Separate public yo JavaScript/snapshot route passed:3 commands,',len(controls),'controls; native support still unverified.')


if __name__=='__main__':asyncio.run(main())
