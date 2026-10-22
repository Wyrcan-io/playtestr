"""Actual interpreted target source faults against unchanged reviewed contracts."""
import asyncio
import argparse
import difflib
import json
import uuid
import os
from pathlib import Path

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    package=(args.package or DOC/'jrnl').resolve();package.relative_to(ROOT)
    target=RAW/'active/jrnl';freeze=package/'development-test-freeze.json'
    frozen=json.loads(freeze.read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('approved test/fixture changed before fault')
    faults=[
        dict(id='F01',path='jrnl/messages/MsgText.py',before=b'Delete entry',after=b'Discard entry',
             category='assertion_timeout',meaning='Incorrect destructive confirmation screen prevents the reviewed interaction'),
        dict(id='F02',path='jrnl/main.py',before=b'    return status_code\n',
             after=b'    return 7 if status_code is None else status_code\n',
             category='unexpected_exit',meaning='Successful deletion incorrectly exits 7 instead of 0'),
        dict(id='F03',path='jrnl/journals/Journal.py',before=b'        atomic_write(filename, text)\n',
             after=b'        atomic_write(filename, text.replace(b"Second body.", b"Second bodX.", 1))\n',
             category='state_assertion_failure',meaning='Same-size retained journal corruption after unchanged successful terminal summary and exit'),
    ]
    root=RAW/'jrnl/faults'/uuid.uuid4().hex;root.mkdir(parents=True)
    declaration=dict(schema_version=1,selected_after_freeze_sha256=sha256(freeze),
        exposure='Target source was reviewed for normal behavior. These concrete source edits were selected after twenty tests and positive development evidence were frozen; no independent human or untouched-source claim.',
        faults=[{k:(v.decode() if isinstance(v,bytes) else v) for k,v in f.items()} for f in faults])
    immutable_json(root/'planned.json',declaration)
    immutable_json(package/'fault-declaration.json',declaration)
    host='windows' if os.name=='nt' else 'linux'
    runner=RAW/'candidate'/host/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=environment(target);campaign=NextCampaign();observations=[]
    async def run(fault,phase):
        for name,digest in frozen['inputs'].items():
            if sha256(package/name)!=digest:raise ValueError('fault test was weakened')
        report=root/(fault['id']+'-'+phase+'.json')
        result=await execute([runner,'test','--report',report,'--artifacts-dir',root/(fault['id']+'-'+phase+'-evidence'),
            package/'normal-delete.json'],'jrnl','source-fault-'+fault['id']+'-'+phase,cwd=ROOT,env=env,
            timeout=140,expected=1 if phase=='mutated' else 0,campaign=campaign)
        row=json.loads(report.read_text())['results'][0]
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('fault cleanup not confirmed')
        category=row.get('failure',{}).get('category')
        if phase=='mutated':
            if row['status']!='failed' or category!=fault['category']:raise ValueError('actual mutation not rejected for declared reason')
            if fault['id']=='F03':
                index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                if not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('saved corruption failed an earlier terminal/exit step')
                if row['steps'][index]['state']['invocation_id']!=row['invocation_id']:raise ValueError('wrong-invocation saved corruption')
        elif row['status']!='passed':raise ValueError('baseline/restored target did not pass')
        return dict(phase=phase,attempt=result['id'],report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),
            status=row['status'],category=category,invocation=row['invocation_id'],target_cleanup=True,workspace_cleanup=True)
    for fault in faults:
        path=target/'src'/fault['path'];original=path.read_bytes()
        if original.count(fault['before'])!=1:raise ValueError('fault source anchor must be exact/unique')
        mutated=original.replace(fault['before'],fault['after'])
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/'+fault['path'],tofile='b/'+fault['path']))
        patch_path=package/'fault-patches'/(fault['id']+'.patch');patch_path.parent.mkdir(exist_ok=True)
        with patch_path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
        baseline=await run(fault,'baseline')
        try:
            path.write_bytes(mutated)
            mutated_hash=sha256(path)
            rejected=await run(fault,'mutated')
        finally:
            path.write_bytes(original)
            if path.read_bytes()!=original:raise ValueError('target source restoration failed')
        restored=await run(fault,'restored')
        observations.append(dict(id=fault['id'],source=fault['path'],original_sha256=__import__('hashlib').sha256(original).hexdigest(),
            mutated_sha256=mutated_hash,restored_sha256=sha256(path),restored_exact=True,
            patch_sha256=sha256(patch_path),outcomes=[baseline,rejected,restored]))
        print(fault['id'],'actual source regression rejected and exact source restored',flush=True)
    immutable_json(root/'summary.json',dict(schema_version=1,phase=campaign.phase,faults=observations,
        runner_sha256=sha256(runner),test_freeze_sha256=sha256(freeze),real_faults=3,calibrations=9,
        overall_project_admission_credit=0,build_scope='Editable interpreted Python: actual imported source changes, no compiled rebuild; executable/dependency/source identities captured before each invocation.'))
    print('Three real source faults / nine separate baseline-mutated-restored',campaign.phase,'calibrations; overall project admission remains independently audited.')


if __name__=='__main__':asyncio.run(main())
