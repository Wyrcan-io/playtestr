"""Three minimal real upstream faults, unchanged tests, exact finally restoration."""
import asyncio
import argparse
import difflib
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path)
    args=parser.parse_args()
    package=args.package.resolve() if args.package else ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry'
    package.relative_to(ROOT)
    contract_names=['normal-init.json','normal-build-sdist.json']
    from readiness_poetry_cases import rows
    contract_names += [row[1] for row in rows()]
    freeze=(RAW/'poetry/reviewed-contract-freeze-native.json') if args.package else package/'reviewed-contract-freeze.json'
    contracts={name:sha256(package/name) for name in sorted(contract_names)}
    if len(contracts)!=20:raise RuntimeError('twenty reviewed contracts required')
    if not freeze.exists():
        immutable_json(freeze,dict(contracts=contracts,qualification='development freeze; Windows E05 remains red; native and final archive qualification open',
                                  holdout_not_yet_selected=True))
    if json.loads(freeze.read_text())['contracts']!=contracts:raise RuntimeError('reviewed contract freeze changed')
    faults=[
      dict(id='F01',spec='normal-init.json',path='console/commands/init.py',
           before='f"Version [<comment>{version}</comment>]: "',after='f"Release revision [<comment>{version}</comment>]: "',held_out=False),
      dict(id='F02',spec='normal-source-remove.json',path='console/commands/source/remove.py',
           before='if source.name.lower() == lower_name:',after='if source.name.lower() != lower_name:',held_out=False),
      dict(id='F03',spec='normal-version.json',path='console/commands/version.py',
           before='project_content["version"] = version.text',after='project_content["version"] = self.poetry.package.pretty_version',held_out=not bool(args.package))]
    receipt_root=RAW/'poetry/faults'/uuid.uuid4().hex;receipt_root.mkdir(parents=True)
    immutable_json(receipt_root/'selected-faults.json',dict(frozen_contracts_sha256=sha256(freeze),faults=faults,
        heldout_selection='Native replicas of original Windows F03' if args.package else 'F03 selected after immutable reviewed-contract freeze; agent-authored, not independent human review'))
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env['PATH']
    receipts=[]
    async def run(fault,phase,expected):
        report=receipt_root/(fault['id']+'-'+phase+'.json')
        result=await execute([runner,'test','--artifacts-dir',report.with_suffix('').relative_to(ROOT),
            '--report',report.relative_to(ROOT),(package/fault['spec']).relative_to(ROOT)],
            'poetry',fault['id']+'-'+phase,env=env,expected=expected,timeout=130,campaign=Campaign())
        data=json.loads(report.read_text())['results'][0]
        if not data['cleanup']['confirmed_exited'] or not data['workspace']['cleaned']:raise RuntimeError('fault cleanup unconfirmed')
        return result,data
    for fault in faults:
        source=RAW/'active/poetry/src/src/poetry'/fault['path'];original=source.read_bytes()
        before=fault['before'].encode();after=fault['after'].encode()
        if original.count(before)!=1:raise RuntimeError('ambiguous source patch')
        mutated=original.replace(before,after)
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
                                         fromfile='a/src/poetry/'+fault['path'],tofile='b/src/poetry/'+fault['path']))
        (receipt_root/(fault['id']+'.patch')).write_text(patch,encoding='utf-8')
        baseline,_=await run(fault,'baseline',0)
        try:
            source.write_bytes(mutated)
            mutation,outcome=await run(fault,'mutated',1)
            if outcome['status']!='failed':raise RuntimeError('unchanged test missed real fault')
            if fault['id']=='F03':
                assert outcome['failure']['category']=='state_assertion_failure'
                assert all(s['status']=='passed' for s in outcome['steps'][:2])
                state=outcome['steps'][2]['state']
                assert state['invocation_id']==state['workspace_id']==outcome['workspace']['id']
        finally:
            source.write_bytes(original)
        if source.read_bytes()!=original:raise RuntimeError('source restoration mismatch')
        restored,_=await run(fault,'restored',0)
        import hashlib
        receipts.append(dict(**fault,baseline_attempt=baseline['id'],mutation_attempt=mutation['id'],
            restored_attempt=restored['id'],original_source_sha256=sha256(source),
            mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),restored_exact=True,
            same_execution_state_rejection=fault['id']=='F03'))
        immutable_json(receipt_root/(fault['id']+'-receipt.json'),receipts[-1])
    immutable_json(receipt_root/'summary.json',dict(faults=receipts,runner_sha256=sha256(runner),
        source_execution='Reviewed editable Python source, bytecode writing disabled; no stale rebuild or wrapper simulation'))
    print('Three actual Poetry source faults detected and exactly restored:',receipt_root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
