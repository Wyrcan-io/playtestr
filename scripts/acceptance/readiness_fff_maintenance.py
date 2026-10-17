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
from readiness_fff_cases import environment,create,expect,quit_clean
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    source=(args.package or RAW/'fff/contracts').resolve();source.relative_to(ROOT)
    root=RAW/'fff'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(source,package)
    runner=RAW/('bin/playtestr'+('.exe' if os.name=='nt' else '')) if args.package else RAW/'bin/playtestr'
    attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'fff','maintenance-'+label,env=environment(),expected=expected,
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
    screen=package/'N04.json';value=load(screen)
    if 'FFF_FILE_FORMAT' in value['env']:raise RuntimeError('unreviewed original display prefix')
    snapshot=next(step['snapshot'] for step in value['steps'] if 'snapshot' in step)
    original_rows=load(package/'snapshots'/snapshot)
    value['env']['FFF_FILE_FORMAT']='reviewed %f'
    screen.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n');approved=screen.read_bytes()
    _,failed=await test(screen,'intended-screen-format-change',1)
    if failed['failure']['category']!='snapshot_mismatch':raise RuntimeError('display prefix change was not diagnosed')
    await test(screen,'selected-screen-update',extra=['--update','--snapshot',snapshot])
    if screen.read_bytes()!=approved:raise RuntimeError('screen update changed file assertions')
    updated_rows=load(package/'snapshots'/snapshot)
    intended={**original_rows,'text':''.join('reviewed '+line if line.strip() else line for line in original_rows['text'].splitlines(keepends=True))}
    if updated_rows!=intended:raise RuntimeError('independent intended screen-prefix review rejects update')
    await test(screen,'selected-screen-replay')
    suffix=package/'rerecorded-suffix.json'
    controls=[expect('source.txt'),*create('discarded.txt'),'/rerecord 1',*create('maintained.txt'),
        *quit_clean(),'/file maintained.txt','/file source.txt','/file sentinel.txt','/missing discarded.txt',
        '/entries .','/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixtures/N01',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','10000',
        '--run-timeout-ms','120000']
    for name in original.get('inherit_env',[]):argv+=['--inherit-env',name]
    for name,value in original.get('env',{}).items():argv+=['--env',name+'='+value]
    argv+=['--','fff']
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=load(suffix)
    if any('discarded.txt' in step.get('text','') for step in exported['steps']):raise RuntimeError('old creation input retained')
    files={step['state']['path']:base64.b64decode(step['state']['bytes_base64']) for step in exported['steps']
           if step.get('state',{}).get('kind')=='file'}
    if files!={'maintained.txt':b'','source.txt':b'reviewed source\n','sentinel.txt':b'reviewed sentinel revision two\n'}:
        raise RuntimeError('independent suffix/preservation byte review failed')
    if not any(step.get('state',{}).get('path')=='discarded.txt' and step['state']['kind']=='absent' for step in exported['steps']):
        raise RuntimeError('discarded suffix path not asserted absent')
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        if sha256(relocated/selected.name)!=sha256(selected):raise RuntimeError('relocation changed contracts')
        await test(relocated/selected.name,'relocated-'+selected.stem)
    output=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision',os.environ.get('SOURCE_REVISION','e7b5f29e575e44babe7fdaa2e83e55b62d318305'),
        '--os','linux,macos','--suite','artifacts/runner-readiness-ten-project-pass/fff/host-contracts',
        '--build','python3 scripts/acceptance/readiness_fff_native_prepare.py --target-only',
        '--output',output.relative_to(ROOT)],'generate-ordinary-workflow')
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,suffix_controls=len(controls),
        unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,maintained_spec_sha256=sha256(spec),
        relocated_spec_sha256=sha256(relocated/spec.name),generated_workflow_sha256=sha256(output),
        phase='development',human_time='unmeasured'))
    print('Editor public maintenance, suffix, Unicode relocation and generated workflow passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
