"""Public Plop diagnosis, selected maintenance, suffix rerecord and relocation."""
import asyncio
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_plop_cases import PACKAGE


async def main():
    global PACKAGE
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path)
    args=parser.parse_args()
    if args.package:
        PACKAGE=args.package.resolve();PACKAGE.relative_to(ROOT)
    campaign=Campaign()
    root=RAW/'plop'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'original route';shutil.copytree(PACKAGE,package)
    spec=package/'normal-artifact.json'
    original=spec.read_bytes();original_json=json.loads(original)
    snapshot=package/'snapshots/normal-artifact.txt';screen_before=snapshot.read_bytes()
    fixture=package/'fixture/plopfile.cjs'
    configuration=fixture.read_bytes()
    old=b"template: 'name={{name}}\\n'"
    if configuration.count(old)!=1:raise RuntimeError('intentional configuration change anchor missing')
    fixture.write_bytes(configuration.replace(old,b"template: 'revision=2 name={{name}}\\n'"))
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=dict(os.environ);env['PATH']=str(RAW/'active/plop/bin')+os.pathsep+env['PATH']
    attempts=[]
    async def run(argv,label,expected=0,input=None):
        attempt=await execute(argv,'plop','maintenance-'+label,env=env,expected=expected,input=input,
                              timeout=120,campaign=campaign)
        attempts.append(dict(label=label,id=attempt['id'],seconds=attempt['seconds']))
        return attempt
    async def test(path,label,expected=0,extra=()):
        report=root/(label+'.json')
        result=await run([runner,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',
                          (root/(label+'-evidence')).relative_to(ROOT),path.relative_to(ROOT)],label,expected)
        data=json.loads(report.read_text(encoding='utf-8'))['results'][0]
        if not data['workspace']['cleaned'] or not data['cleanup']['confirmed_exited']:
            raise RuntimeError('maintenance managed cleanup unconfirmed')
        return report,data,result
    report,failed,_=await test(spec,'intended-file-change-rejected',1)
    if failed['failure']['category']!='state_assertion_failure':raise RuntimeError('wrong failure diagnosis')
    await run([runner,'report','--input',report,'--evidence-root',root,'--output',root/'diagnosis.html'],'offline-diagnosis')
    await run([runner,'record','--edit',spec],'selected-file-update',input='/update-state 7\n/review\n/replay\n/save\n')
    changed=json.loads(spec.read_bytes())
    expected=base64.b64encode(b'revision=2 name=alpha\n').decode()
    if changed['steps'][6]['state']['bytes_base64']!=expected:raise RuntimeError('unreviewed updated bytes')
    comparison=json.loads(spec.read_bytes());comparison['steps'][6]=original_json['steps'][6]
    if comparison!=original_json or snapshot.read_bytes()!=screen_before:
        raise RuntimeError('unrelated state/screen expectation changed')
    await test(spec,'selected-file-update-replay')
    approved=spec.read_bytes()
    fixture.write_bytes(fixture.read_bytes().replace(b"message: 'Artifact name'",b"message: 'Artifact name (reviewed revision)'"))
    _,screen_failure,_=await test(spec,'intended-screen-change-rejected',1)
    if screen_failure['failure']['category']!='snapshot_mismatch':raise RuntimeError('screen change did not reach selected snapshot')
    await test(spec,'selected-screen-update',extra=['--update','--snapshot','normal-artifact.txt'])
    if spec.read_bytes()!=approved:raise RuntimeError('screen update changed file expectations')
    await test(spec,'selected-screen-update-replay')
    suffix=package/'rerecorded-suffix.json'
    commands='\n'.join(['/expect Artifact name','/text "discarded"','/key Enter','/expect discarded.txt','/exit 0',
        '/rerecord 1','/text "beta"','/key Enter','/expect beta.txt','/exit 0',
        '/file out/beta.txt','/entries out','/snapshot rerecorded-suffix.txt','/review','/replay','/save',''])
    target=['cmd.exe','/d','/s','/c','plop --no-progress'] if os.name=='nt' else ['plop','--no-progress']
    await run([runner,'record','--output',suffix,'--fixture','fixture','--temporary-home','--temporary-temp',
               '--timeout-ms','10000','--run-timeout-ms','120000','--',*target],'suffix-rerecord',input=commands)
    suffix_data=json.loads(suffix.read_text(encoding='utf-8'))
    if suffix_data['steps'][0]!={'expect':'Artifact name'} or 'discarded' in json.dumps(suffix_data):
        raise RuntimeError('discarded suffix survived fresh rerecord')
    if next(s['state'] for s in suffix_data['steps'] if s.get('state',{}).get('kind')=='file')['bytes_base64']!=base64.b64encode(b'revision=2 name=beta\n').decode():
        raise RuntimeError('rerecorded bytes differ from reviewed template')
    await test(suffix,'rerecorded-suffix-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    if sha256(relocated/spec.name)!=sha256(spec):raise RuntimeError('relocation changed contract bytes')
    await test(relocated/spec.name,'relocated-state-replay')
    await test(relocated/suffix.name,'relocated-suffix-replay')
    immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,
        selected_file_update_controls=4,suffix_record_controls=16,human_time='unmeasured',
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),
        original_spec_sha256=sha256(PACKAGE/'normal-artifact.json'),
        phase='development',project_admitted=False))
    print('Plop public maintenance/relocation:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
