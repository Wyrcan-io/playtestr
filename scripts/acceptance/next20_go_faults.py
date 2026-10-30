"""Compile declared real Go mutations and calibrate unchanged frozen contracts."""
import argparse
import asyncio
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_candidate import executable
from next20_cargo_faults import NativeFaultCampaign
from next20_check import DOC,RAW,ROOT,NextCampaign
from next20_python_setup import environment as target_environment
from readiness_build_rclone import environment as build_environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--final',action='store_true');parser.add_argument('--package',type=Path);args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go fault project')
    canonical=DOC/project;package=(args.package or canonical).resolve();package.relative_to(ROOT);target=RAW/'active'/project;source=target/'src';phase='final-archive' if args.final else 'development'
    freeze=json.loads((package/'development-test-freeze.json').read_text());rule_path=canonical/'fault-declaration.json';declaration=json.loads(rule_path.read_text())
    if declaration['selected_after_freeze_sha256']!=sha256(canonical/'development-test-freeze.json') or len(declaration['faults'])!=3:raise ValueError('faults not selected after exact canonical freeze')
    build=json.loads((target/'build.json').read_text());runtime=json.loads((target/'runtime.json').read_text());app=Path(runtime['target']);capture=Path(runtime['native'])
    primary=json.loads((canonical/'source-provenance.json').read_text())['files'];catalog=json.loads((target/'dependency-source-catalog.json').read_text());review=json.loads((canonical/'dependency-source-review-declaration.json').read_text());fetch=json.loads((target/'module-fetch.json').read_text())
    root=RAW/project/'faults'/uuid.uuid4().hex;root.mkdir(parents=True);variants=target/'fault-builds'/root.name;variants.mkdir(parents=True)
    original_binary=variants/('original-'+app.name);shutil.copyfile(app,original_binary)
    immutable_metadata={p:sha256(p) for p in [target/'build.json',target/'runtime.json',target/'installed-inventory.json']}
    def contracts():
        for name,digest in freeze['inputs'].items():
            if sha256(package/name)!=digest:raise ValueError('frozen Go fault contract/input changed')
    def source_bytes(expected):
        for name,digest in primary.items():
            if sha256(source/name)!=expected.get(name,digest):raise ValueError('actual Go primary source differs from declared fault/restoration')
        for name,digest in catalog['files'].items():
            if not name.startswith('src/') and sha256(target/name)!=digest:raise ValueError('reviewed Go module source changed')
        if any(sha256(p)!=d for p,d in immutable_metadata.items()) or sha256(capture)!=build['binary_sha256'] or sha256(fetch['compiler'])!=build['compiler_sha256']:raise ValueError('baseline build/runtime/compiler/capture metadata changed')
    def pristine():
        source_bytes({})
        if sha256(app)!=build['actual_target_sha256']:raise ValueError('ordinary actual target executable not restored exactly')
    contracts();pristine();env=build_environment(target);env.update(GOENV='off',GOPROXY='off',GOSUMDB='off',GONOPROXY='none',GONOSUMDB='none');target_env=target_environment(target);runner=executable('native-exit-v1');faults=[]
    immutable_json(root/'planned.json',dict(schema_version=1,phase=phase,fault_declaration_sha256=sha256(rule_path),actual_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        pristine_target_binary_sha256=sha256(app),capture_fixture_sha256=sha256(capture),calibrations=9,scope='Three real source-compiled mutation triples; original source and original compiled executable bytes restored exactly. Restored phases use the original reviewed executable,not a falsely claimed new rebuild.'))
    async def run_case(fault,stage,receipt=None):
        contracts();spec=package/declaration['primary_spec'];report=root/(fault['id']+'-'+stage+'.report.json')
        actual_files={p.name:sha256(p) for p in app.parent.iterdir() if p.is_file()}
        launch=dict(schema_version=1,runtime_root=app.parent.relative_to(ROOT).as_posix(),files=actual_files,actual_target_sha256=sha256(app),capture_sha256=sha256(capture),phase=stage,fault=fault['id'])
        encoded=(json.dumps(launch,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode();launch_path=root/(fault['id']+'-'+stage+'-runtime.json');launch_path.write_bytes(encoded);(target/'launch-runtime-catalog.json').write_bytes(encoded)
        inputs=[package/name for name in freeze['inputs']]+[rule_path,canonical/'development-test-freeze.json',target/'build.json',target/'runtime.json',launch_path]
        campaign=NativeFaultCampaign(app,receipt,inputs,phase=phase) if receipt else NextCampaign(phase=phase)
        observed=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/(fault['id']+'-'+stage+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],project,
            'go-real-source-'+fault['id']+'-'+stage,cwd=ROOT,env=target_env,timeout=140,expected=1 if stage=='mutated' else 0,campaign=campaign)
        result=json.loads(report.read_text())['results'][0];mutated=stage=='mutated'
        if result['status']!=('failed' if mutated else 'passed') or result.get('failure',{}).get('category')!=(fault['category'] if mutated else None):raise ValueError('Go source mutation outcome differs from declaration')
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:raise ValueError('Go fault target/workspace cleanup incomplete')
        if mutated and fault['id']=='F03':
            index=next(i for i,s in enumerate(result['steps']) if s['status']=='failed')
            if result['steps'][index]['action']!='state' or json.loads(spec.read_text())['steps'][index]['state']['path']!='selected.txt' or not all(s['status']=='passed' for s in result['steps'][:index]) or not {'expect','snapshot','exit'}<=set(s['action'] for s in result['steps'][:index]):raise ValueError('saved output corruption failed before normal UI/snapshot/exit completion')
        return dict(phase=stage,attempt=observed['id'],report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),spec_sha256=sha256(spec),status=result['status'],category=result.get('failure',{}).get('category'),
            invocation=result['invocation_id'],actual_target_binary_sha256=sha256(app),capture_fixture_sha256=sha256(capture),runtime_catalog=launch_path.relative_to(ROOT).as_posix(),runtime_catalog_sha256=sha256(launch_path),target_cleanup=True,workspace_cleanup=True)
    for fault in declaration['faults']:
        pristine();baseline=await run_case(fault,'baseline');path=source/fault['path'];original=path.read_bytes();before=fault['before'].encode();after=fault['after'].encode()
        if original.count(before)!=1 or sha256(path)!=fault['original_source_sha256']:raise ValueError('declared Go source anchor changed')
        receipt=root/(fault['id']+'-compiled.json');variant=variants/(fault['id']+'-'+app.name)
        try:
            path.write_bytes(original.replace(before,after));source_bytes({fault['path']:fault['mutated_source_sha256']})
            patch=''.join(difflib.unified_diff(original.decode().splitlines(True),path.read_text().splitlines(True),fromfile=fault['path'],tofile=fault['path']))
            (root/(fault['id']+'.patch')).write_text(patch,encoding='utf-8',newline='\n')
            command=[fetch['compiler'],'build',*review['build_flags'],'-modfile='+str(target/'build-inputs/pinned.mod'),'-o',str(variant),review['main_package']]
            compiled=await execute(command,project,'compile-real-go-source-mutation-'+fault['id'],cwd=source,env=env,timeout=180,campaign=NextCampaign(phase=phase))
            source_bytes({fault['path']:fault['mutated_source_sha256']})
            if sha256(variant)==build['actual_target_sha256']:raise ValueError('source mutation did not produce a distinct actual executable')
            sources={('src/'+name):sha256(source/name) for name in primary}
            sources.update({name:sha256(target/name) for name in catalog['actual_native_compile_inputs']});sources[capture.relative_to(target).as_posix()]=sha256(capture)
            immutable_json(receipt,dict(schema_version=1,compile_attempt=compiled['id'],command=list(map(str,command)),binary=variant.relative_to(ROOT).as_posix(),binary_sha256=sha256(variant),binary_bytes=variant.stat().st_size,
                compiler_sha256=build['compiler_sha256'],compiler_tools=build['compiler_tools'],pristine_build_sha256=sha256(target/'build.json'),fault_declaration_sha256=sha256(rule_path),
                source_inputs={(target/name).relative_to(ROOT).as_posix():d for name,d in sources.items()},dependency_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
                effective_go_mod_sha256=sha256(target/'build-inputs/pinned.mod'),effective_go_sum_sha256=sha256(target/'build-inputs/pinned.sum'),capture_fixture_sha256=sha256(capture)))
            shutil.copyfile(variant,app);mutated=await run_case(fault,'mutated',receipt)
        finally:
            path.write_bytes(original);shutil.copyfile(original_binary,app);pristine()
        restored=await run_case(fault,'restored');faults.append(dict(id=fault['id'],source=fault['path'],original_sha256=fault['original_source_sha256'],mutated_sha256=fault['mutated_source_sha256'],restored_sha256=sha256(path),restored_exact=True,
            original_binary_sha256=build['actual_target_sha256'],mutated_binary_sha256=sha256(variant),restored_binary_sha256=sha256(app),compiled_receipt=receipt.relative_to(ROOT).as_posix(),compiled_receipt_sha256=sha256(receipt),outcomes=[baseline,mutated,restored]))
        immutable_json(root/(fault['id']+'-complete.json'),faults[-1]);print(fault['id'],'actual baseline passed / compiled source mutation rejected / exact restoration passed',flush=True)
    contracts();pristine();immutable_json(root/'summary.json',dict(schema_version=1,project=project,phase=phase,real_faults=3,calibrations=9,faults=faults,ordinary_credit=0,project_admissions=0,source_and_binary_restored_exact=True))
    print('Three actual Go source faults detected;9fresh calibration phases; complete original source/executable restoration. No admission.')


if __name__=='__main__':asyncio.run(main())
