"""Public selected updates, fresh suffix reconstruction and exact relocation."""
import asyncio
import base64
import json
import os
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_rclone_native_contracts import target_environment


def require(value,message):
    if not value:raise RuntimeError(message)


async def main():
    root=RAW/'rclone'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(RAW/'rclone/host-contracts',package)
    binary,candidate,cell=runner();attempts=[]
    async def call(label,argv,expected=0,stdin=None):
        result=await execute(argv,'rclone','maintenance-'+label,env=target_environment(),expected=expected,
            input=stdin,timeout=150,campaign=Campaign());attempts.append(dict(label=label,id=result['id']))
        return result
    async def test(label,spec,expected=0,extra=()):
        report=root/(label+'.json')
        await call(label,[binary,'test',*extra,'--report',report,'--artifacts-dir',root/(label+'-evidence'),spec],expected)
        value=load(report);result=value['results'][0]
        require(value['runner_version']==candidate['version'] and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'],'maintenance identity/cleanup differs')
        return report,result
    spec=package/'N01.json';original=load(spec)
    sentinel=package/'fixtures/N01/sentinel.bin';sentinel.write_bytes(b'reviewed sentinel revision two\x00\r\n')
    report,result=await test('intended-file-change',spec,1)
    require(result['failure']['category']=='state_assertion_failure','wrong selected-file diagnosis')
    await call('offline-diagnosis',[binary,'report','--input',report,'--evidence-root',root,'--output',root/'diagnosis.html'])
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.bin')
    await call('selected-file-update',[binary,'record','--edit',spec],stdin=f'/update-state {index+1}\n/review\n/replay\n/save\n')
    changed=load(spec)
    require(base64.b64decode(changed['steps'][index]['state']['bytes_base64'])==sentinel.read_bytes(),'selected file differs')
    comparison=load(spec);comparison['steps'][index]=original['steps'][index]
    require(comparison==original,'selected update changed unrelated expectations')
    await test('selected-file-replay',spec)
    screen_spec=package/'N02.json';screen=load(screen_spec)
    baseline=next(s['snapshot'] for s in screen['steps'] if 'snapshot' in s);path=package/'snapshots'/baseline
    before=path.read_bytes()
    require(before.startswith(b'y) Yes\nn) No (default)\n'),'reviewed original viewport differs')
    expected=b'Edit advanced config?\n'+before
    screen['height']=29;screen_spec.write_text(json.dumps(screen,indent=2)+'\n',encoding='utf-8',newline='\n')
    reviewed=screen_spec.read_bytes()
    _,result=await test('intended-viewport-change',screen_spec,1)
    require(result['failure']['category']=='snapshot_mismatch','wrong viewport-change diagnosis')
    await test('selected-screen-update',screen_spec,extra=['--update','--snapshot',baseline])
    require(screen_spec.read_bytes()==reviewed and path.read_bytes()==expected,'selected screen differs from exact predeclared extra row')
    immutable_json(root/'selected-screen-review.json',dict(original_height=28,updated_height=29,
        original_sha256=__import__('hashlib').sha256(before).hexdigest(),updated_sha256=sha256(path),
        exact_review='One additional preceding row: Edit advanced config? plus LF. All prior bytes and saved-state assertions unchanged.'))
    await test('selected-screen-replay',screen_spec)
    suffix_fixture=package/'suffix-fixture';shutil.copytree(package/'fixtures/N02',suffix_fixture)
    suffix=package/'rerecorded-suffix.json'
    text=lambda s:'/text '+json.dumps(s,ensure_ascii=True)
    controls=['/expect No remotes found, make a new one?',text('n\r'),'/expect name>',text('wrong'),'/expect wrong',
        '/rerecord 3',text('corrected\r'),'/expect Storage>',text('alias\r'),'/expect remote>',text('.\r'),
        '/expect Edit advanced config?',text('n\r'),'/expect Keep this "corrected" remote?',text('y\r'),
        '/expect Current remotes:','/snapshot suffix.txt',text('q\r'),'/exit 0',
        '/file rclone.conf','/file sentinel.bin','/entries .','/review','/replay','/save']
    await call('fresh-suffix-rerecord',[binary,'record','--output',suffix,'--fixture','suffix-fixture','--temporary-home','--temporary-temp',
        '--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000','--env','TERM=xterm-256color',
        '--','rclone','--config','rclone.conf','config'],stdin='\n'.join(controls)+'\n')
    exported=load(suffix);newline=b'\r\n' if os.name=='nt' else b'\n'
    expected_files={'rclone.conf':newline.join([b'[corrected]',b'type = alias',b'remote = .',b'',b'']),
                    'sentinel.bin':b'preserve\x00existing\r\n'}
    saved={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in exported['steps'] if s.get('state',{}).get('kind')=='file'}
    require(saved==expected_files and all(s.get('text')!='wrong' and s.get('expect')!='wrong' for s in exported['steps']),
            'discarded suffix or incorrect saved bytes survived reconstruction')
    await test('suffix-ordinary-replay',suffix)
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,screen_spec,suffix]:
        require(sha256(relocated/selected.name)==sha256(selected),'relocation changed contract bytes')
        await test('relocated-'+selected.stem,relocated/selected.name)
    workflow=root/'generated-workflow.yml'
    await call('generate-ordinary-workflow',[binary,'workflow','--source-revision',candidate['source_revision'],'--os','linux,windows',
        '--suite','artifacts/runner-readiness-ten-project-pass/rclone/host-contracts',
        '--build','python scripts/acceptance/readiness_rclone_native_prepare.py','--output',workflow])
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,suffix_controls=len(controls),
        unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,maintained_spec_sha256=sha256(spec),
        relocated_spec_sha256=sha256(relocated/spec.name),screen_spec_sha256=sha256(screen_spec),
        generated_workflow_sha256=sha256(workflow),runner_sha256=cell['binary_sha256'],provisional_archive_sha256=cell['archive_sha256'],
        phase='reserved provisional transfer',human_time='unmeasured',generated_workflow_execution=False))
    print('Public Rclone selected state/screen updates, suffix reconstruction and Unicode relocation passed.')


if __name__=='__main__':asyncio.run(main())
