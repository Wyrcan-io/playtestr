"""Actual Copier source faults with exact contract/source restoration."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import time
from adversarial_process import ROOT,DOC,RAW,run
from adversarial_journey import recorder

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--binary',type=Path,required=True)
    args=parser.parse_args()
    app=args.runtime or ROOT/'.cache/ten-new-project-apps/copier'
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    source=Path(identity['source_path'])
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    package=DOC/'copier'
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    suffix=config.get('baseline_suffix_by_host',{}).get(__import__('platform').system(),'')
    mutations=[
        ('validator-bypass','copier/_user_data.py','                self.validate_answer(ans)',
         '                pass # Deliberate real validation regression','edge-validator-recovery',False),
        ('wrong-success-exit','copier/_cli.py','    return 0\n\n\nclass CopierApp',
         '    return 7\n\n\nclass CopierApp','normal-project',False),
        ('silent-saved-corruption','copier/_main.py','            dst_abspath.write_bytes(new_content)',
         "            dst_abspath.write_bytes(new_content + b'CORRUPTED\\n')",'normal-project',True),
    ]
    controls=[]
    for name,relative,old,new,case_name,state_only in mutations:
        spec=package/(case_name+suffix+'.json')
        case_configuration=next(c for c in config['cases'] if c['name']==case_name)
        extension='.rows.json' if case_configuration.get('snapshot_rows') else '.txt'
        baseline=package/'snapshots'/(case_name+suffix+extension)
        contracts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}
        path=source/relative
        original=path.read_bytes()
        original_stat=path.stat()
        value=original.decode('utf-8').replace('\r\n','\n')
        if value.count(old)!=1:
            raise RuntimeError('Mutation anchor not unique: '+name)
        modified=value.replace(old,new)
        patch=''.join(difflib.unified_diff(value.splitlines(True),modified.splitlines(True),
            fromfile='a/'+relative,tofile='b/'+relative))
        (package/(name+'.patch')).write_text(patch,encoding='utf-8',newline='\n')
        try:
            path.write_text(modified,encoding='utf-8',newline='\n')
            # Make loader invalidation explicit, even for a same-length exit-code
            # edit restored within one timestamp second. This is fixture setup.
            os.utime(path,ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns+2_000_000_000))
            fault=dict(name=name,source_path=relative,case=case_name,
                pristine_sha256=hashlib.sha256(original).hexdigest(),
                mutated_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),contracts=contracts,
                loader_mtime='Original timestamp +2 seconds during mutation, exact original restored')
            label=name+'-'+str(time.time_ns())
            report=RAW/'copier'/(label+'.json')
            result=run([args.binary,'test','--report',report.relative_to(ROOT),
                '--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                'copier',label,env=env,expected=0 if state_only else 1)
            data=json.loads(report.read_text(encoding='utf-8'))
            if state_only:
                if data['summary']['passed']!=1:
                    raise RuntimeError('Saved corruption must preserve ordinary terminal green')
                case=dict(next(c for c in config['cases'] if c['name']==case_name),name=case_name+suffix)
                try:
                    recorder(args.binary,'copier',case,env,export=False)
                except RuntimeError as error:
                    if 'Independent exact file state mismatch' not in str(error): raise
                    fault.update(state_oracle_detected=True,state_probe_evidence_id=error.evidence_id)
                else:
                    raise RuntimeError('Independent oracle accepted actual saved corruption')
            else:
                if data['summary']['failed']!=1 or not data['results'][0].get('failure'):
                    raise RuntimeError('Regression lacked an actual failed assertion/exit report')
                fault['category']=data['results'][0]['failure']['category']
            if not data['results'][0]['cleanup']['confirmed_exited']:
                raise RuntimeError('Mutation target cleanup unconfirmed')
            fault.update(evidence_id=result['id'],report=report.relative_to(ROOT).as_posix())
        finally:
            path.write_bytes(original)
            os.utime(path,ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns))
        if path.read_bytes()!=original:
            raise RuntimeError('Exact source restoration failed')
        if {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}!=contracts:
            raise RuntimeError('Regression weakened unchanged contract')
        recovery=RAW/'copier'/('restored-'+name+'-'+str(time.time_ns())+'.json')
        result=run([args.binary,'test','--report',recovery.relative_to(ROOT),spec],
            'copier','restore-'+name,env=env)
        config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
        case=dict(next(c for c in config['cases'] if c['name']==case_name),name=case_name+suffix)
        state_recovery=recorder(args.binary,'copier',case,env,export=False)
        fault.update(restored=True,recovery_id=result['id'],contracts_unchanged=True,
                     state_recovery_id=state_recovery['id'])
        controls.append(fault)
        (RAW/'copier'/(label+'-control.json')).write_text(json.dumps(fault,indent=2)+'\n',encoding='utf-8')
        print(name,'detected and restored',flush=True)
    (RAW/'copier'/('mutation-controls-'+os.name+'-'+str(time.time_ns())+'.json')).write_text(
        json.dumps(controls,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
