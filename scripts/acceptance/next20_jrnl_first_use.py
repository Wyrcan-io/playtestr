"""First no-handwritten-JSON public jrnl route with independently reviewed bytes."""
import asyncio
import base64
import json
import os
from pathlib import Path

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/jrnl';package=DOC/'jrnl'
    runtime=json.loads((target/'runtime.json').read_text())
    python=Path(runtime['python'])
    inventory=json.loads((target/'installed-inventory.json').read_text())['files']
    for name,digest in inventory.items():
        if sha256(target/'venv'/name)!=digest:raise ValueError('installed dependency input changed: '+name)
    suffix='.exe' if os.name=='nt' else ''
    host='windows' if os.name=='nt' else 'linux'
    runner=RAW/'candidate'/host/('playtestr'+suffix)
    installed=json.loads((runner.parent/'installed.json').read_text())
    if sha256(runner)!=installed['binary_sha256']:raise ValueError('wrong archive executable')
    spec=package/'normal-delete.json'
    if spec.exists():raise ValueError('first route already exported; inspect it rather than overwrite')
    env=environment(target);campaign=NextCampaign()
    async def run(argv,label,input=None):
        return await execute(argv,'jrnl',label,cwd=ROOT,env=env,input=input,timeout=120,campaign=campaign)
    version=await run([runner,'--version'],'first-use-runner-version')
    # These are public recorder controls; no spec JSON is supplied before capture.
    controls=['/expect Delete entry','/text "y"','/key Enter','/expect 1 entry deleted',
        '/exit 0','/snapshot normal-delete.txt','/file journal.txt','/entries .',
        '/review','/replay','/save']
    relative_python=os.path.relpath(python,package).replace('\\','/')
    capture=await run([runner,'record','--output',spec.relative_to(ROOT).as_posix(),
        '--fixture','fixture','--temporary-home','--temporary-temp',
        '--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONIOENCODING=utf-8',
        '--env','PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring',
        '--timeout-ms','10000','--run-timeout-ms','120000','--',
        relative_python,'-B','-m','jrnl','--config-file','config.yaml','-contains','alpha','--delete'],
        'first-public-record-review-replay-export','\n'.join(controls+['']))
    approved=json.loads(spec.read_text(encoding='utf-8'))
    states=[s['state'] for s in approved['steps'] if 'state' in s]
    file=next(s for s in states if s['kind']=='file')
    expected=b'[2020-01-02 10:15] beta retained.\nSecond body.\n'
    if base64.b64decode(file['bytes_base64'])!=expected:
        raise ValueError('captured journal disagrees with independently reviewed intended deletion')
    if set(next(s for s in states if s['kind']=='entries')['entries'])!={'config.yaml','journal.txt'}:
        raise ValueError('unexpected first-run persistent file set')
    report=RAW/'jrnl/first-ordinary-report.json'
    ordinary=await run([runner,'test','--report',report,spec],'first-reviewed-ordinary-test')
    result=json.loads(report.read_text())['results'][0]
    if result['status']!='passed' or not result['workspace']['cleaned'] or not result['cleanup']['confirmed_exited']:
        raise ValueError('first ordinary positive/cleanup evidence incomplete')
    for name,digest in inventory.items():
        if sha256(target/'venv'/name)!=digest:raise ValueError('dependency changed during first route')
    immutable_json(package/'first-use.json',dict(schema_version=1,status='prepared-agent-route-passed-not-admitted',
        shell_invocations=3,recorder_controls=len(controls),target_keystrokes_separate=True,
        attempts=[version['id'],capture['id'],ordinary['id']],runner_sha256=sha256(runner),
        spec_sha256=sha256(spec),report_sha256=sha256(report),handwritten_playtestr_json=False,
        independent_expected_file_sha256=__import__('hashlib').sha256(expected).hexdigest(),
        target_setup_excluded='Pinned source/tree review; copied owned venv, wheel review and offline build',
        human_time='unmeasured',confounders=['Prepared synthetic configuration/seed','Operator familiar with recorder'],
        measured_window='All first-use labels in this project must be reconciled including any earlier failed calls; this receipt lists this completed route only.'))
    print('Prepared public route passed, 3 invocations /',len(controls),'controls; same-execution reviewed deletion and cleanup. No project admission.')


if __name__=='__main__':asyncio.run(main())
