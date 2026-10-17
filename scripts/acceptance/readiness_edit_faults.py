"""Real rebuilt editor mutations against frozen, unchanged public contracts."""
import argparse
import asyncio
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from adversarial_process import execute
from readiness_edit_cases import environment
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    package=(args.package or RAW/'edit/contracts').resolve();package.relative_to(ROOT)
    frozen=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/reviewed-contract-freeze.json'
    freeze=json.loads(frozen.read_text(encoding='utf-8-sig'))
    # Native profiles may relocate runtime settings, but never change actions or baselines.
    canonical=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/contracts'
    for name,digest in freeze['contracts'].items():
        if sha256(canonical/name)!=digest:raise RuntimeError('canonical contract changed after freeze')
        original=json.loads((canonical/name).read_text(encoding='utf-8-sig'))
        current=json.loads((package/name).read_text(encoding='utf-8-sig'))
        if original['steps']!=current['steps']:raise RuntimeError('fault run changed frozen actions')
    faults=[
        dict(id='F01',spec='N01.json',path='i18n/edit.toml',before='[File]\nen = "File"',
             after='[File]\nen = "Files"',held_out=False,category='snapshot_mismatch'),
        dict(id='F02',spec='N02.json',path='crates/edit/src/bin/edit/main.rs',
             before='Ok(()) => process::ExitCode::SUCCESS,',after='Ok(()) => process::ExitCode::from(7),',
             held_out=False,category='unexpected_exit'),
        dict(id='F03',spec='N01.json',path='crates/edit/src/bin/edit/documents.rs',
             before='            tb.write_file(&mut file)?;',
             after='            tb.write_file(&mut file)?;\n            file.set_len(file.metadata()?.len().saturating_sub(1))?;',
             held_out=not bool(args.package),category='state_assertion_failure')]
    root=RAW/'edit/faults'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'selected-faults.json',dict(frozen_contract_sha256=sha256(frozen),faults=faults,
        selection='Native replicas; original heldout consumed.' if args.package else
            'F03 selected after twenty-contract freeze and committed checkpoint 9e5ce70; agent authored.',
        actual_build='Every mutated and restored Rust source is rebuilt offline through the ordinary stable release build.'))
    runner=RAW/('bin/playtestr'+('.exe' if os.name=='nt' else '')) if args.package else RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    binary=RAW/'active/edit'/json.loads((RAW/'active/edit/build.json').read_text())['binary_relative_path']
    async def build(label,version_exit=0):
        result=await execute([sys.executable,'scripts/acceptance/readiness_build_edit.py','--label',label,
            '--version-exit-code',str(version_exit)],'edit',label+'-build-parent',timeout=920,campaign=Campaign())
        return dict(attempt=result['id'],binary_sha256=sha256(binary))
    async def run(fault,phase,expected):
        report=root/(fault['id']+'-'+phase+'.json')
        result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            report.with_suffix('').relative_to(ROOT),(package/fault['spec']).relative_to(ROOT)],
            'edit',fault['id']+'-'+phase,env=environment(),expected=expected,timeout=150,campaign=Campaign())
        outcome=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('unconfirmed fault cleanup')
        return result,outcome
    receipts=[]
    for fault in faults:
        source=RAW/'active/edit/src'/fault['path'];original=source.read_bytes()
        # Upstream source archive bytes are LF; never normalize the restored source.
        before=fault['before'].encode();after=fault['after'].encode()
        if original.count(before)!=1:raise RuntimeError('ambiguous actual source patch')
        mutated=original.replace(before,after)
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/'+fault['path'],tofile='b/'+fault['path']))
        (root/(fault['id']+'.patch')).write_text(patch,encoding='utf-8',newline='\n')
        baseline,_=await run(fault,'baseline',0)
        baseline_binary=sha256(binary)
        try:
            source.write_bytes(mutated)
            mutation_build=await build(fault['id'].lower()+'-mutated',7 if fault['id']=='F02' else 0)
            if mutation_build['binary_sha256']==baseline_binary:raise RuntimeError('mutation did not change actual executable')
            mutation,outcome=await run(fault,'mutated',1)
            if outcome['status']!='failed' or outcome['failure']['category']!=fault['category']:
                raise RuntimeError('wrong actual fault diagnosis: '+json.dumps(outcome.get('failure')))
            if fault['id']=='F03':
                failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed')
                prior=outcome['steps'][:failed]
                if not all(s['status']=='passed' for s in prior):raise RuntimeError('earlier F03 failure')
                if not {'snapshot','exit'}<={s['action'] for s in prior}:raise RuntimeError('F03 lacked passing screen and exit')
                state=outcome['steps'][failed]['state']
                if state['invocation_id']!=outcome['invocation_id'] or state['workspace_id']!=outcome['workspace']['id']:
                    raise RuntimeError('F03 cross-execution state')
        finally:
            source.write_bytes(original)
            restored_build=await build(fault['id'].lower()+'-restored')
        if source.read_bytes()!=original:raise RuntimeError('source restoration mismatch')
        restored,_=await run(fault,'restored',0)
        receipt=dict(**fault,baseline_attempt=baseline['id'],baseline_binary_sha256=baseline_binary,
            mutation_attempt=mutation['id'],restored_attempt=restored['id'],mutation_build=mutation_build,
            restored_build=restored_build,original_source_sha256=sha256(source),
            mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),restored_exact=True,
            same_execution_state_rejection=fault['id']=='F03')
        immutable_json(root/(fault['id']+'-receipt.json'),receipt);receipts.append(receipt)
        print(fault['id'],'actual rebuilt source fault detected and restored',flush=True)
    immutable_json(root/'summary.json',dict(faults=receipts,runner_sha256=sha256(runner),
        source_execution='actual pinned Rust source and ordinary rebuilt native editor executable'))
    print('Three real rebuilt editor faults:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
