"""Public file/screen maintenance, fresh suffix rerecord and unchanged relocation."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    source=args.package.resolve() if args.package else ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry'
    source.relative_to(ROOT)
    root=RAW/'poetry'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(source,package)
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env['PATH']
    attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'poetry','maintenance-'+label,env=env,expected=expected,input=input,
                             timeout=130,campaign=Campaign())
        attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,extra=()):
        report=root/(label+'.json')
        await run([runner,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',
                  (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        outcome=json.loads(report.read_text())['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('maintenance cleanup unconfirmed')
        return report,outcome
    spec=package/'normal-version.json';original=json.loads(spec.read_text())
    fixture=package/'project-fixture/pyproject.toml'
    fixture.write_bytes(fixture.read_bytes().replace(b'preserve this reviewed comment',b'preserve reviewed revision two'))
    report,failed=await test(spec,'intended-file-change',1)
    assert failed['failure']['category']=='state_assertion_failure'
    await run([runner,'report','--input',report,'--evidence-root',root,'--output',root/'diagnosis.html'],'offline-diagnosis')
    await run([runner,'record','--edit',spec],'selected-file-update',input='/update-state 3\n/review\n/replay\n/save\n')
    changed=json.loads(spec.read_text())
    value=base64.b64decode(changed['steps'][2]['state']['bytes_base64'])
    assert b'preserve reviewed revision two' in value and b'version = "1.3.0"' in value
    comparison=json.loads(spec.read_text());comparison['steps'][2]=original['steps'][2]
    assert comparison==original
    await test(spec,'selected-file-replay')
    screen_spec=package/'normal-init.json';screen_data=json.loads(screen_spec.read_text())
    screen_data['height']=30
    screen_spec.write_text(json.dumps(screen_data,indent=2)+'\n')
    approved=screen_spec.read_bytes()
    _,failed=await test(screen_spec,'intended-viewport-screen-change',1)
    assert failed['failure']['category']=='snapshot_mismatch'
    await test(screen_spec,'selected-screen-update',extra=['--update','--snapshot','normal-init.txt'])
    assert screen_spec.read_bytes()==approved
    await test(screen_spec,'selected-screen-replay')
    suffix=package/'rerecorded-suffix.json'
    def inputs(version):
        return ['/text '+json.dumps(version),'/key Enter','/expect Author [','/key Enter',
          '/expect Would you like to define your main dependencies interactively?','/text "n"','/key Enter',
          '/expect Would you like to define your development dependencies interactively?','/text "n"','/key Enter',
          '/expect Do you confirm generation?','/text "yes"','/key Enter','/exit 0']
    controls=['/expect Version [',*inputs('0.9.0'),'/rerecord 1',*inputs('0.2.0'),
              '/file pyproject.toml','/entries .','/snapshot suffix.txt','/review','/replay','/save']
    argv=[runner,'record','--output',suffix,'--fixture','fixture','--temporary-home','--temporary-temp',
          '--width','100','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for key,value in screen_data['env'].items():argv+=['--env',key+'='+value]
    argv+=['--',*screen_data['command']]
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=json.loads(suffix.read_text())
    assert '0.9.0' not in json.dumps(exported)
    selected=next(s['state'] for s in exported['steps'] if s.get('state',{}).get('kind')=='file')
    assert b'version = "0.2.0"' in base64.b64decode(selected['bytes_base64'])
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    assert sha256(relocated/spec.name)==sha256(spec) and sha256(relocated/suffix.name)==sha256(suffix)
    await test(relocated/spec.name,'relocated-file-replay')
    await test(relocated/suffix.name,'relocated-suffix-replay')
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,
        suffix_controls=len(controls),unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,
        relocated_spec_sha256=sha256(relocated/spec.name),maintained_spec_sha256=sha256(spec),
        human_time='unmeasured',phase='development',project_admitted=False))
    print('Poetry public file/screen maintenance, suffix and Unicode relocation passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
