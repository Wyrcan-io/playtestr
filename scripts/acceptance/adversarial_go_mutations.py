"""Actual pinned Go application faults, rebuilds, and unchanged-contract recovery."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from adversarial_process import ROOT, DOC, RAW, run
from adversarial_journey import recorder
from adversarial_setup_go import build


def main(*,rust=False,c=False):
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--binary',type=Path,required=True)
    args=parser.parse_args()
    package=DOC/args.project
    app=args.runtime or ROOT/'.cache/ten-new-project-apps'/args.project
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    if rust and c:raise RuntimeError('Choose exactly one compiled target backend')
    if c:
        from adversarial_setup_c import build as c_build
        if not identity.get('toolchain','').startswith('C compiler: '):
            raise RuntimeError('C mutation adapter requires an identified C target')
        def build_target(directory,project,invalidate_packages=()):
            if invalidate_packages:raise RuntimeError('C build uses full recompilation, not crate invalidation')
            return c_build(directory,project)
    elif rust:
        from adversarial_setup_rust import build as rust_build
        if not identity.get('toolchain','').startswith('rustc '):
            raise RuntimeError('Rust mutation adapter requires an identified Rust target')
        def build_target(directory,project,invalidate_packages=()):
            return rust_build(directory,project,clean_package=True,clean_packages=invalidate_packages)
    else:
        if not identity.get('toolchain','').startswith('go version '):
            raise RuntimeError('Go mutation adapter requires an identified Go target')
        def build_target(directory,project,invalidate_packages=()):
            if invalidate_packages:
                raise RuntimeError('Explicit crate invalidation requires a Rust target')
            return build(directory,project)
    source=Path(identity['source_path'])
    source.relative_to(app)
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    instructions=json.loads((package/'faults/definitions.json').read_text(encoding='utf-8'))
    if rust or c:
        if subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'],text=True,timeout=15).strip():
            raise RuntimeError('Pristine rebuild preflight requires unchanged target source')
        invalidation=list(dict.fromkeys(p for fault in instructions for p in fault.get('invalidate_packages',[]))) if rust else []
        initial=identity['binary_sha256']
        first=build_target(app,args.project,invalidation)
        second=build_target(app,args.project,invalidation)
        preflight=dict(initial_target_binary_sha256=initial,
            first_clean_target_binary_sha256=first['binary_sha256'],
            second_clean_target_binary_sha256=second['binary_sha256'],
            initial_build_differs=initial!=first['binary_sha256'],
            explicit_crate_invalidation=invalidation,
            reproducible=first['binary_sha256']==second['binary_sha256'],
            scope=('Two pristine declared-crate clean builds before source controls; no control qualification implied'
                   if rust else 'Two forced ordinary Makefile compilations before C source controls; no control qualification implied'))
        (RAW/args.project/(('rust' if rust else 'c')+'-pristine-build-preflight-'+str(time.time_ns())+'.json')).write_text(
            json.dumps(preflight,indent=2)+'\n',encoding='utf-8')
        if not preflight['reproducible']:
            raise RuntimeError('Pristine compiled target rebuilds are not reproducible')
        identity=second
    controls=[]
    for mutation in instructions:
        name=mutation['name']
        case_name=mutation['case']
        original_case=next(c for c in config['cases'] if c['name']==case_name)
        suffix=original_case.get('baseline_suffix_by_host',config.get('baseline_suffix_by_host',{})).get(__import__('platform').system(),'')
        case=dict(original_case,name=case_name+suffix)
        spec=package/(case['name']+'.json')
        contracts=[spec,*(package/'snapshots').glob('*')]
        digests={str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in contracts if p.is_file()}
        path=source/mutation['file']
        path.resolve(strict=True).relative_to(source.resolve())
        original=path.read_bytes()
        stat=path.stat()
        value=original.decode('utf-8').replace('\r\n','\n')
        if value.count(mutation['old'])!=1:
            raise RuntimeError('Actual source mutation anchor is not unique: '+name)
        modified=value.replace(mutation['old'],mutation['new'])
        patch=''.join(difflib.unified_diff(value.splitlines(True),modified.splitlines(True),
            fromfile='a/'+mutation['file'],tofile='b/'+mutation['file']))
        (package/'faults'/(name+'.patch')).write_text(patch,encoding='utf-8')
        before_binary=hashlib.sha256(Path(identity['binary']).read_bytes()).hexdigest()
        fault=dict(name=name,source_file=mutation['file'],original_sha256=hashlib.sha256(original).hexdigest(),
                   mutated_sha256=hashlib.sha256(modified.encode()).hexdigest(),case=case_name,
                   pristine_target_binary_sha256=before_binary,contract_sha256=digests,
                   negative_probe_wall_timeout_seconds=30)
        label=name+'-'+str(time.time_ns())
        report=RAW/args.project/(label+'.json')
        try:
            path.write_bytes(modified.encode('utf-8'))
            mutated_identity=build_target(app,args.project,mutation.get('invalidate_packages',[]))
            fault['mutated_target_binary_sha256']=mutated_identity['binary_sha256']
            if rust:fault['mutation_profile_cleanup']=mutated_identity['last_profile_cleanup']
            state_only=mutation.get('state_only',False)
            result=run([args.binary,'test','--report',report.relative_to(ROOT),
                '--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],args.project,label,
                env=env,expected=0 if state_only else 1,timeout=30)
            data=json.loads(report.read_text(encoding='utf-8'))
            if state_only:
                if data['summary']['passed']!=1:
                    raise RuntimeError('Actual saved corruption did not preserve ordinary terminal green')
                try:
                    recorder(args.binary,args.project,case,env,export=False,wall_timeout=30)
                except RuntimeError as error:
                    if 'Independent exact file state mismatch' not in str(error):
                        raise
                    fault.update(state_oracle_detected=True,state_probe_evidence_id=error.evidence_id)
                else:
                    raise RuntimeError('Independent oracle accepted actual corrupt saved bytes')
            else:
                if data['summary']['failed']!=1 or not data['results'][0].get('failure'):
                    raise RuntimeError('Actual upstream regression lacked a failed result')
                fault['category']=data['results'][0]['failure']['category']
            if not data['results'][0]['cleanup']['confirmed_exited']:
                raise RuntimeError('Mutated application cleanup not confirmed')
            fault.update(evidence_id=result['id'],report=report.relative_to(ROOT).as_posix())
        finally:
            path.write_bytes(original)
            os.utime(path,ns=(stat.st_atime_ns,stat.st_mtime_ns))
            restored_identity=build_target(app,args.project,mutation.get('invalidate_packages',[]))
        if path.read_bytes()!=original or restored_identity['binary_sha256']!=before_binary:
            fault.update(restored_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         actual_restored_target_binary_sha256=restored_identity['binary_sha256'],
                         accepted=False,scope='Restoration failure; no qualified source-control credit')
            (RAW/args.project/(label+'-restoration-failure.json')).write_text(
                json.dumps(fault,indent=2)+'\n',encoding='utf-8')
            raise RuntimeError('Source or reproducible target binary was not restored exactly')
        if rust:fault['restoration_profile_cleanup']=restored_identity['last_profile_cleanup']
        if {str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in contracts if p.is_file()}!=digests:
            raise RuntimeError('Fault detection changed its approved contract')
        recovery=RAW/args.project/('restored-'+label+'.json')
        result=run([args.binary,'test','--report',recovery.relative_to(ROOT),spec],
                   args.project,'restore-'+name,env=env)
        state_recovery=recorder(args.binary,args.project,case,env,export=False)
        fault.update(restored=True,recovery_id=result['id'],state_recovery_id=state_recovery['id'],contracts_unchanged=True,
                     restored_target_binary_sha256=restored_identity['binary_sha256'])
        controls.append(fault)
        (RAW/args.project/(label+'-control.json')).write_text(json.dumps(fault,indent=2)+'\n',encoding='utf-8')
        print(name,'detected; exact source/binary restored; ordinary and state recovery passed',flush=True)
    (RAW/args.project/('mutation-controls-'+os.name+'-'+str(time.time_ns())+'.json')).write_text(
        json.dumps(controls,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
