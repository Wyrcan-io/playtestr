"""Use only public recorder controls for an actual peco selection and saved stdout."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC,RAW,ROOT,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    project='peco';target=RAW/'active'/project;package=DOC/project;root=RAW/project/'first-public-v1';root.mkdir(exist_ok=False)
    runtime=json.loads((target/'runtime.json').read_text());build=json.loads((target/'build.json').read_text());binary=Path(runtime['native']);app=Path(runtime['target'])
    for name,digest in build['compiled_files'].items():
        if sha256(binary.parent/name)!=digest:raise ValueError('actual built target/capture fixture changed')
    fixture=package/'fixture';fixture.mkdir(exist_ok=False)
    config=(json.dumps(dict(Prompt='Select>',QueryExecutionDelay=0,OnCancel='error',InitialFilter='IgnoreCase',Filters=['IgnoreCase','CaseSensitive','Regexp'],SuppressStatusMsg=True),sort_keys=True,indent=2)+'\n').encode()
    expected={'candidates.txt':b'alpha notes\nbeta draft\ngamma release\n','config.json':config,'sentinel.txt':b'unrelated synthetic data\n','selected.txt':b'beta draft\n'}
    for name,body in expected.items():
        if name!='selected.txt':(fixture/name).write_bytes(body)
    runner=executable('native-exit-v1');spec=package/'normal-selection.json';controls=['/expect gamma release','/expect alpha notes','/text "beta"','/expect Select> beta','/absent alpha notes',
        '/snapshot normal-selection.txt','/key Enter','/exit 0','/file selected.txt','/file candidates.txt','/file config.json','/file sentinel.txt','/entries .','/review','/replay','/save']
    immutable_json(root/'planned.json',dict(schema_version=1,candidate='v0.4.0-rc.6',runner_sha256=sha256(runner),runtime_sha256=sha256(target/'runtime.json'),
        actual_target_sha256=sha256(app),capture_fixture_sha256=sha256(binary),controls=controls,independent_expected_bytes={n:base64.b64encode(b).decode() for n,b in expected.items()},
        handwritten_playtestr_json=False,human_participants=0,scope='First prepared-agent public recorder window. Actual source-built peco reads synthetic input and renders its real tcell UI; reviewed capture fixture redirects only selected stdout into a bounded workspace file. No target mutation or synthetic output substitution.'))
    env=environment(target);attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=150,campaign=NextCampaign());attempts.append(result['id']);return result
    version=await run([runner,'--version'],'peco-first-public-runner-version')
    if version['output'].strip()!='playtestr v0.4.0-rc.6':raise ValueError('wrong actual private archive version')
    relative=os.path.relpath(binary,package).replace('\\','/')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','100','--height','24','--timeout-ms','10000','--run-timeout-ms','120000','--env','TERM=xterm-256color','--env','LANG=C.UTF-8','--env','LC_ALL=C.UTF-8',
        '--',relative,'--app',app.name,'--output','selected.txt','--','--rcfile','config.json','candidates.txt']
    await run(argv,'peco-first-public-record-review-replay-export','\n'.join(controls+['']))
    approved=json.loads(spec.read_text());states={s['state']['path']:s['state'] for s in approved['steps'] if 'state' in s}
    for name,body in expected.items():
        if base64.b64decode(states[name]['bytes_base64'],validate=True)!=body:raise ValueError('captured output differs from complete independent oracle: '+name)
    if set(states['.']['entries'])!=set(expected):raise ValueError('unexpected saved-state file set')
    report=root/'ordinary-report.json';await run([runner,'test','--report',report,'--artifacts-dir',root/'ordinary-evidence',spec],'peco-first-reviewed-ordinary-test')
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('ordinary first route/cleanup incomplete')
    immutable_json(package/'first-use.json',dict(schema_version=1,status='prepared-public-route-passed-not-admitted',initial_window=True,candidate='v0.4.0-rc.6',shell_invocations=3,recorder_controls=len(controls),attempts=attempts,
        handwritten_playtestr_json=False,runner_sha256=sha256(runner),actual_target_sha256=sha256(app),capture_fixture_sha256=sha256(binary),spec_sha256=sha256(spec),ordinary_report_sha256=sha256(report),
        independent_expected_file_sha256={n:hashlib.sha256(b).hexdigest() for n,b in expected.items()},human_participants=0,human_time='unmeasured',
        confounders=['Prepared synthetic file/config','Agent read implementation','Reviewed compiled stdout-capture fixture supplied as installation prerequisite'],scope='Public recorder/review/fresh replay/export/ordinary route with actual tcell target and independently verified selected output/preserved files/entries. No admission or beginner-readiness credit.'))
    print('First public peco recording,review,replay,export and ordinary test passed;3shell/16controls; exact selected stdout and preserved fixture verified. No admission.')


if __name__=='__main__':asyncio.run(main())
