"""Public editor diagnosis, selected maintenance, suffix and relocated replay."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_edit_cases import environment
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    source=(args.package or RAW/'edit/contracts').resolve();source.relative_to(ROOT)
    root=RAW/'edit'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(source,package)
    runner=RAW/('bin/playtestr'+('.exe' if os.name=='nt' else '')) if args.package else RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'edit','maintenance-'+label,env=environment(),expected=expected,
            input=input,timeout=180,campaign=Campaign())
        attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,extra=()):
        report=root/(label+'.json')
        await run([runner,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        outcome=load(report)['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('maintenance cleanup unconfirmed')
        return report,outcome
    spec=package/'N01.json';original=load(spec)
    fixture=package/'fixtures/N01/sentinel.txt';fixture.write_bytes(b'reviewed sentinel revision two\n')
    report,failed=await test(spec,'intended-file-change',1)
    if failed['failure']['category']!='state_assertion_failure':raise RuntimeError('wrong diagnosis')
    await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),
        '--output',(root/'diagnosis.html').relative_to(ROOT)],'offline-diagnosis')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.txt')
    await run([runner,'record','--edit',spec.relative_to(ROOT)],'selected-file-update',
        input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
    changed=load(spec)
    if base64.b64decode(changed['steps'][index]['state']['bytes_base64'])!=fixture.read_bytes():
        raise RuntimeError('selected state update did not capture intended bytes')
    comparison=load(spec);comparison['steps'][index]=original['steps'][index]
    if comparison!=original:raise RuntimeError('selected maintenance changed unrelated expectations')
    await test(spec,'selected-file-replay')
    screen=package/'N04.json';value=load(screen);value['height']=24
    screen.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n');approved=screen.read_bytes()
    _,failed=await test(screen,'intended-viewport-change',1)
    if failed['failure']['category']!='snapshot_mismatch':raise RuntimeError('viewport change was not diagnosed')
    await test(screen,'selected-screen-update',extra=['--update','--snapshot','N04.txt'])
    if screen.read_bytes()!=approved:raise RuntimeError('screen update changed file assertions')
    await test(screen,'selected-screen-replay')
    suffix=package/'rerecorded-suffix.json'
    controls=['/expect reviewed seed','/key End','/text " discarded suffix"','/expect reviewed seed discarded suffix',
        '/rerecord 1','/key End','/text " maintained suffix"','/expect reviewed seed maintained suffix',
        '/expect *','/key CtrlS','/absent *','/key CtrlQ','/exit 0','/file note.txt','/entries .',
        '/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixtures/N01',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','10000',
        '--run-timeout-ms','120000']
    for name in original.get('inherit_env',[]):argv+=['--inherit-env',name]
    for name,value in original.get('env',{}).items():argv+=['--env',name+'='+value]
    argv+=['--','edit','note.txt']
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=load(suffix)
    if 'discarded suffix' in json.dumps(exported):raise RuntimeError('old suffix retained')
    expected=next(s['state'] for s in exported['steps'] if s.get('state',{}).get('path')=='note.txt')
    if base64.b64decode(expected['bytes_base64'])!=b'reviewed seed maintained suffix\n':
        raise RuntimeError('suffix bytes differ from independent expectation')
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        if sha256(relocated/selected.name)!=sha256(selected):raise RuntimeError('relocation changed contracts')
        await test(relocated/selected.name,'relocated-'+selected.stem)
    output=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision',os.environ.get('SOURCE_REVISION','e7b5f29e575e44babe7fdaa2e83e55b62d318305'),
        '--os','linux,windows','--suite','artifacts/runner-readiness-ten-project-pass/edit/host-contracts',
        '--build','python scripts/acceptance/readiness_edit_native_prepare.py',
        '--output',output.relative_to(ROOT)],'generate-ordinary-workflow')
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,suffix_controls=len(controls),
        unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,maintained_spec_sha256=sha256(spec),
        relocated_spec_sha256=sha256(relocated/spec.name),generated_workflow_sha256=sha256(output),
        phase='development',human_time='unmeasured'))
    print('Editor public maintenance, suffix, Unicode relocation and generated workflow passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
