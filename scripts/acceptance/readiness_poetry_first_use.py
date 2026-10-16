"""Public recorder first-use route; calibrate reviewed metadata independently."""
import asyncio
import argparse
import base64
import json
import os
import tomllib

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    package=ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry'
    fixture=package/'fixture'
    if args.resume:
        if (fixture/'sentinel.txt').read_bytes()!=b'reviewed existing work\n' or list(fixture.iterdir())!=[fixture/'sentinel.txt']:
            raise RuntimeError('first-use fixture changed; preserve it and inspect')
    else:
        fixture.mkdir(exist_ok=False)
        (fixture/'sentinel.txt').write_bytes(b'reviewed existing work\n')
    suffix='.exe' if os.name=='nt' else ''
    runner=RAW/'bin'/('playtestr'+suffix)
    env=dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+str(RAW/'toolchain/go/bin')+os.pathsep+env['PATH']
    for name,folder in [('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),('GOCACHE','go-cache'),('GOPATH','gopath'),('GOMODCACHE','gopath/pkg/mod')]:
        env[name]=str(RAW/folder)
    attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,'poetry',label,env=env,cwd=ROOT,input=input,timeout=180,campaign=Campaign())
        attempts.append(result['id'])
        return result
    if not args.resume:
        await run(['go','build','-o',runner,'./cmd/playtestr'],'first-use-source-runner-build')
        await run([runner,'--version'],'first-use-version-check')
    commands=['/expect Version [','/key Enter','/expect Author [','/key Enter',
        '/expect Would you like to define your main dependencies interactively?',
        '/text "n"','/key Enter',
        '/expect Would you like to define your development dependencies interactively?',
        '/text "n"','/key Enter','/expect Do you confirm generation?',
        '/text "yes"','/key Enter','/exit 0','/snapshot normal-init.txt',
        '/file pyproject.toml','/entries .','/review','/replay','/save']
    spec=package/'normal-init.json'
    argv=[runner,'record','--output',spec.relative_to(ROOT).as_posix(),'--fixture','fixture',
          '--temporary-home','--temporary-temp','--width','100','--height','28',
          '--timeout-ms','10000','--run-timeout-ms','120000']
    for key,value in [('PYTHONDONTWRITEBYTECODE','1'),('PYTHONNOUSERSITE','1'),
        ('GIT_CONFIG_NOSYSTEM','1'),('GIT_CONFIG_GLOBAL',os.devnull),('POETRY_KEYRING_ENABLED','false')]:
        argv+=['--env',key+'='+value]
    argv+=['--','poetry','--no-plugins','init','--name','atlas','--description','Fixture project',
           '--author','Fixture Author <author@example.invalid>','--python','>=3.10','--license','MIT']
    capture=await run(argv,'first-use-record-review-replay-export','\n'.join(commands)+'\n')
    exported=json.loads(spec.read_text())
    selected=next(s['state'] for s in exported['steps'] if s.get('state',{}).get('path')=='pyproject.toml')
    data=tomllib.loads(base64.b64decode(selected['bytes_base64']).decode())
    assert data['project']==dict(name='atlas',version='0.1.0',description='Fixture project',
        authors=[dict(name='Fixture Author',email='author@example.invalid')],license='MIT',
        **{'requires-python':'>=3.10'},dependencies=[])
    assert data['build-system']=={'requires':['poetry-core>=2.0.0,<3.0.0'],'build-backend':'poetry.core.masonry.api'}
    report=RAW/'poetry/first-ordinary-report.json'
    ordinary=await run([runner,'test','--report',report.relative_to(ROOT).as_posix(),spec.relative_to(ROOT).as_posix()],
                       'first-use-ordinary-public-test')
    result=json.loads(report.read_text())['results'][0]
    assert result['status']=='passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned']
    history=[]
    for path in (RAW/'events').glob('*-started.json'):
        event=json.loads(path.read_text())
        if event['project']=='poetry' and event['label'].startswith('first-use-'):history.append(event)
    capture_count=sum(e['label']=='first-use-record-review-replay-export' for e in history)
    immutable_json(package/'first-use.json',dict(schema_version=1,status='development-route-passed',
        route_attempts=[e['id'] for e in history],shell_invocations_including_runner_build=len(history),
        submitted_recorder_controls=capture_count*len(commands),successful_capture_controls=len(commands),
        initial_engineering_count_targets_met=len(history)<=5 and capture_count*len(commands)<=20,
        handwritten_playtestr_json=False,spec_sha256=sha256(spec),runner_sha256=sha256(runner),
        target_build_sha256=sha256(RAW/'active/poetry/build.json'),capture_attempt=capture['id'],
        ordinary_attempt=ordinary['id'],human_authoring_time='unmeasured',
        confounders=['prepared synthetic author and metadata','agent familiarity','owned prerequisites already available']))
    print('Poetry first reviewed ordinary test passed; all attempts retained:',len(history),
          'invocations,',capture_count*len(commands),'submitted controls.')


if __name__=='__main__':asyncio.run(main())
