"""Public same-execution saved-state journey using the deterministic fixture.

This is product calibration, never a real-project admission or human timing.
"""
import asyncio
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    campaign = Campaign()
    suffix = '.exe' if os.name == 'nt' else ''
    runner = RAW/'bin'/('playtestr'+suffix)
    fixture = RAW/'bin'/('fixture'+suffix)
    runner.parent.mkdir(parents=True,exist_ok=True)
    env = dict(os.environ)
    for name, folder in [('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),('GOCACHE','go-cache')]:
        path = RAW/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env['PYTHONIOENCODING']='utf-8'

    async def run(argv,label,expected=0,input=None,timeout=60):
        return await execute(argv,'state-calibration',label,cwd=ROOT,env=env,
                             expected=expected,input=input,timeout=timeout,campaign=campaign)
    await run(['go','build','-o',runner,'./cmd/playtestr'],'build-current-runner',timeout=120)
    await run(['go','build','-o',fixture,'./cmd/fixture'],'build-correct-fixture',timeout=120)
    directory = RAW/('public route caf\u00e9 '+uuid.uuid4().hex[:8])
    (directory/'fixture').mkdir(parents=True)
    (directory/'fixture'/'seed.txt').write_bytes(b'synthetic\n')
    spec = directory/'saved.json'
    relative_spec = spec.relative_to(ROOT).as_posix()
    commands = '\n'.join([
        '/expect Press Enter to save the synthetic file', '/key Enter',
        '/expect Saved successfully', '/exit 0', '/snapshot saved.txt',
        '/file result.bin', '/entries .', '/review', '/replay', '/save', ''
    ])
    capture = await run([runner,'record','--output',relative_spec,'--fixture','fixture',
                         '--temporary-home','--temporary-temp','--','../bin/'+fixture.name,'saved-state'],
                        'public-record-review-replay-export',input=commands)
    contract = sha256(spec)
    (directory/'original-reviewed-spec.json').write_bytes(spec.read_bytes())
    baseline = directory/'snapshots'/'saved.txt'
    baseline_hash = sha256(baseline)
    good_binary = sha256(fixture)
    receipts=[]
    async def ordinary(label,expected):
        report = directory/(label+'.json')
        result = await run([runner,'test','--artifacts-dir',str(directory.relative_to(ROOT)/label),
                            '--report',str(report.relative_to(ROOT)),relative_spec],label,expected)
        data = json.loads(report.read_text(encoding='utf-8'))
        observed = data['results'][0]
        assert observed['cleanup']['confirmed_exited'] and observed['workspace']['cleaned']
        assert data['report_version'] == 3
        for step in observed['steps']:
            if step['action']=='state' and step['status'] in {'passed','failed'}:
                assert step['state']['invocation_id']==observed['invocation_id']
                assert step['state']['workspace_id']==observed['workspace']['id']
        assert sha256(spec)==contract and sha256(baseline)==baseline_hash
        receipts.append(dict(attempt=result['id'],target_sha256=sha256(fixture),report=report.relative_to(ROOT).as_posix(),
                             report_sha256=sha256(report),status=observed['status'],
                             invocation_id=observed['invocation_id']))
        return observed,report
    await ordinary('correct',0)
    await run(['go','build','-ldflags','-X main.stateFileValue=corrupt','-o',fixture,'./cmd/fixture'],
              'build-success-looking-wrong-saved-bytes',timeout=120)
    corrupt_binary=sha256(fixture)
    assert corrupt_binary!=good_binary
    bad,report=await ordinary('corruption',1)
    assert bad['failure']['category']=='state_assertion_failure'
    assert all(s['status']=='passed' for s in bad['steps'][:5])
    await run([runner,'report','--input',str(report.relative_to(ROOT)),
               '--evidence-root',str(directory.relative_to(ROOT)),
               '--output',str((directory/'corruption.html').relative_to(ROOT))],'public-offline-state-diagnosis')
    await run(['go','build','-o',fixture,'./cmd/fixture'],'restore-only-target',timeout=120)
    assert sha256(fixture)==good_binary
    await ordinary('restored',0)
    # Selected maintenance: an intended target change is captured without editing JSON.
    await run(['go','build','-ldflags','-X main.stateFileValue=intended-change','-o',fixture,'./cmd/fixture'],
              'build-intended-state-change',timeout=120)
    await run([runner,'record','--edit',relative_spec],'public-selected-file-maintenance',
              input='/update-state 6\n/review\n/replay\n/save\n')
    assert sha256(baseline)==baseline_hash
    reviewed = json.loads(spec.read_text(encoding='utf-8'))
    assert reviewed['steps'][5]['state']['bytes_base64']=='aW50ZW5kZWQtY2hhbmdl'
    await run([runner,'test',relative_spec],'ordinary-test-after-selected-maintenance')
    await run(['go','build','-o',fixture,'./cmd/fixture'],'restore-fixture-after-calibration',timeout=120)
    assert sha256(fixture)==good_binary
    immutable_json(directory/'journey.json',dict(schema_version=1,type='synthetic-product-control',
        runner_sha256=sha256(runner),correct_target_sha256=good_binary,corrupt_target_sha256=corrupt_binary,
        original_spec_sha256=contract,screen_baseline_sha256=baseline_hash,
        capture_attempt=capture['id'],recorder_controls=10,ordinary=receipts,
        authoring='automated prepared public command route; human time unmeasured',
        target_fixture_restored=True))
    print('Public record/test/corruption/HTML/restoration/selected-maintenance passed:',directory.relative_to(ROOT))


if __name__ == '__main__': asyncio.run(main())
