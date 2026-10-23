"""Run declared actual Python source faults against frozen reviewed contracts."""
import argparse
import asyncio
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--package',type=Path);args=parser.parse_args()
    canonical=DOC/args.project;package=(args.package or canonical).resolve();package.relative_to(ROOT)
    target=RAW/'active'/args.project
    if json.loads((target/'task-owned.json').read_text())['slug']!=args.project:raise ValueError('wrong active source fault target')
    declaration=json.loads((canonical/'fault-declaration.json').read_text());frozen=json.loads((package/'development-test-freeze.json').read_text())
    if declaration['selected_after_freeze_sha256']!=sha256(canonical/'development-test-freeze.json'):raise ValueError('source faults were not selected after this canonical freeze')
    faults=declaration['faults']
    if len(faults)!=3 or {f['id'] for f in faults}!={'F01','F02','F03'}:raise ValueError('three concrete source faults required')
    root=RAW/args.project/'faults'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'planned.json',dict(declaration_sha256=sha256(canonical/'fault-declaration.json'),
        actual_test_freeze_sha256=sha256(package/'development-test-freeze.json'),declaration=declaration))
    host='windows' if os.name=='nt' else 'linux';runner=RAW/'candidate'/host/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=environment(target);campaign=NextCampaign();observations=[]
    async def run(fault,phase):
        for name,digest in frozen['inputs'].items():
            if sha256(package/name)!=digest:raise ValueError('frozen contract/input changed before source calibration')
        selected=package/declaration['primary_spec']
        if phase=='terminal-only':
            derived=root/'terminal-only';derived.mkdir()
            spec=json.loads(selected.read_text());source_fixture=package/spec['workspace']['fixture']
            shutil.copytree(source_fixture,derived/'fixture')
            spec['workspace']['fixture']='fixture'
            spec['command'][0]=os.path.relpath(json.loads((target/'runtime.json').read_text())['python'],derived).replace('\\','/')
            spec['steps']=[s for s in spec['steps'] if 'state' not in s]
            immutable_json(derived/'spec.json',spec)
            immutable_json(derived/'derivation.json',dict(original_spec_sha256=sha256(selected),
                scope='Different deliberately terminal-only contract; state oracles removed only for this labeled calibration, zero ordinary credit.'))
            selected=derived/'spec.json'
        report=root/(fault['id']+'-'+phase+'.json')
        result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(fault['id']+'-'+phase+'-evidence')).relative_to(ROOT),selected.relative_to(ROOT)],
            args.project,'source-fault-'+fault['id']+'-'+phase,cwd=ROOT,env=env,timeout=140,
            expected=1 if phase=='mutated' else 0,campaign=campaign)
        row=json.loads(report.read_text())['results'][0]
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('fault cleanup unconfirmed')
        category=row.get('failure',{}).get('category')
        if phase=='mutated':
            if row['status']!='failed' or category!=fault['category']:raise ValueError('actual source mutation not rejected for declared reason')
            if fault['id']=='F03':
                index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                if not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('saved corruption failed before terminal/exit completion')
                if row['steps'][index]['state']['invocation_id']!=row['invocation_id']:raise ValueError('saved corruption evidence from another execution')
        elif row['status']!='passed' or any(s['status']!='passed' for s in row['steps']):raise ValueError('nonpositive pristine/recovery/terminal-only calibration')
        return dict(phase=phase,attempt=result['id'],report=report.relative_to(ROOT).as_posix(),
            report_sha256=sha256(report),spec_sha256=sha256(selected),status=row['status'],category=category,
            invocation=row['invocation_id'],target_cleanup=True,workspace_cleanup=True,ordinary_credit=0)
    for fault in faults:
        path=target/'src'/fault['path'];path.resolve(strict=True).relative_to((target/'src').resolve())
        original=path.read_bytes();before=fault['before'].encode();after=fault['after'].encode()
        if original.count(before)!=1:raise ValueError('source mutation anchor not exact/unique')
        mutated=original.replace(before,after)
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/'+fault['path'],tofile='b/'+fault['path']))
        patch_path=canonical/'fault-patches'/(fault['id']+'.patch');patch_path.parent.mkdir(exist_ok=True)
        if patch_path.exists():
            if patch_path.read_text(encoding='utf-8')!=patch:raise ValueError('declared source patch changed')
        else:
            with patch_path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
        phases=[await run(fault,'baseline')]
        try:
            path.write_bytes(mutated);mutated_sha256=sha256(path)
            phases.append(await run(fault,'mutated'))
            if fault.get('terminal_only_probe'):phases.append(await run(fault,'terminal-only'))
        finally:
            path.write_bytes(original)
            if path.read_bytes()!=original:raise ValueError('source exact restoration failed')
        phases.append(await run(fault,'restored'))
        observations.append(dict(id=fault['id'],source=fault['path'],original_sha256=hashlib.sha256(original).hexdigest(),
            mutated_sha256=mutated_sha256,restored_sha256=sha256(path),restored_exact=True,
            patch_sha256=sha256(patch_path),outcomes=phases))
        print(fault['id'],'real mutation rejected and restored; phases',len(phases),flush=True)
    immutable_json(root/'summary.json',dict(schema_version=1,project=args.project,phase=campaign.phase,faults=observations,
        runner_sha256=sha256(runner),test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        real_faults=3,calibrations=sum(len(f['outcomes']) for f in observations),ordinary_credit=0,
        terminal_only_scope='Explicitly different contract demonstrates false green; not an ordinary final execution.',
        build_scope='Editable interpreted source with actual prelaunch source/runtime/dependency identities; no compiled rebuild.'))
    print('Verified real source mutations, genuine restored recoveries and separately labeled terminal-only probe. No project admission.')


if __name__=='__main__':asyncio.run(main())
