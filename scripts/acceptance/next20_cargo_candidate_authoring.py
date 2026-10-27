"""Repeat the public recorder route on the replacement, preserving first-use history."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,default=1);args=parser.parse_args()
    if not 1<=args.generation<=3:raise ValueError('bounded explicit authoring generation required')
    project='cargo-generate';canonical=DOC/project;target=RAW/'active'/project
    original=canonical/'first-use.json';historical=json.loads(original.read_text())
    if historical['handwritten_playtestr_json']:raise ValueError('historical public route not established')
    package=canonical/'candidate-authoring/native-exit-v1'/str(args.generation)
    raw=RAW/project/'candidate-authoring/native-exit-v1'/str(args.generation)
    if package.exists() or raw.exists():raise ValueError('preserve every earlier authoring attempt')
    runner=executable('native-exit-v1');runtime=json.loads((target/'runtime.json').read_text());binary=Path(runtime['native'])
    binary.resolve(strict=True).relative_to(target.resolve(strict=True))
    if sha256(binary)!=runtime['native_sha256']:raise ValueError('built target changed')
    package.mkdir(parents=True);raw.mkdir(parents=True)
    shutil.copytree(canonical/'fixture',package/'fixture')
    expected={'synthetic-notes/profile.txt':b'project=synthetic-notes\nowner=Ada\nmode=basic\nreadme=true\n',
        'synthetic-notes/README.md':b'# synthetic-notes\n\nOwner: Ada\nMode: basic\n',
        'sentinel.txt':b'unrelated synthetic data\n'}
    controls=['/expect Project Name','/text "synthetic-notes"','/key Enter',
        '/expect Project owner','/text "Ada"','/key Enter','/expect Project mode',
        '/snapshot-rows normal-project.rows.json 4 9','/key Enter','/expect Include documentation','/key Enter',
        '/expect New project created','/exit 0','/file synthetic-notes/profile.txt','/file synthetic-notes/README.md',
        '/file sentinel.txt','/entries synthetic-notes','/review','/replay','/save']
    env=environment(target);env['CARGO_HOME']=str(target/'home/cargo');Path(env['CARGO_HOME']).mkdir(exist_ok=True)
    spec=package/'normal-project.json';campaign=NextCampaign()
    async def run(argv,label,input=None):
        return await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=140,campaign=campaign)
    immutable_json(raw/'planned.json',dict(schema_version=1,runner_sha256=sha256(runner),target_sha256=sha256(binary),
        historical_first_use_sha256=sha256(original),generation=args.generation,controls=controls,
        first_attempt=False,human_time='unmeasured',project_credits=0))
    version=await run([runner,'--version'],'replacement-authoring-version')
    if version['output'].strip()!='playtestr v0.4.0-rc.6':raise ValueError('wrong replacement version')
    recorded=await run([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture',
        '--temporary-home','--temporary-temp','--env','GIT_CONFIG_NOSYSTEM=1','--env','GIT_CONFIG_GLOBAL='+os.devnull,
        '--env','USERNAME=synthetic','--env','USER=synthetic','--width','120','--height','24',
        '--timeout-ms','10000','--run-timeout-ms','120000','--',os.path.relpath(binary,package).replace('\\','/'),
        'generate','--path','template','--vcs','none','--no-workspace'],
        'replacement-public-record-review-replay-export','\n'.join(controls+['']))
    exported=json.loads(spec.read_text());states=[s['state'] for s in exported['steps'] if 'state' in s]
    for name,payload in expected.items():
        rows=[s for s in states if s.get('path')==name and s.get('kind')=='file']
        if len(rows)!=1 or base64.b64decode(rows[0]['bytes_base64'])!=payload:raise ValueError('export differs from independent output bytes')
    entries=[s for s in states if s.get('path')=='synthetic-notes' and s.get('kind')=='entries']
    if len(entries)!=1 or set(entries[0]['entries'])!={'profile.txt','README.md'}:raise ValueError('export generated file set differs')
    report=raw/'ordinary-report.json';ordinary=await run([runner,'test','--report',report,spec],'replacement-public-reviewed-ordinary-test')
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('authoring ordinary outcome/cleanup incomplete')
    immutable_json(package/'requalification.json',dict(schema_version=1,status='candidate-public-authoring-requalified-not-admitted',
        candidate_series='native-exit-v1',historical_first_use_sha256=sha256(original),first_attempt=False,
        handwritten_playtestr_json=False,shell_invocations=3,recorder_controls=len(controls),
        attempts=[version['id'],recorded['id'],ordinary['id']],runner_sha256=sha256(runner),target_binary_sha256=sha256(binary),
        spec_sha256=sha256(spec),ordinary_report=report.relative_to(ROOT).as_posix(),ordinary_report_sha256=sha256(report),
        independent_expected_file_sha256={n:hashlib.sha256(data).hexdigest() for n,data in expected.items()},
        human_time='unmeasured',project_credits=0,scope='Actual repeat on replacement archive after prior exposure. Original first-use misses and counts remain historical; no beginner-study or first-attempt claim.'))
    print('Replacement public recorder/replay/export/ordinary route passed with independent saved-output bytes.')


if __name__=='__main__':asyncio.run(main())
