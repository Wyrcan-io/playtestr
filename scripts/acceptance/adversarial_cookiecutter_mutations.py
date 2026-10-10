"""Real target faults, unchanged-contract detection, restoration and independent state controls."""
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
    parser.add_argument('--binary',type=Path)
    args=parser.parse_args()
    app=args.runtime or ROOT/'.cache/ten-new-project-apps/cookiecutter'
    identity=json.loads((app/'runtime.json').read_text())
    source=Path(identity['source_path'])
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    binary=args.binary or ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr-linux')
    directory=DOC/'cookiecutter'
    spec=directory/'normal-project.json'
    baseline=directory/'snapshots/normal-project.txt'
    contracts={str(p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}
    mutations=[
        ('choice-truncation','cookiecutter/prompt.py',
         "enumerate(options, 1)","enumerate(options[:1], 1)",False),
        ('wrong-success-exit','cookiecutter/cli.py',
         "            keep_project_on_failure=keep_project_on_failure,\n        )\n    except (",
         "            keep_project_on_failure=keep_project_on_failure,\n        )\n        sys.exit(7)\n    except (",False),
        ('silent-saved-corruption','cookiecutter/generate.py',
         '        fh.write(rendered_file)',
         "        fh.write(rendered_file + 'CORRUPTED\\n')",True),
    ]
    controls=[]
    for name,relative,old,new,state_only in mutations:
        path=source/relative
        original=path.read_bytes()
        value=original.decode('utf-8').replace('\r\n','\n')
        if value.count(old)!=1:
            raise RuntimeError('Mutation anchor not unique: '+name)
        modified=value.replace(old,new)
        patch=''.join(difflib.unified_diff(value.splitlines(True),modified.splitlines(True),
            fromfile='a/'+relative,tofile='b/'+relative))
        (directory/(name+'.patch')).write_text(patch,encoding='utf-8',newline='\n')
        try:
            path.write_text(modified,encoding='utf-8',newline='\n')
            fault=dict(name=name,source_path=relative,
                pristine_sha256=hashlib.sha256(original).hexdigest(),
                mutated_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                contracts=contracts,host=os.name)
            label=name+'-'+str(time.time_ns())
            report=RAW/'cookiecutter'/(label+'.json')
            result=run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                'cookiecutter',label,env=env,expected=0 if state_only else 1)
            data=json.loads(report.read_text(encoding='utf-8'))
            if state_only:
                if data['summary']['passed']!=1:
                    raise RuntimeError('Saved corruption did not preserve passing terminal UI')
                config=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'))
                case=next(c for c in config['cases'] if c['name']=='normal-project')
                try:
                    recorder(binary,'cookiecutter',case,env,export=False)
                except RuntimeError as error:
                    if 'Independent exact file state mismatch' not in str(error):
                        raise
                    fault['state_oracle_detected']=True
                else:
                    raise RuntimeError('State oracle accepted actual saved corruption')
            else:
                if data['summary']['failed']!=1 or not data['results'][0].get('failure'):
                    raise RuntimeError('Missing actual regression evidence')
                fault['category']=data['results'][0]['failure']['category']
                fault['failed_step']=next(s['number'] for s in data['results'][0]['steps'] if s['status']=='failed')
            if not data['results'][0]['cleanup']['confirmed_exited']:
                raise RuntimeError('Mutation cleanup unconfirmed')
            fault['evidence_id']=result['id']
            fault['report']=str(report.relative_to(ROOT))
        finally:
            path.write_bytes(original)
        if path.read_bytes()!=original:
            raise RuntimeError('Target source restoration mismatch')
        after={str(p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}
        if after!=contracts:
            raise RuntimeError('Mutation weakened an unchanged contract')
        recovery=RAW/'cookiecutter'/('restored-'+name+'-'+str(time.time_ns())+'.json')
        result=run([binary,'test','--report',recovery,spec],'cookiecutter','restore-'+name,env=env)
        fault.update(restored=True,recovery_id=result['id'],contracts_unchanged=True)
        controls.append(fault)
        (RAW/'cookiecutter'/(label+'-control.json')).write_text(json.dumps(fault,indent=2)+'\n')
        print(name,'detected and restored',flush=True)
    output=RAW/'cookiecutter'/('mutation-controls-'+os.name+'-'+str(time.time_ns())+'.json')
    output.write_text(json.dumps(controls,indent=2)+'\n')

if __name__=='__main__':
    main()
