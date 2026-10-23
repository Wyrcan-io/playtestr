"""Public no-spec-JSON first authoring route for the actual cz-cli hook mode."""
import asyncio
import argparse
import base64
import hashlib
import json
import os
import shutil

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_fixture_git import reconstruct
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fix-snapshot',action='store_true');args=parser.parse_args()
    project='cz-cli';target=RAW/'active'/project;package=DOC/project;raw=RAW/project
    spec=package/('normal-fix.json' if args.fix_snapshot else 'normal-message.json');receipt=package/('snapshot-authoring.json' if args.fix_snapshot else 'first-use.json')
    if os.name!='nt' or spec.exists() or receipt.exists():raise ValueError('Preserve the existing first authoring attempt or use the declared Windows host')
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'));node=runtime['node'];app=target/runtime['app_relative_path']
    catalog=json.loads((target/'launch-runtime-catalog.json').read_text(encoding='utf-8'))
    if sha256(node)!=runtime['node_sha256']:raise ValueError('Actual owned Node changed')
    for name,digest in catalog['files'].items():
        if sha256(app/name)!=digest:raise ValueError('Actual compiled/runtime file changed: '+name)
    boundary=json.loads((DOC/'commitizen-python/fixture-git.json').read_text(encoding='utf-8'))
    boundary['fixture_roots']=['fixture'];boundary['scope']='Empty owned synthetic Git repository; hook-mode message capture only, no commits/hooks/tags/network.'
    if (package/'fixture-git.json').exists():
        if json.loads((package/'fixture-git.json').read_text(encoding='utf-8'))!=boundary:raise ValueError('Existing fixture declaration changed')
    else:immutable_json(package/'fixture-git.json',boundary)
    reconstruct(package)
    (package/'fixture/.czrc').write_bytes(b'{"path":"cz-conventional-changelog"}\n')
    (package/'fixture/sentinel.txt').write_bytes(b'Unrelated synthetic file must remain unchanged.\n')
    runner=RAW/'candidate/windows/playtestr.exe';env=environment(target);attempts=[];campaign=NextCampaign()
    async def run(argv,label,input=None):
        if args.fix_snapshot:label='technical-snapshot-'+label
        value=await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=180,campaign=campaign)
        attempts.append(value['id']);return value
    controls=['/expect cz-cli@0.0.3','/expect Select the type of change', '/key Enter',
        '/expect What is the scope','/key Enter',
        '/expect Write a short, imperative tense description','/text "Add a synthetic entry."','/key Enter',
        '/expect Provide a longer description','/key Enter',
        '/expect Are there any breaking changes?','/key Enter',
        '/expect Does this change affect any open issues?','/key Enter',
        '/exit 0','/file .git/COMMIT_EDITMSG','/entries .git','/review','/replay','/save']
    if args.fix_snapshot:
        controls.insert(2,'/key ArrowDown');controls.insert(controls.index('/file .git/COMMIT_EDITMSG'),'/snapshot normal-fix.txt')
    # The standard entry file executes in the same Node process. Reconstruct its
    # normal argv while locating it relative to the owned interpreter, keeping
    # user/machine absolute paths out of the exported contract.
    launch="const p=require('path');const e=p.resolve(p.dirname(process.execPath),'../"+runtime['app_relative_path']+"/bin/git-cz');process.argv.splice(1,0,e);require(e);"
    command=[os.path.relpath(node,package).replace('\\','/'),'-e',launch,'--','--hook','--allow-empty']
    raw.mkdir(exist_ok=True)
    expected=(b'fix: ' if args.fix_snapshot else b'feat: ')+b'add a synthetic entry'
    immutable_json(raw/('snapshot-authoring-planned.json' if args.fix_snapshot else 'first-use-planned.json'),dict(schema_version=1,controls=controls,target_command=command,
        expected_shell_invocations=3,recorder_controls=len(controls),build_sha256=sha256(target/'build.json'),
        expected_message_base64=base64.b64encode(expected).decode(),handwritten_playtestr_json=False))
    await run([runner,'--version'],'first-use-runner-version')
    declared_env=dict(PATH=os.pathsep.join([str(os.path.dirname(shutil.which('git'))),os.path.join(os.environ['SYSTEMROOT'],'System32')]),
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',TZ='UTC')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in declared_env.items():argv+=['--env',name+'='+value]
    for name in ['SYSTEMROOT','WINDIR']:argv+=['--inherit-env',name]
    await run([*argv,'--',*command],'first-public-record-review-replay-export','\n'.join(controls+['']))
    captured=json.loads(spec.read_text(encoding='utf-8'))
    files=[s['state'] for s in captured['steps'] if s.get('state',{}).get('kind')=='file']
    if len(files)!=1 or files[0]['path']!='.git/COMMIT_EDITMSG' or base64.b64decode(files[0]['bytes_base64'])!=expected:
        raise ValueError('Recorded message differs from independently reviewed adapter semantics')
    report=raw/('snapshot-ordinary-report.json' if args.fix_snapshot else 'first-ordinary-report.json')
    await run([runner,'test','--report',report.relative_to(ROOT),spec.relative_to(ROOT)],'first-reviewed-ordinary-test')
    row=json.loads(report.read_text(encoding='utf-8'))['results'][0]
    if row['status']!='passed' or not all(s['status']=='passed' for s in row['steps']) or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:
        raise ValueError('Public ordinary run lacks positive steps/cleanup')
    immutable_json(receipt,dict(schema_version=1,attempts=attempts,shell_invocations=len(attempts),recorder_controls=len(controls),
        handwritten_playtestr_json=False,target_keystrokes_separate=True,runner_sha256=sha256(runner),
        spec_sha256=sha256(spec),report_sha256=sha256(report),independent_expected_file_sha256=hashlib.sha256(expected).hexdigest(),
        human_time='unmeasured',scope='Prepared familiar-agent public route; exact pinned entry and locked upstream adapter. No engineering admission yet.',
        technical_snapshot_route=args.fix_snapshot,
        launcher='Same Node process requires the unmodified standard bin/git-cz entry, with its standard argv; portable relative interpreter lookup. No replaced prompter or application behavior.'))
    print('Public cz-cli route passed:',len(attempts),'invocations,',len(controls),'controls; exact message/cleanup. No admission yet.')


if __name__=='__main__':asyncio.run(main())
