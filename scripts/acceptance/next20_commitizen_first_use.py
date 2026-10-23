"""First public no-JSON authoring window for real Commitizen initialization."""
import asyncio
import argparse
import base64
import hashlib
import json
import os

from adversarial_process import execute
from next20_check import RAW, DOC, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repair-portability',action='store_true')
    parser.add_argument('--snapshot-plain-toml',action='store_true');args=parser.parse_args()
    package=DOC/'commitizen-python';target=RAW/'active/commitizen-python'
    runner=RAW/'candidate/windows/playtestr.exe'
    spec=package/('normal-init-portable.json' if args.repair_portability else 'normal-init.json')
    receipt=package/('first-use-portable.json' if args.repair_portability else 'first-use.json')
    if args.snapshot_plain_toml:
        spec=package/'normal-plain-toml.json';receipt=package/'snapshot-authoring.json'
    if os.name!='nt' or spec.exists() or receipt.exists():
        raise ValueError('first Windows authoring window already used or wrong host; preserve it')
    runtime=json.loads((target/'runtime.json').read_text());python=runtime['python']
    env=environment(target);attempts=[];campaign=NextCampaign()
    async def run(argv,label,input=None):
        if args.repair_portability:label='portability-repair-'+label
        if args.snapshot_plain_toml:label='technical-snapshot-'+label
        value=await execute(argv,'commitizen-python',label,cwd=ROOT,env=env,input=input,timeout=180,campaign=campaign)
        attempts.append(value['id']);return value
    await run([runner,'--version'],'first-use-runner-version')
    prompts=['Please choose a supported config file:', 'Please choose a cz (commit rule):',
        'Choose the source of the version:', 'Choose version scheme:',
        'Please enter the correct version format:', 'Create changelog automatically on bump',
        'Keep major version zero (0.x) during breaking changes']
    controls=[item for prompt in prompts for item in ['/expect '+prompt,'/key Enter']]
    if args.snapshot_plain_toml:controls.insert(1,'/key ArrowDown')
    controls+=['/expect Configuration complete','/exit 0','/file .cz.toml','/review','/replay','/save']
    if args.snapshot_plain_toml:
        controls[controls.index('/file .cz.toml')]='/file cz.toml'
        controls.insert(controls.index('/file cz.toml'),'/snapshot init-plain-complete.txt')
    path=os.pathsep.join([r'C:\Program Files\Git\cmd',os.path.join(os.environ['SYSTEMROOT'],'System32')])
    declared_env=dict(PATH=path,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',TZ='UTC')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
        '--temporary-temp','--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in declared_env.items():argv+=['--env',name+'='+value]
    for name in ['SYSTEMROOT','WINDIR']:argv+=['--inherit-env',name]
    argv+=['--',os.path.relpath(python,package).replace('\\','/'),'-B','-m','commitizen','init']
    await run(argv,'first-public-record-review-replay-export','\n'.join(controls+['']))
    captured=json.loads(spec.read_text())
    expected=(b'[tool.commitizen]\nname = "cz_conventional_commits"\ntag_format = "$version"\n'
        b'version_scheme = "semver2"\nversion = "0.0.1"\nupdate_changelog_on_bump = true\nmajor_version_zero = true\n')
    files=[s['state'] for s in captured['steps'] if s.get('state',{}).get('kind')=='file']
    if len(files)!=1 or files[0]['path']!=('cz.toml' if args.snapshot_plain_toml else '.cz.toml') or base64.b64decode(files[0]['bytes_base64'])!=expected:
        raise ValueError('Recorder captured a saved configuration different from independently derived approved defaults')
    report=RAW/'commitizen-python'/('portable-ordinary-report.json' if args.repair_portability else 'first-ordinary-report.json')
    if args.snapshot_plain_toml:report=RAW/'commitizen-python/snapshot-ordinary-report.json'
    await run([runner,'test','--report',report.relative_to(ROOT),spec.relative_to(ROOT)],'first-reviewed-ordinary-test')
    result=json.loads(report.read_text())['results'][0]
    if result['status']!='passed' or any(s['status']!='passed' for s in result['steps']) or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise ValueError('First ordinary run lacks positive steps/cleanup')
    immutable_json(receipt,dict(schema_version=1,status='prepared-agent-route-passed-not-admitted',
        attempts=attempts,shell_invocations=3,recorder_controls=len(controls),handwritten_playtestr_json=False,
        target_keystrokes_separate=True,runner_sha256=sha256(runner),spec_sha256=sha256(spec),
        report_sha256=sha256(report),independent_expected_file_sha256=hashlib.sha256(expected).hexdigest(),
        human_time='unmeasured',confounders=['Prepared empty Git boundary and synthetic file','Source-reviewed prompts/defaults; operator familiar with recorder'],
        repaired_portability_window=args.repair_portability,
        technical_snapshot_route=args.snapshot_plain_toml,
        scope='Original local route retained; this repaired window removes the unnecessary personal venv PATH. Not an unfamiliar first-use observation.' if args.repair_portability else 'All earlier failed first-window labels must also be reconciled; this receipt does not erase them.'))
    print('Public Commitizen route passed:',len(attempts),'invocations,',len(controls),'controls; technical snapshot',args.snapshot_plain_toml,'; exact approved configuration and cleanup. Not yet admitted.')


if __name__=='__main__':asyncio.run(main())
