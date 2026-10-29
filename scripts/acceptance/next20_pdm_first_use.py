"""First public PDM recorder route, checked against independent complete metadata."""
import asyncio
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import tomllib

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from next20_python_runtime import python_runtime_root
from readiness_evidence import immutable_json,sha256


async def main(generation):
    project='pdm';target=RAW/'active/pdm';package=DOC/project;raw=RAW/project/('first-use-v'+str(generation))
    spec=package/('normal-minimal.json' if generation==1 else 'normal-minimal-runtime-v2.json')
    snapshot_name='normal-minimal.txt' if generation==1 else 'normal-minimal-runtime-v2.txt'
    if raw.exists() or spec.exists():raise ValueError('preserve every original first-use attempt')
    runtime=json.loads((target/'runtime.json').read_text());python=Path(runtime['python']);runner=executable('native-exit-v1')
    if sha256(python)!=runtime['python_sha256']:raise ValueError('actual reviewed interpreter changed')
    inventory=json.loads((target/'installed-inventory.json').read_text())['files']
    selected_runtime=python_runtime_root(target,runtime)
    for name,digest in inventory.items():
        if sha256(selected_runtime/name)!=digest:raise ValueError('installed dependency changed')
    raw.mkdir(parents=True);fixture=package/'fixture'
    if generation==1:
        fixture.mkdir();(fixture/'.git/objects').mkdir(parents=True);(fixture/'.git/refs/heads').mkdir(parents=True)
    sentinel=b'unrelated synthetic data\n'
    git_config=b'[core]\n\trepositoryformatversion = 0\n\tbare = false\n[user]\n\tname = Synthetic User\n\temail = synthetic@example.invalid\n'
    for name,payload in [('sentinel.txt',sentinel),('.git/config',git_config),('.git/HEAD',b'ref: refs/heads/synthetic\n')]:
        if generation==1:(fixture/name).write_bytes(payload)
        elif (fixture/name).read_bytes()!=payload:raise ValueError('existing reviewed fixture changed before runtime repeat')
    expected_metadata=dict(project=dict(name='synthetic-notes',version='0.1.0',description='Default template for PDM package',
        authors=[dict(name='Ada',email='ada@example.invalid')],dependencies=[],**{'requires-python':'>=3.10'},readme='README.md',license='MIT'),tool=dict(pdm=dict(distribution=False)))
    controls=['/expect Project version','/key Enter','/key Enter','/key Enter','/text "Ada"','/key Enter',
        '/text "ada@example.invalid"','/key Enter','/text ">=3.10"','/key Enter','/expect Project is initialized successfully',
        '/exit 0','/snapshot '+snapshot_name,'/file pyproject.toml','/file sentinel.txt','/file .git/config','/entries .','/review','/replay','/save']
    values=dict(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PDM_CHECK_UPDATE='false',PDM_USE_VENV='false',
        PDM_IGNORE_ACTIVE_VENV='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='user.name',GIT_CONFIG_VALUE_0='Synthetic User',
        GIT_CONFIG_KEY_1='user.email',GIT_CONFIG_VALUE_1='synthetic@example.invalid')
    immutable_json(raw/'planned.json',dict(schema_version=1,controls=controls,recorder_controls=len(controls),expected_metadata=expected_metadata,
        candidate_sha256=sha256(runner),actual_python_sha256=sha256(python),actual_runtime_sha256=sha256(target/'runtime.json'),
        initial_attempt=generation==1,runtime_generation=generation,handwritten_playtestr_json=False,human_time='unmeasured',
        scope='Prepared agent public route. All metadata values independently declared before target launch; captured exact native bytes must decode to this complete TOML value. Explicit existing interpreter, builtin minimal template,no Git/hook/install/network workflow.'))
    env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=150,campaign=campaign);attempts.append(result['id']);return result
    version=await run([runner,'--version'],'pdm-first-use-runner-version')
    if version['output'].strip()!='playtestr v0.4.0-rc.6':raise ValueError('wrong current candidate version')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','120','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in values.items():argv+=['--env',name+'='+value]
    argv+=['--',os.path.relpath(python,package).replace('\\','/'),'-B','-m','pdm','init','--name','synthetic-notes','--python',str(python),'--no-git','--skip',':all','minimal']
    await run(argv,'pdm-first-public-record-review-replay-export','\n'.join(controls+['']))
    approved=json.loads(spec.read_text());states={s['state']['path']:s['state'] for s in approved['steps'] if 'state' in s}
    payload=base64.b64decode(states['pyproject.toml']['bytes_base64'],validate=True)
    if tomllib.loads(payload.decode('utf-8'))!=expected_metadata:raise ValueError('captured TOML differs from independently declared complete expected metadata')
    if base64.b64decode(states['sentinel.txt']['bytes_base64'])!=sentinel or base64.b64decode(states['.git/config']['bytes_base64'])!=git_config:raise ValueError('unrelated approved fixture changed')
    if states['.']['kind']!='entries' or set(states['.']['entries'])!={'.git','.gitignore','.pdm-python','pyproject.toml','sentinel.txt'}:raise ValueError('generated files differ from independently expected builtin workflow')
    report=raw/'ordinary-report.json';await run([runner,'test','--report',report,spec],'pdm-first-reviewed-ordinary-test')
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or not all(s['status']=='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('public ordinary replay not positive or clean')
    destination=package/('first-use.json' if generation==1 else 'first-use-runtime-v2.json')
    immutable_json(destination,dict(schema_version=1,status='prepared-public-agent-route-passed-not-admitted',candidate='v0.4.0-rc.6',
        attempts=attempts,shell_invocations=3,recorder_controls=len(controls),handwritten_playtestr_json=False,
        runner_sha256=sha256(runner),actual_python_sha256=sha256(python),spec_sha256=sha256(spec),ordinary_report_sha256=sha256(report),
        independently_expected_metadata=expected_metadata,approved_native_file_sha256=hashlib.sha256(payload).hexdigest(),
        first_attempt=generation==1,runtime_generation=generation,**(dict(original_first_use_sha256=sha256(package/'first-use.json')) if generation==2 else {}),
        human_time='unmeasured',human_participants=0,confounders=['Prepared synthetic fixture','Agent read upstream init/template code','Existing interpreter explicitly supplied; no interpreter-discovery coverage'],
        scope='First prepared agent route only. Complete TOML values independently declared before launch and checked against captured exact native bytes. No beginner study or project/native qualification claim.'))
    print('PDM public recorder/replay/export/ordinary route passed:3shell invocations,20controls; independent complete TOML/sentinel/Git/entries checks')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,choices=[1,2],default=1);args=parser.parse_args();asyncio.run(main(args.generation))
