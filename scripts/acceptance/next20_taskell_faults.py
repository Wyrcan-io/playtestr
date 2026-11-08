"""Run Taskell's declared baseline/mutated/restored source-fault controls."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from next20_taskell_llvm import verify_tool_inventory
from readiness_evidence import immutable_json,sha256


def source_snapshot(source):
    """Hash pinned source while excluding Stack cache and Hpack's bound output."""
    files={};modes={}
    for path in source.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('Taskell fault source contains a linked path')
        if not path.is_file():continue
        relative=path.relative_to(source).as_posix()
        if relative=='.stack-work' or relative.startswith('.stack-work/'):
            continue
        if relative=='taskell.cabal':
            continue
        files[relative]=sha256(path)
        modes[relative]='100755' if path.stat().st_mode&stat.S_IXUSR else '100644'
    return files,modes


def generated_cabal_identity(source):
    """Bind Stack/Hpack's generated package file independently from pinned source."""
    source=Path(source)
    path=source/'taskell.cabal'
    package_yaml=source/'package.yaml'
    if (path.is_symlink() or getattr(path,'is_junction',lambda:False)() or not path.is_file() or
            package_yaml.is_symlink() or not package_yaml.is_file()):
        raise ValueError('Taskell Hpack generated inputs are missing, linked, or non-regular')
    size=path.stat().st_size
    if size<=0 or size>2*1024*1024:raise ValueError('Taskell generated cabal file exceeds its bound')
    return dict(path='taskell.cabal',bytes=size,sha256=sha256(path),mode=
        '100755' if path.stat().st_mode&stat.S_IXUSR else '100644',
        package_yaml_sha256=sha256(package_yaml),generator='Stack-managed Hpack output')


def verify_generated_cabal(source,expected):
    actual=generated_cabal_identity(source)
    if actual!=expected:
        raise ValueError('Taskell Hpack output differs from its independently bound build input')
    return actual


def source_files(source,provenance):
    """Require exact frozen file bytes and Git executable modes."""
    files,modes=source_snapshot(source)
    expected_files=provenance.get('files',{});expected_modes=provenance.get('git_modes',{})
    if files!=expected_files or modes!=expected_modes:
        actual_paths=set(files);expected_paths=set(expected_files)
        changed=sorted(path for path in actual_paths&expected_paths if files[path]!=expected_files[path])
        mode_changed=sorted(path for path in actual_paths&expected_paths
                            if modes.get(path)!=expected_modes.get(path))
        details=dict(missing=sorted(expected_paths-actual_paths)[:20],
            unexpected=sorted(actual_paths-expected_paths)[:20],
            changed_bytes=changed[:20],changed_modes=mode_changed[:20],
            missing_count=len(expected_paths-actual_paths),unexpected_count=len(actual_paths-expected_paths),
            changed_bytes_count=len(changed),changed_modes_count=len(mode_changed))
        raise ValueError('Taskell fault source differs from its pinned files/modes: '+
                         json.dumps(details,sort_keys=True,separators=(',',':')))
    return files


def file_map_hash(files):
    payload=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(payload).hexdigest()


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-series',choices=['native-exit-v1'],default='native-exit-v1')
    args=parser.parse_args()
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    package=DOC/'taskell'
    declaration_path=package/'fault-declaration-native-exit-v1.json'
    declaration=json.loads(declaration_path.read_text(encoding='utf-8'))
    if host not in declaration['hosts']:raise ValueError('Undeclared Taskell fault host')
    if declaration['candidate_series']!=args.candidate_series:raise ValueError('Fault candidate series differs')
    if sha256(package/'native-runtime-lock-native-exit-v1.json')!=declaration['runtime_lock_sha256']:
        raise ValueError('Taskell runtime-lock freeze changed')
    if sha256(package/'host-contracts/scenarios.json')!=declaration['scenario_freeze_sha256']:
        raise ValueError('Taskell scenario freeze changed')
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    if provenance['pin']!=declaration['source_pin']:raise ValueError('Taskell source pin changed')
    source=RAW/'active/taskell/src';target=RAW/'active/taskell'
    baseline_build=json.loads((target/'build.json').read_text(encoding='utf-8'))
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'))
    baseline=Path(runtime['native']).resolve(strict=True)
    baseline.resolve(strict=True).relative_to(target.resolve(strict=True))
    if sha256(baseline)!=baseline_build['binary_sha256'] or sha256(baseline)!=runtime['native_sha256']:
        raise ValueError('Taskell pristine runtime binary identity differs')
    if host=='darwin':
        manifest_path=ROOT/baseline_build.get('llvm_manifest_path','')
        if (not manifest_path.is_file() or sha256(manifest_path)!=baseline_build.get('llvm_manifest_sha256') or
                os.environ.get('TASKELL_LLVM_MANIFEST')!=str(manifest_path)):
            raise ValueError('Apple Silicon LLVM toolchain receipt differs from the pristine runtime build')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        prefix=Path(manifest['tool_prefix']).resolve(strict=True)
        verify_tool_inventory(prefix,manifest['files'])
    candidate=executable(args.candidate_series,host)
    canonical=package/'host-contracts'
    run_id=os.environ.get('GITHUB_RUN_ID') or uuid.uuid4().hex
    root=RAW/'taskell'/'fault-calibration-native-exit-v1'/run_id
    root.mkdir(parents=True,exist_ok=False)
    variants=target/'native-build'/'faults'/run_id
    variants.mkdir(parents=True,exist_ok=False)
    stack_root=os.environ.get('STACK_ROOT')
    if not stack_root:raise ValueError('Owned STACK_ROOT is required for native fault rebuilds')
    build_env=environment(target);build_env['STACK_ROOT']=stack_root
    if os.environ.get('STACK_YAML'):
        build_env['STACK_YAML']=os.environ['STACK_YAML']
    if os.environ.get('DYLD_LIBRARY_PATH'):
        build_env['DYLD_LIBRARY_PATH']=os.environ['DYLD_LIBRARY_PATH']
    campaign=NextCampaign(phase='fault-calibration')
    failures=[];results=[]
    generated_cabal=generated_cabal_identity(source)
    immutable_json(root/'generated-cabal-input.json',dict(schema_version=1,project='taskell',
        source_pin=provenance['pin'],**generated_cabal,
        scope='Stack/Hpack-generated package metadata is excluded from pinned Git-source identity but its exact bytes, mode and package.yaml input are bound across all fault rebuilds.'))

    async def build(label,output):
        bindir=output/'bin';bindir.mkdir(parents=True,exist_ok=False)
        verify_generated_cabal(source,generated_cabal)
        await execute(['stack','install','taskell','--local-bin-path',str(bindir)],'taskell',label,
            cwd=source,env=build_env,timeout=declaration['timeout_seconds'],output_cap=16*1024*1024,campaign=campaign)
        verify_generated_cabal(source,generated_cabal)
        binary=bindir/('taskell.exe' if os.name=='nt' else 'taskell')
        if not binary.is_file():raise ValueError(label+': expected native output missing')
        return binary.resolve(strict=True),sha256(binary)

    async def invoke(fault,phase,case_spec,binary,expected_exit):
        report=root/(fault+'-'+phase+'.report.json')
        evidence=root/(fault+'-'+phase+'-artifacts')
        env=environment(target);env['PATH']=str(binary.parent)+os.pathsep+env.get('PATH','')
        command=[candidate,'test','--report',report,'--artifacts-dir',evidence,canonical/case_spec]
        attempt=None;error=None;row=None
        try:
            attempt=await execute(command,'taskell','fault-'+fault+'-'+phase,cwd=ROOT,env=env,
                timeout=150,expected=expected_exit,campaign=campaign)
            data=json.loads(report.read_text(encoding='utf-8'))
            if len(data.get('results',[]))!=1:raise ValueError('Expected one Taskell calibration report result')
            row=data['results'][0]
            cleanup=bool(row.get('workspace',{}).get('cleaned') and row.get('cleanup',{}).get('confirmed_exited'))
            if not cleanup:raise RuntimeError('Taskell calibration cleanup was not confirmed')
            if phase in {'baseline','restored'}:
                if row.get('status')!='passed' or any(s.get('status')!='passed' for s in row.get('steps',[])):
                    raise ValueError(phase+' exact contract did not pass')
            else:
                if row.get('status')=='passed' or not any(s.get('status')!='passed' for s in row.get('steps',[])):
                    raise ValueError('Mutated Taskell target produced no observed contract rejection')
            record=dict(fault=fault,phase=phase,runner_exit=attempt['returncode'],expected_runner_exit=expected_exit,
                report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),invocation=row.get('invocation_id'),
                target_exit=next((s.get('target_exit_code') for s in row.get('steps',[]) if 'target_exit_code' in s),None),
                cleanup_confirmed=True,status='passed')
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            if report.is_file():
                try:
                    data=json.loads(report.read_text(encoding='utf-8'));row=data.get('results',[None])[0]
                except (ValueError,KeyError,IndexError):row=None
            cleanup=bool(row and row.get('workspace',{}).get('cleaned') and row.get('cleanup',{}).get('confirmed_exited'))
            record=dict(fault=fault,phase=phase,runner_exit=attempt['returncode'] if attempt else None,
                expected_runner_exit=expected_exit,report=report.relative_to(ROOT).as_posix(),
                report_sha256=sha256(report) if report.is_file() else None,
                invocation=row.get('invocation_id') if row else None,cleanup_confirmed=cleanup,
                status='failed',failure=error)
            if row is not None and not cleanup:raise RuntimeError('Unsafe Taskell fault invocation; process/workspace cleanup unconfirmed')
        immutable_json(root/(fault+'-'+phase+'.json'),record)
        return record

    for fault in declaration['faults']:
        pristine=source_files(source,provenance);pristine_hash=file_map_hash(pristine)
        file=source/fault['path'];original=file.read_bytes();before=fault['before'].encode('utf-8');after=fault['after'].encode('utf-8')
        if original.count(before)!=1:raise ValueError('Fault patch is not unique in pinned source: '+fault['id'])
        if hashlib.sha256(fault['before'].encode()+b'\0'+fault['after'].encode()).hexdigest()!=fault['patch_sha256']:
            raise ValueError('Fault declaration patch hash changed')
        rows=[]
        case_spec=fault['case']
        rows.append(await invoke(fault['id'],'baseline',case_spec,baseline,0))
        mutant_binary=None;mutant_sha=None;mutation_error=None
        try:
            file.write_bytes(original.replace(before,after,1))
            changed,changed_modes=source_snapshot(source)
            if set(changed)!=set(pristine) or changed_modes!=provenance['git_modes'] or changed==pristine:
                raise ValueError('Declared source mutation changed source scope/modes or failed to change source bytes')
            patch_record=dict(fault=fault['id'],source_path=fault['path'],pristine_file_sha256=hashlib.sha256(original).hexdigest(),
                mutated_file_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),pristine_source_manifest_sha256=pristine_hash,
                mutated_source_manifest_sha256=file_map_hash(changed),patch_sha256=fault['patch_sha256'],before=fault['before'],after=fault['after'])
            immutable_json(root/(fault['id']+'-patch.json'),patch_record)
            mutant_binary,mutant_sha=await build('fault-'+fault['id']+'-mutated-build',variants/fault['id']/'mutated')
            rows.append(await invoke(fault['id'],'mutated',case_spec,mutant_binary,1))
        except Exception as exc:
            mutation_error=type(exc).__name__+': '+str(exc)
            failures.append(dict(fault=fault['id'],phase='mutated',failure=mutation_error))
        finally:
            file.write_bytes(original)
        restored=source_files(source,provenance)
        if restored!=pristine:raise RuntimeError('Taskell source restoration failed after '+fault['id'])
        restored_binary=None;restored_sha=None
        try:
            restored_binary,restored_sha=await build('fault-'+fault['id']+'-restored-build',variants/fault['id']/'restored')
            rows.append(await invoke(fault['id'],'restored',case_spec,restored_binary,0))
        except Exception as exc:
            failures.append(dict(fault=fault['id'],phase='restored',failure=type(exc).__name__+': '+str(exc)))
        if mutation_error is None and len(rows)==3 and all(r['status']=='passed' for r in rows):
            status='passed'
        else:status='failed'
        result=dict(fault=fault['id'],case=case_spec,rows=rows,baseline_binary_sha256=sha256(baseline),
            mutated_binary_sha256=mutant_sha,restored_binary_sha256=restored_sha,
            source_restored=file_map_hash(restored)==pristine_hash,status=status,
            scope=fault['expected_mutation'])
        immutable_json(root/(fault['id']+'-summary.json'),result);results.append(result)
        if status!='passed' and not any(f.get('fault')==fault['id'] for f in failures):
            failures.append(dict(fault=fault['id'],phase='result',failure='Baseline/mutated/restored qualification incomplete'))
    final_generated_cabal=verify_generated_cabal(source,generated_cabal)
    final_source_restored=source_files(source,provenance)==provenance['files']
    immutable_json(root/'summary.json',dict(schema_version=1,project='taskell',host=host,workflow_run_id=run_id,
        declaration_sha256=sha256(declaration_path),candidate_sha256=sha256(candidate),source_pin=declaration['source_pin'],
        llvm_manifest_sha256=baseline_build.get('llvm_manifest_sha256'),
        calibrated_phases=sum(len(r['rows']) for r in results),required_phases=declaration['calibrations_per_host'],
        results=results,failures=failures,source_restored=final_source_restored,
        generated_cabal=final_generated_cabal,
        project_admissions=0,scope='Three source faults with unchanged exact contracts, private archived runner and confirmed cleanup; not project admission.'))
    if failures:raise ValueError('Taskell source fault calibration failed; all safely restored outcomes retained')
    print(host,'Taskell exact candidate source-fault phases passed:',len(results),'faults,',sum(len(r['rows']) for r in results),'executions',flush=True)


if __name__=='__main__':asyncio.run(main())
