"""Real interpreted-source faults, unchanged contracts and exact restoration."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import time
from adversarial_process import ROOT,DOC,RAW,run
from adversarial_journey import recorder
from adversarial_setup_python import source_identity


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['ranger'])
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--binary',type=Path,required=True)
    args=parser.parse_args();project=args.project
    app=args.runtime or ROOT/'.cache/ten-new-project-apps'/project
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    source=Path(identity['source_path']);source.resolve(strict=True).relative_to(app.resolve(strict=True))
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    package=DOC/project
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    definitions=json.loads((package/'faults/definitions.json').read_text(encoding='utf-8'))
    pristine=source_identity(source)
    if pristine!=identity['execution_identity']:
        raise RuntimeError('Interpreted source differs from pristine setup identity')
    controls=[]
    for mutation in definitions:
        name=mutation['name'];case=next(c for c in config['cases'] if c['name']==mutation['case'])
        spec=package/(case['name']+'.json')
        contracts=[spec,*(package/'snapshots').glob('*')]
        hashes={p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in contracts if p.is_file()}
        path=source/mutation['file'];path.resolve(strict=True).relative_to(source.resolve(strict=True))
        original=path.read_bytes();stat=path.stat();value=original.decode('utf-8').replace('\r\n','\n')
        if value.count(mutation['old'])!=1:raise RuntimeError('Source mutation anchor is not unique: '+name)
        modified=value.replace(mutation['old'],mutation['new'])
        patch=''.join(difflib.unified_diff(value.splitlines(True),modified.splitlines(True),
                                         fromfile='a/'+mutation['file'],tofile='b/'+mutation['file']))
        (package/'faults'/(name+'.patch')).write_text(patch,encoding='utf-8')
        label=name+'-'+str(time.time_ns());report=RAW/project/(label+'.json')
        fault=dict(name=name,case=case['name'],source_file=mutation['file'],
                   original_sha256=hashlib.sha256(original).hexdigest(),contract_sha256=hashes,
                   pristine_executed_source_sha256=pristine['digest'],
                   launcher_sha256=identity['binary_sha256'],
                   interpreter_sha256=identity['interpreter_sha256'])
        try:
            path.write_bytes(modified.encode('utf-8'))
            os.utime(path,ns=(stat.st_atime_ns,stat.st_mtime_ns+2_000_000_000))
            mutated=source_identity(source)
            if mutated['digest']==pristine['digest']:raise RuntimeError('Source control did not change actual source')
            fault['mutated_executed_source_sha256']=mutated['digest']
            state_only=mutation.get('state_only',False)
            result=run([args.binary,'test','--report',report.relative_to(ROOT),
                        '--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                       project,label,env=env,timeout=30,expected=0 if state_only else 1)
            data=json.loads(report.read_text(encoding='utf-8'))
            if state_only:
                if data['summary']['passed']!=1:raise RuntimeError('Saved corruption did not preserve ordinary green')
                try:recorder(args.binary,project,case,env,export=False,wall_timeout=30)
                except RuntimeError as error:
                    if 'Independent exact file state mismatch' not in str(error):raise
                    fault.update(state_oracle_detected=True,state_probe_evidence_id=error.evidence_id)
                else:raise RuntimeError('Independent oracle accepted real corrupt saved bytes')
            else:
                if data['summary']['failed']!=1 or not data['results'][0].get('failure'):
                    raise RuntimeError('Source regression lacked a real failed result')
                fault['category']=data['results'][0]['failure']['category']
            if not data['results'][0]['cleanup']['confirmed_exited']:
                raise RuntimeError('Fault cleanup not confirmed')
            fault.update(evidence_id=result['id'],report=report.relative_to(ROOT).as_posix())
        finally:
            path.write_bytes(original);os.utime(path,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        restored=source_identity(source)
        if restored!=pristine:raise RuntimeError('Actual executed Python source was not restored exactly')
        if {p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in contracts if p.is_file()}!=hashes:
            raise RuntimeError('Source fault weakened an unchanged contract')
        recovery=RAW/project/('restored-'+label+'.json')
        passed=run([args.binary,'test','--report',recovery.relative_to(ROOT),spec],project,'restore-'+name,env=env)
        state=recorder(args.binary,project,case,env,export=False)
        fault.update(restored=True,recovery_id=passed['id'],state_recovery_id=state['id'],
                     contracts_unchanged=True,restored_executed_source_sha256=restored['digest'])
        controls.append(fault)
        (RAW/project/(label+'-control.json')).write_text(json.dumps(fault,indent=2)+'\n',encoding='utf-8')
        print(name,'detected; exact executed source, ordinary and state recovery passed',flush=True)
    (RAW/project/('mutation-controls-'+os.name+'-'+str(time.time_ns())+'.json')).write_text(
        json.dumps(controls,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
