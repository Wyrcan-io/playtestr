"""Ordinary public diagnosis, selected maintenance, suffix and relocated replay."""
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
from readiness_rubygems_cases import PACKAGE, environment


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path)
    parser.add_argument('--complete-existing',type=Path);args=parser.parse_args()
    source=args.package.resolve() if args.package else PACKAGE;source.relative_to(ROOT)
    if args.complete_existing:
        root=args.complete_existing.resolve()
        root.relative_to((RAW/'rubygems').resolve())
        if root.is_symlink() or not root.name.startswith('maintenance caf\u00e9 '):raise RuntimeError('unowned maintenance continuation')
    else:
        root=RAW/'rubygems'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package'
    if not args.complete_existing:shutil.copytree(source,package)
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'rubygems','maintenance-'+label,env=environment(),expected=expected,
            input=input,timeout=130,campaign=Campaign())
        attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,extra=()):
        report=root/(label+'.json')
        await run([runner,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        outcome=json.loads(report.read_text())['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:raise RuntimeError('maintenance cleanup unconfirmed')
        return report,outcome
    async def workflow():
        output=root/'generated-workflow.yml'
        await run([runner,'workflow','--source-revision',os.environ.get('SOURCE_REVISION','e7b5f29e575e44babe7fdaa2e83e55b62d318305'),
            '--os','linux,windows','--suite','artifacts/runner-readiness-ten-project-pass/rubygems/host-contracts',
            '--build','python scripts/acceptance/readiness_rubygems_native_prepare.py',
            '--output',output.relative_to(ROOT)],'generate-ordinary-workflow')
        return output
    if args.complete_existing:
        reports={}
        for name,status in [('intended-file-change','failed'),('selected-file-replay','passed'),
            ('intended-viewport-change','failed'),('selected-screen-update','passed'),
            ('selected-screen-replay','passed'),('suffix-ordinary-replay','passed'),
            ('relocated-normal-set-path','passed'),('relocated-rerecorded-suffix','passed')]:
            report=root/(name+'.json');outcome=json.loads(report.read_text())['results'][0]
            assert outcome['status']==status and outcome['cleanup']['confirmed_exited'] and outcome['workspace']['cleaned']
            reports[name]=sha256(report)
        original=json.loads((source/'normal-set-path.json').read_text())
        changed=json.loads((package/'normal-set-path.json').read_text());changed['steps'][2]=original['steps'][2]
        assert changed==original
        assert sha256(package/'rerecorded-suffix.json')==sha256(root/'relocated \u96ea route/rerecorded-suffix.json')
        output=await workflow()
        immutable_json(root/'journey.json',dict(continuation='only missing workflow generation repeated after argument correction',
            prior_reports=reports,attempts=attempts,selected_file_controls=4,unrelated_steps_preserved=True,
            generated_workflow_sha256=sha256(output),phase='development',human_time='unmeasured'))
        print('Completed retained maintenance journey after public workflow argument correction:',root.relative_to(ROOT));return
    spec=package/'normal-set-path.json';original=json.loads(spec.read_text())
    fixture=package/'project-fixture/Gemfile'
    fixture.write_bytes(b'# reviewed revision two dependency-free project\n')
    report,failed=await test(spec,'intended-file-change',1)
    assert failed['failure']['category']=='state_assertion_failure'
    await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),
               '--output',(root/'diagnosis.html').relative_to(ROOT)],'offline-diagnosis')
    await run([runner,'record','--edit',spec.relative_to(ROOT)],'selected-file-update',
              input='/update-state 3\n/review\n/replay\n/save\n')
    changed=json.loads(spec.read_text())
    assert base64.b64decode(changed['steps'][2]['state']['bytes_base64'])==fixture.read_bytes()
    comparison=json.loads(spec.read_text());comparison['steps'][2]=original['steps'][2]
    assert comparison==original
    await test(spec,'selected-file-replay')
    screen=package/'normal-gem.json';screen_data=json.loads(screen.read_text());screen_data['height']=16
    screen.write_text(json.dumps(screen_data,indent=2)+'\n',encoding='utf-8')
    approved=screen.read_bytes()
    _,failed=await test(screen,'intended-viewport-change',1)
    assert failed['failure']['category']=='snapshot_mismatch'
    await test(screen,'selected-screen-update',extra=['--update','--snapshot','normal-gem.txt'])
    assert screen.read_bytes()==approved
    await test(screen,'selected-screen-replay')
    suffix=package/'rerecorded-suffix.json'
    def choose(value):
        return ['/text '+json.dumps(value),'/key Enter',"/expect Gem 'atlas' was successfully created.",'/exit 0']
    controls=['/expect Enter a test framework.',*choose('minitest'),'/rerecord 1',*choose('rspec'),
              '/file atlas/Rakefile','/file .bundle-user-config','/snapshot suffix.txt','/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture',
          '--temporary-home','--temporary-temp','--inherit-env','RUBYLIB','--width','100','--height','28',
          '--timeout-ms','10000','--run-timeout-ms','120000']
    for key,value in screen_data['env'].items():argv+=['--env',key+'='+value]
    argv+=['--',*screen_data['command']]
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=json.loads(suffix.read_text())
    assert 'minitest' not in json.dumps(exported)
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in exported['steps'] if s.get('state',{}).get('kind')=='file'}
    assert b'RSpec::Core::RakeTask' in files['atlas/Rakefile'] and b'rspec' in files['.bundle-user-config']
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        assert sha256(relocated/selected.name)==sha256(selected)
        await test(relocated/selected.name,'relocated-'+selected.stem)
    output=await workflow()
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,
        suffix_controls=len(controls),unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),
        generated_workflow_sha256=sha256(output),phase='development',human_time='unmeasured'))
    print('Public file/screen maintenance, suffix, Unicode relocation and generated workflow passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
