"""Rebuild real Rclone source faults and prove unchanged-contract detection."""
import argparse
import asyncio
import hashlib
import os
import platform
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_rclone_native_contracts import native_profile,target_environment


def require(value,message):
    if not value:raise RuntimeError(message)


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--original-heldout',action='store_true');args=parser.parse_args()
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    selection=load(docs/'fault-selection.json')
    require(selection['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json'), 'fault freeze differs')
    if args.original_heldout:
        require(platform.system()=='Linux' and os.environ.get('GITHUB_ACTIONS')=='true'
                and not (docs/'original-source-faults.json').exists(),'original heldout is initial hosted Linux only')
    else:require((docs/'original-source-faults.json').is_file(),'replicas require preserved original Linux outcome')
    profile=native_profile();frozen=load(profile/'reviewed-contract-freeze.json');package=RAW/'rclone/host-contracts'
    def unchanged():
        for name,digest in frozen['all_package_inputs'].items():
            require(sha256(package/name)==digest,'fault changed approved contract/fixture')
    unchanged()
    target=RAW/'active/rclone';build=load(target/'build.json');runtime=load(target/'runtime.json')
    executable=target/build['binary_relative_path'];compiler=target/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
    require(sha256(compiler)==build['compiler_sha256']==runtime['compiler_sha256'],'owned compiler differs')
    original_binary=sha256(executable)
    require(original_binary==build['binary_sha256'],'initial compiled executable differs')
    env=target_environment();binary,candidate,cell=runner()
    root=RAW/'rclone/faults'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'selected-faults.json',dict(fault_selection_sha256=sha256(docs/'fault-selection.json'),
        native_freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),original_heldout=args.original_heldout,
        faults=selection['faults'],compiler_sha256=sha256(compiler),initial_binary_sha256=original_binary))
    async def compile(label):
        operation=asyncio.create_task(execute([compiler,'build','-p','2','-mod=readonly','-trimpath','-buildvcs=false',
            '-ldflags','-s -w','-o',executable,'.'],'rclone',label+'-actual-rebuild',cwd=target/'src',env=env,timeout=300,campaign=Campaign()))
        sizes=[]
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target);sizes.append(size)
                require(size<=3840*1024**2,'stop before four-GiB active limit')
                await asyncio.sleep(2)
            attempt=await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
            immutable_json(root/(label+'-storage.json'),dict(observed_active_bytes=sizes,scope='Periodic logical bytes, not exact peak.'))
        version=await execute([executable,'--config',target/'validation/unused.conf','version'],'rclone',label+'-version',
            cwd=target/'validation',env=env,timeout=30,campaign=Campaign())
        require(version['output'].splitlines()[0]=='rclone v1.76.0-DEV','mutated application cannot launch normal version route')
        return dict(attempt=attempt['id'],version_attempt=version['id'],binary_sha256=sha256(executable),compiler_sha256=sha256(compiler))
    async def run(fault,phase,expected):
        unchanged();report=root/(fault['id']+'-'+phase+'.json')
        result=await execute([binary,'test','--report',report,'--artifacts-dir',report.with_suffix(''),package/fault['spec']],
            'rclone',fault['id']+'-'+phase,env=env,expected=expected,timeout=140,campaign=Campaign())
        value=load(report);outcome=value['results'][0]
        require(value['runner_version']==candidate['version'] and outcome['cleanup']['confirmed_exited']
                and outcome['workspace']['cleaned'],'fault runner or cleanup differs')
        return result,outcome
    receipts=[]
    for fault in selection['faults']:
        source=target/'src'/fault['path'];original=source.read_bytes()
        require(sha256(source)==fault['original_source_sha256'] and original.count(fault['before'].encode())==1,'original mutation site differs')
        mutated=original.replace(fault['before'].encode(),fault['after'].encode())
        require(hashlib.sha256(mutated).hexdigest()==fault['mutated_source_sha256'],'reviewed mutation differs')
        baseline,_=await run(fault,'baseline',0)
        try:
            source.write_bytes(mutated)
            validation=await compile(fault['id']+'-mutated')
            require(validation['binary_sha256']!=original_binary,'fault did not change compiled executable')
            mutation,outcome=await run(fault,'mutated',1)
            require(outcome['status']=='failed' and outcome['failure']['category']==fault['category'],'wrong real source-fault diagnosis')
            if fault['id']=='F02':
                require(outcome['target']['exited'] and outcome['target']['exit_code']==0,'fault did not produce OS exit0')
            else:
                failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed');prior=outcome['steps'][:failed]
                require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                        and outcome['target']['exited'] and outcome['target']['exit_code']==0,'file fault lacks passing screen and exact exit0')
                state=outcome['steps'][failed]['state']
                require((state['kind'],state['path'])==(fault['state_kind'],fault['state_path'])
                        and state['invocation_id']==outcome['invocation_id'] and state['workspace_id']==outcome['workspace']['id'],
                        'wrong or cross-execution public state rejection')
                if fault['id']=='F03':require(sum(s.get('state',{}).get('kind')=='file' for s in prior)==2,
                                            'extra-file fault lacks earlier passing exact files')
        finally:
            source.write_bytes(original)
            restoration=await compile(fault['id']+'-restored')
        require(sha256(source)==fault['original_source_sha256'] and sha256(executable)==original_binary,
                'source or compiled binary not restored exactly')
        restored,_=await run(fault,'restored',0)
        receipt=dict(**fault,baseline_attempt=baseline['id'],mutation_attempt=mutation['id'],restored_attempt=restored['id'],
            mutation_validation=validation,restored_validation=restoration,restored_exact=True,
            original_heldout=bool(args.original_heldout and fault['id']=='F03'))
        immutable_json(root/(fault['id']+'-receipt.json'),receipt);receipts.append(receipt)
        print(fault['id'],'actual compiled source fault detected; original source and binary restored',flush=True)
    unchanged()
    immutable_json(root/'summary.json',dict(faults=receipts,runner_sha256=cell['binary_sha256'],provisional_archive_sha256=cell['archive_sha256'],
        original_binary_sha256=original_binary,compiler_sha256=sha256(compiler),source_revision=candidate['source_revision'],final_archive_credit=0))


if __name__=='__main__':asyncio.run(main())
