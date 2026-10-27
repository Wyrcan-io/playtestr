"""Compile actual upstream mutations and test unchanged frozen contracts."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment as target_environment
from next20_rust_fetch import environment,short_owned_path,materialize_short_cache
from readiness_evidence import Campaign,immutable_json,sha256
from readiness_build_plop import usage


class NativeFaultCampaign(NextCampaign):
    """Bind a deliberate compiled variant separately from pristine runtime metadata."""
    def __init__(self,variant,receipt,inputs):
        super().__init__(phase='development');self.variant=variant;self.receipt=receipt;self.inputs=inputs

    def identity(self,project,argv):
        value=json.loads(self.receipt.read_text())
        if sha256(self.variant)!=value['binary_sha256']:raise ValueError('actual fault executable differs from compile receipt')
        for name,digest in value['source_inputs'].items():
            if sha256(ROOT/name)!=digest:raise ValueError('actual fault source differs from compile receipt')
        # Pristine runtime/build receipts are immutable. The explicit fault
        # catalog binds the intentional variant; never relabel it as pristine.
        reference=Campaign.identity(self,project,[*argv,*self.inputs,self.receipt,self.variant])
        manifest=json.loads((RAW/reference['manifest']).read_text())
        manifest['native_source_fault']=dict(build_receipt=self.receipt.relative_to(ROOT).as_posix(),
            build_receipt_sha256=sha256(self.receipt),actual_executable=self.variant.relative_to(ROOT).as_posix(),
            actual_executable_sha256=sha256(self.variant),source_inputs=value['source_inputs'])
        output=RAW/'identities'/(uuid.uuid4().hex+'-native-fault.json');immutable_json(output,manifest)
        return dict(manifest=output.relative_to(RAW).as_posix(),sha256=sha256(output))


async def main():
    project='cargo-generate';package=DOC/project;target=RAW/'active'/project;source=target/'src'
    freeze_path=package/'development-test-freeze.json';freeze=json.loads(freeze_path.read_text())
    declaration_path=package/'fault-declaration.json';declaration=json.loads(declaration_path.read_text())
    if declaration['selected_after_freeze_sha256']!=sha256(freeze_path):raise ValueError('faults not selected against this exact freeze')
    review=json.loads((package/'source-review.json').read_text());build_path=target/'build.json';build=json.loads(build_path.read_text())
    runtime_path=target/'runtime.json';runtime=json.loads(runtime_path.read_text());binary=Path(runtime['native'])
    if sha256(binary)!=build['binary_sha256'] or runtime['native_sha256']!=build['binary_sha256']:raise ValueError('pristine native build differs')
    immutable_metadata={p:sha256(p) for p in [build_path,runtime_path,target/'installed-inventory.json']}
    runner=executable('native-exit-v1');root=RAW/project/'source-fault-development/v1'
    if root.exists():raise ValueError('preserve original fault probes; no automatic retries')
    root.mkdir(parents=True);variants=target/'fault-builds/v1';variants.mkdir(parents=True,exist_ok=False)
    original_binary=variants/'original'/binary.name;original_binary.parent.mkdir();shutil.copyfile(binary,original_binary)
    if sha256(original_binary)!=build['binary_sha256']:raise ValueError('pristine executable backup differs')
    inputs=[package/name for name in freeze['inputs']]+[declaration_path,freeze_path,build_path,runtime_path]
    dependencies=json.loads((target/'dependency-fetch-review.json').read_text());catalog=json.loads((target/'dependency-source-catalog.json').read_text())
    def contracts():
        for name,digest in freeze['inputs'].items():
            if sha256(package/name)!=digest:raise ValueError('frozen fault oracle changed')
    def pristine():
        for name,digest in review['reviewed_inputs'].items():
            if sha256(source/name)!=digest:raise ValueError('pristine source restoration differs')
        if sha256(binary)!=build['binary_sha256']:raise ValueError('pristine executable restoration differs')
        if any(sha256(p)!=h for p,h in immutable_metadata.items()):raise ValueError('pristine runtime/build metadata changed')
    def dependency_bytes():
        for name,digest in catalog['files'].items():
            if sha256(target/name)!=digest:raise ValueError('reviewed dependency source changed')
        for name,row in dependencies['files'].items():
            if sha256(target/name)!=row['sha256']:raise ValueError('reviewed dependency archive changed')
    contracts();pristine();dependency_bytes()
    compiler=Path(build['compiler_path']);cargo=Path(build['cargo_path'])
    if sha256(compiler)!=build['compiler_sha256'] or sha256(cargo)!=build['cargo_sha256']:raise ValueError('read-only compiler changed')
    env=environment(target);env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc.exe' if os.name=='nt' else 'rustdoc')),
        CARGO_NET_OFFLINE='true',SOURCE_DATE_EPOCH='1793030400')
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    if os.name=='nt':
        env['CARGO_HOME']=str(materialize_short_cache(target,dependencies,catalog))
        for key in ['CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR']:env[key]=short_owned_path(env[key])
    command=[cargo,'rustc','--locked','--offline','--release','--target',build['native_triple'],'--bin','cargo-generate']
    if os.name=='nt':command+=['--','-C','link-arg=/Brepro']
    target_env=target_environment(target);observations=[]
    async def compile_variant(fault):
        task=asyncio.create_task(execute(command,project,'cargo-real-source-fault-compile-'+fault['id'],
            cwd=Path(short_owned_path(source)),env=env,timeout=1100,campaign=NextCampaign(phase='development')))
        samples=[]
        try:
            while not task.done():
                size=await asyncio.to_thread(usage,RAW);samples.append(size)
                if size>3*1024**3:raise ValueError('fault compiler owned raw storage stop')
                await asyncio.sleep(2)
            return await task
        finally:
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
            immutable_json(root/(fault['id']+'-build-storage.json'),dict(observed_raw_bytes=samples,
                stop_bytes=3*1024**3,scope='Periodic logical samples, not exact peak, allocation or quota.'))
    async def run_case(fault,phase,variant_receipt=None):
        contracts();report=root/(fault['id']+'-'+phase+'.report.json')
        campaign=NativeFaultCampaign(binary,variant_receipt,inputs) if variant_receipt else NextCampaign(phase='development')
        result=await execute([runner,'test','--report',report,'--artifacts-dir',root/(fault['id']+'-'+phase+'-evidence'),
            package/fault['spec']],project,'cargo-source-fault-'+fault['id']+'-'+phase,cwd=ROOT,env=target_env,
            timeout=140,expected=1 if phase=='mutated' else 0,campaign=campaign)
        data=json.loads(report.read_text());row=data['results'][0];category=row.get('failure',{}).get('category')
        if row['status']!=('failed' if phase=='mutated' else 'passed') or category!=(fault['category'] if phase=='mutated' else None):raise ValueError('source fault outcome differs from declaration')
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('fault target/workspace cleanup incomplete')
        if fault['id']=='F03' and phase=='mutated':
            first=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
            state=row['steps'][first]['state']
            if not all(s['status']=='passed' for s in row['steps'][:first]) or state['invocation_id']!=row['invocation_id'] or state['workspace_id']!=row['workspace']['id']:
                raise ValueError('saved corruption was not isolated after successful terminal/exit assertions')
        return dict(phase=phase,attempt=result['id'],report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),
            status=row['status'],category=category,invocation=row['invocation_id'],runner_sha256=sha256(runner),
            actual_target_binary_sha256=sha256(binary),target_cleanup=True,workspace_cleanup=True)
    for fault in declaration['faults']:
        pristine();contracts();baseline=await run_case(fault,'baseline')
        path=source/fault['path'];original=path.read_bytes()
        if sha256(path)!=fault['original_source_sha256'] or original.count(fault['before'].encode())!=1:raise ValueError('fault source anchor changed')
        try:
            path.write_bytes(original.replace(fault['before'].encode(),fault['after'].encode()))
            if sha256(path)!=fault['mutated_source_sha256']:raise ValueError('actual upstream mutation differs')
            compiled=await compile_variant(fault)
            expected=dict(review['reviewed_inputs']);expected[fault['path']]=fault['mutated_source_sha256']
            if any(sha256(source/name)!=digest for name,digest in expected.items()):raise ValueError('actual compiled source differs from the one declared mutation')
            output=target/'cargo-target'/build['native_triple']/'release'/binary.name
            variant=variants/fault['id']/binary.name;variant.parent.mkdir();shutil.copyfile(output,variant)
            if sha256(variant)!=sha256(output) or sha256(variant)==build['binary_sha256']:raise ValueError('fault did not produce a distinct actual executable')
            variant_receipt=root/(fault['id']+'-compiled.json')
            immutable_json(variant_receipt,dict(schema_version=1,fault=fault['id'],compile_attempt=compiled['id'],command=list(map(str,command)),
                binary=variant.relative_to(ROOT).as_posix(),binary_sha256=sha256(variant),binary_bytes=variant.stat().st_size,
                compiler_sha256=sha256(compiler),cargo_sha256=sha256(cargo),pristine_build_sha256=sha256(build_path),
                fault_declaration_sha256=sha256(declaration_path),source_inputs={
                    (source/name).relative_to(ROOT).as_posix():sha256(source/name) for name in review['reviewed_inputs']},
                dependency_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
                dependency_fetch_receipt_sha256=sha256(target/'dependency-fetch-review.json')))
            shutil.copyfile(variant,binary);rejected=await run_case(fault,'mutated',variant_receipt)
        finally:
            path.write_bytes(original);shutil.copyfile(original_binary,binary);pristine()
        restored=await run_case(fault,'restored');observations.append(dict(fault=fault['id'],baseline=baseline,mutated=rejected,restored=restored,
            compiled_receipt=variant_receipt.relative_to(ROOT).as_posix(),compiled_receipt_sha256=sha256(variant_receipt)))
        immutable_json(root/(fault['id']+'-complete.json'),observations[-1]);print(fault['id'],'baseline passed / compiled mutation rejected / exact restoration passed',flush=True)
    contracts();pristine();dependency_bytes()
    if os.name=='nt':materialize_short_cache(target,dependencies,catalog)
    immutable_json(root/'summary.json',dict(schema_version=1,observations=observations,actual_source_faults=3,
        exploratory_executions=9,mandatory_final_native_calibration_credit=0,project_credits=0,
        scope='Local real source-fault exploration. Exact native final series must repeat the declared calibration triples. Original runtime/build receipts and source/executable bytes restored.'))
    print('Three real source mutations detected by unchanged contracts; pristine source and executable restored.')


if __name__=='__main__':asyncio.run(main())
