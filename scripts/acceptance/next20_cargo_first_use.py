"""Record cargo-generate's first useful test using ordinary public controls."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

from adversarial_process import execute
from next20_check import RAW,DOC,ROOT,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


CONFIG='''[template]
cargo_generate_version = ">=0.25.0"

[placeholders.owner]
type = "string"
prompt = "Project owner"
regex = "^.{1,80}$"

[placeholders.mode]
type = "string"
prompt = "Project mode"
choices = ["basic", "extended"]
default = "basic"

[placeholders.readme]
type = "bool"
prompt = "Include documentation"
default = true
'''
PROFILE='project={{project-name}}\nowner={{owner}}\nmode={{mode}}\nreadme={{readme}}\n'
README='{% if readme %}# {{project-name}}\n\nOwner: {{owner}}\nMode: {{mode}}\n{% else %}Documentation disabled\n{% endif %}'


async def main():
    project='cargo-generate';target=RAW/'active'/project;package=DOC/project;raw=RAW/project
    raw.mkdir(exist_ok=True);spec=package/'normal-project.json'
    if spec.exists() or (package/'first-use.json').exists():raise ValueError('preserve existing first route')
    runtime=json.loads((target/'runtime.json').read_text());binary=Path(runtime['native'])
    if sha256(binary)!=runtime['native_sha256']:raise ValueError('changed built executable')
    fixture=package/'fixture';template=fixture/'template';template.mkdir(parents=True,exist_ok=False)
    for name,data in [('cargo-generate.toml',CONFIG),('profile.txt.liquid',PROFILE),('README.md.liquid',README)]:
        (template/name).write_bytes(data.encode())
    (fixture/'sentinel.txt').write_bytes(b'unrelated synthetic data\n')
    runner=RAW/'candidate/windows/playtestr.exe'
    install=json.loads((runner.parent/'installed.json').read_text())
    if sha256(runner)!=install['binary_sha256']:raise ValueError('wrong private archive executable')
    env=environment(target);env['CARGO_HOME']=str(target/'home/cargo');Path(env['CARGO_HOME']).mkdir(exist_ok=True)
    env['GIT_CONFIG_GLOBAL']=os.devnull
    async def run(argv,label,input=None):
        return await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=120,campaign=NextCampaign())
    version=await run([runner,'--version'],'first-use-runner-version')
    controls=['/expect Project Name','/text "synthetic-notes"','/key Enter',
        '/expect Project owner','/text "Ada"','/key Enter',
        '/expect Project mode','/snapshot normal-project.txt','/key Enter',
        '/expect Include documentation','/key Enter','/expect New project created','/exit 0',
        '/file synthetic-notes/profile.txt','/file synthetic-notes/README.md',
        '/file sentinel.txt','/entries synthetic-notes','/review','/replay','/save']
    relative=os.path.relpath(binary,package).replace('\\','/')
    capture=await run([runner,'record','--output',spec.relative_to(ROOT).as_posix(),
        '--fixture','fixture','--temporary-home','--temporary-temp','--env','GIT_CONFIG_NOSYSTEM=1',
        '--env','GIT_CONFIG_GLOBAL='+os.devnull,'--timeout-ms','10000','--run-timeout-ms','120000',
        '--',relative,'generate','--path','template','--vcs','none','--no-workspace'],
        'first-public-record-review-replay-export','\n'.join(controls+['']))
    approved=json.loads(spec.read_text());states=[s['state'] for s in approved['steps'] if 'state' in s]
    expected={'synthetic-notes/profile.txt':b'project=synthetic-notes\nowner=Ada\nmode=basic\nreadme=true\n',
        'synthetic-notes/README.md':b'# synthetic-notes\n\nOwner: Ada\nMode: basic\n',
        'sentinel.txt':b'unrelated synthetic data\n'}
    for name,data in expected.items():
        state=next(s for s in states if s['path']==name and s['kind']=='file')
        if base64.b64decode(state['bytes_base64'])!=data:raise ValueError('recorded output differs from independent expected bytes: '+name)
    if set(next(s for s in states if s['path']=='synthetic-notes' and s['kind']=='entries')['entries'])!={'profile.txt','README.md'}:
        raise ValueError('unexpected generated file set')
    report=raw/'first-ordinary-report.json'
    ordinary=await run([runner,'test','--report',report,spec],'first-reviewed-ordinary-test')
    result=json.loads(report.read_text())['results'][0]
    if result['status']!='passed' or not result['workspace']['cleaned'] or not result['cleanup']['confirmed_exited']:
        raise ValueError('first ordinary positive/cleanup evidence incomplete')
    immutable_json(package/'first-use.json',dict(schema_version=1,status='prepared-agent-route-passed-not-admitted',
        shell_invocations=3,recorder_controls=len(controls),attempts=[version['id'],capture['id'],ordinary['id']],
        runner_sha256=sha256(runner),target_binary_sha256=sha256(binary),spec_sha256=sha256(spec),
        report_sha256=sha256(report),handwritten_playtestr_json=False,
        independent_expected_file_sha256={n:hashlib.sha256(b).hexdigest() for n,b in expected.items()},
        human_time='unmeasured',confounders=['Prepared synthetic local template','Operator familiar with recorder'],
        target_setup_excluded='Pinned source and all registry payload/hook review; offline native source build',
        measured_window='Includes all actual first-use labels and failed attempts separately; no invented human interval.'))
    print('Public local-template recorder/export/ordinary test passed with independently checked output; no admission credit yet.')


if __name__=='__main__':asyncio.run(main())
