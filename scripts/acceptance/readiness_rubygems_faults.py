"""Real source regressions, source identities, unchanged contracts and restoration."""
import argparse
import asyncio
import difflib
import hashlib
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import PACKAGE, environment, rows


def contract_names():
    return ['normal-gem.json','normal-extension.json','normal-build-gem.json']+[r[1] for r in rows()]


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);args=parser.parse_args()
    package=args.package.resolve() if args.package else PACKAGE
    package.relative_to(ROOT)
    contracts={name:sha256(package/name) for name in sorted(contract_names())}
    if len(contracts)!=20:raise RuntimeError('twenty complete reviewed contracts required')
    freeze=RAW/'rubygems/reviewed-contract-freeze-native.json' if args.package else package/'reviewed-contract-freeze.json'
    if not freeze.exists():immutable_json(freeze,dict(contracts=contracts,holdout_not_yet_selected=True,
        qualification='development freeze; quiet Windows resize remains excluded; actual pager resize is declared'))
    if json.loads(freeze.read_text())['contracts']!=contracts:raise RuntimeError('contract freeze changed')
    faults=[
        dict(id='F01',spec='normal-gem.json',path='bundler/cli/gem.rb',
             before='Enter a test framework. rspec/minitest/test-unit/(none):',
             after='Choose a test library. rspec/minitest/test-unit/(none):',held_out=False),
        dict(id='F02',spec='edge-build-missing.json',path='rubygems/commands/build_command.rb',
             before='terminate_interaction(1)',after='terminate_interaction(0)',held_out=False),
        dict(id='F03',spec='normal-gem.json',path='bundler/templates/newgem/lib/newgem/version.rb.tt',
             before='VERSION = "0.1.0"',after='VERSION = "0.1.1"',held_out=not bool(args.package))]
    root=RAW/'rubygems/faults'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'selected-faults.json',dict(frozen_contract_sha256=sha256(freeze),faults=faults,
        heldout_selection='replicas of original Windows F03' if args.package else 'F03 selected after reviewed twenty-contract freeze; agent authored'))
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    async def run(fault,phase,expected):
        report=root/(fault['id']+'-'+phase+'.json')
        result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            report.with_suffix('').relative_to(ROOT),(package/fault['spec']).relative_to(ROOT)],
            'rubygems',fault['id']+'-'+phase,env=environment(),expected=expected,timeout=130,campaign=Campaign())
        outcome=json.loads(report.read_text())['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:raise RuntimeError('unconfirmed fault cleanup')
        return result,outcome
    receipts=[]
    for fault in faults:
        source=RAW/'active/rubygems/src/lib'/fault['path'];original=source.read_bytes()
        if original.count(fault['before'].encode())!=1:raise RuntimeError('ambiguous real source patch')
        mutated=original.replace(fault['before'].encode(),fault['after'].encode())
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/lib/'+fault['path'],tofile='b/lib/'+fault['path']))
        (root/(fault['id']+'.patch')).write_text(patch,encoding='utf-8')
        baseline,_=await run(fault,'baseline',0)
        try:
            source.write_bytes(mutated)
            mutation,outcome=await run(fault,'mutated',1)
            if outcome['status']!='failed':raise RuntimeError('false green on actual fault')
            if fault['id']=='F03':
                assert outcome['failure']['category']=='state_assertion_failure'
                failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed')
                assert all(s['status']=='passed' for s in outcome['steps'][:failed])
                assert any(s['action']=='snapshot' for s in outcome['steps'][:failed])
                evidence=outcome['steps'][failed]['state']
                assert evidence['invocation_id']==evidence['workspace_id']==outcome['workspace']['id']
        finally:source.write_bytes(original)
        if source.read_bytes()!=original:raise RuntimeError('source restoration mismatch')
        restored,_=await run(fault,'restored',0)
        receipt=dict(**fault,baseline_attempt=baseline['id'],mutation_attempt=mutation['id'],
            restored_attempt=restored['id'],original_source_sha256=sha256(source),
            mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),restored_exact=True,
            same_execution_state_rejection=fault['id']=='F03')
        immutable_json(root/(fault['id']+'-receipt.json'),receipt);receipts.append(receipt)
        print(fault['id'],'detected and restored',flush=True)
    immutable_json(root/'summary.json',dict(faults=receipts,runner_sha256=sha256(runner),
        source_execution='actual pinned Ruby and ERB source loaded fresh by normal CLI; no wrapper or rebuild simulation'))
    print('Three actual RubyGems/Bundler source faults:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
