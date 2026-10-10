"""Exercise ordinary public commands; keep every attempt and same-workspace probes.

Recorder state probes are separate executions from ordinary runner replays.
No file assertions are claimed as public runner functionality.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import time
from adversarial_process import ROOT,DOC,RAW,run

def control(step):
    key,value=next(iter(step.items()))
    if key=='text': return '/text '+json.dumps(value,ensure_ascii=False)
    if key=='resize': return f"/resize {value['width']} {value['height']}"
    names={'expect':'expect','expect_not':'absent','key':'key','exit':'exit','snapshot':'snapshot'}
    return '/'+names[key]+' '+str(value)

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def check_state(working,case):
    if not working.parent.name.startswith('playtestr-workspace-'):
        raise RuntimeError('Independent oracle received no managed workspace')
    checked={}
    for relative,value in case.get('expected_files',{}).items():
        unresolved=working/relative
        unresolved.relative_to(working)
        for parent in [unresolved,*unresolved.parents]:
            if parent==working.parent:
                break
            if parent.is_symlink():
                raise RuntimeError('Independent oracle refuses linked state: '+relative)
        target=unresolved.resolve()
        target.relative_to(working.resolve())
        if target.is_symlink() or not target.is_file():
            raise RuntimeError('Independent expected file absent or unsafe: '+relative)
        with target.open('rb') as stream:
            actual=stream.read(4*1024*1024+1)
        if len(actual)>4*1024*1024:
            raise RuntimeError('Independent file oracle size bound')
        expected=value.encode('utf-8')
        if actual!=expected:
            raise RuntimeError('Independent exact file state mismatch: '+relative+
                ' actual='+hashlib.sha256(actual).hexdigest()+' expected='+hashlib.sha256(expected).hexdigest())
        checked[relative]=hashlib.sha256(actual).hexdigest()
    for relative in case.get('absent_paths',[]):
        target=(working/relative).resolve()
        target.relative_to(working.resolve())
        if target.exists():
            raise RuntimeError('Independent expected absence mismatch: '+relative)
    return dict(files=checked,absent=case.get('absent_paths',[]),passed=True)

def recorder(binary,project,case,env,*,export=True,rerecord=False):
    directory=DOC/project
    spec=directory/(case['name']+'.json')
    output=spec if export else directory/('probe-'+str(time.time_ns())+'.json')
    args=[binary,'record','--output',output,'--name',case['purpose'],'--fixture','fixtures',
          '--temporary-home','--temporary-temp','--width','100','--height','30',
          '--timeout-ms',str(case['timeout_ms']),'--run-timeout-ms','120000']
    config=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'))
    for key,value in config.get('environment',{}).items():
        args+=['--env',key+'='+value]
    args+=['--',*case['command']]
    steps=list(case['steps'])
    # These error strings contain random workspace paths: readiness/exit remain
    # explicit, and only the earlier stable prompt screen is snapshotted.
    if case['name']=='edge-existing-rejected':
        steps.insert(-4,{'snapshot':case['name']+'.txt'})
    else:
        steps+=[{'snapshot':case['name']+'.txt'}]
    body='\n'.join(control(s) for s in steps)+'\n'
    if rerecord:
        if len(steps)<4:
            raise RuntimeError('Suffix maintenance needs a meaningful retained prefix')
        body+='/rerecord 3\n'+'\n'.join(control(s) for s in steps[3:])+'\n'
    body+='/review\n'
    sent=False
    async def inspect(proc,output,evidence):
        nonlocal sent
        screen=output.decode('utf-8',errors='replace')
        if sent:
            return
        if 'Recorder:' in screen:
            sent=True
            proc.stdin.write(b'/screen\n/quit\n')
            await proc.stdin.drain()
            raise RuntimeError('Public recorder rejected a step; evidence retained')
        if f"Baseline {case['name']}.txt:" not in screen or not screen.rstrip().endswith('record>'):
            return
        matches=re.findall(r'working-directory=(".*")',screen)
        if not matches:
            raise RuntimeError('Recorder omitted current workspace identity')
        working=Path(json.loads(matches[-1]))
        if not export:
            baseline=directory/'snapshots'/(case['name']+'.txt')
            match=re.search(r'Baseline '+re.escape(case['name'])+r'\.txt:\r?\n(.*?)\r?\nrecord>',screen,re.S)
            if match is None:
                return
            observed=match[1].replace('\r\n','\n').rstrip('\n')+'\n'
            if observed!=baseline.read_text(encoding='utf-8'):
                raise RuntimeError('Independent capture differs from the reviewed screen contract')
        state=check_state(working,case)
        (evidence/'state-oracle.json').write_text(json.dumps(state,indent=2)+'\n')
        sent=True
        proc.stdin.write(b'/replay\n/save\n' if export else b'/quit\n')
        await proc.stdin.drain()
        proc.stdin.close()
    result=run(args,project,case['name']+('-record' if export else '-state-probe'),env=env,
        input=body,expected=0 if export else 130,on_output=inspect)
    if not sent:
        raise RuntimeError('Recorder completed without independent state evidence')
    if export and (not spec.exists() or 'Recorder:' in result['output']):
        raise RuntimeError('Recorder export/replay failed')
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['record','test','state','rerecord','final'])
    parser.add_argument('project')
    parser.add_argument('--case')
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--binary',type=Path)
    args=parser.parse_args()
    runtime=args.runtime or ROOT/'.cache/ten-new-project-apps'/args.project
    identity=json.loads((runtime/'runtime.json').read_text())
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    binary=args.binary or ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr-linux')
    config=json.loads((DOC/args.project/'scenarios.json').read_text(encoding='utf-8'))
    cases=[c for c in config['cases'] if not args.case or c['name']==args.case]
    if not cases:
        raise RuntimeError('Empty case selection')
    for case in cases:
        if case['name']=='edge-cancel-after-edit' and os.name!='nt':
            case=dict(case,name='edge-cancel-after-edit-unix')
        spec=DOC/args.project/(case['name']+'.json')
        if args.mode=='record':
            if spec.exists():
                raise RuntimeError('Refuse replacing an approved contract')
            recorder(binary,args.project,case,env)
        elif args.mode in ('state','rerecord'):
            recorder(binary,args.project,case,env,export=False,rerecord=args.mode=='rerecord')
        else:
            count=10 if args.mode=='final' else 1
            for repetition in range(count):
                before=digest(spec)
                label=f"{case['name']}-{args.mode}-{repetition}"
                report=RAW/args.project/(label+'-'+str(time.time_ns())+'.json')
                result=run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                    args.project,label,env=env,load=args.mode=='final' and repetition>=5)
                data=json.loads(report.read_text(encoding='utf-8'))
                run_result=data['results'][0]
                if data['summary']['passed']!=1 or not run_result['cleanup']['confirmed_exited']:
                    raise RuntimeError('Reported pass lacks exact result/cleanup evidence')
                if digest(spec)!=before:
                    raise RuntimeError('Ordinary execution changed its contract')
                if args.mode=='final' and case.get('expected_files'):
                    recorder(binary,args.project,case,env,export=False)
                print(label,'passed',result['id'],flush=True)
        print(args.project,case['name'],args.mode,'complete',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
