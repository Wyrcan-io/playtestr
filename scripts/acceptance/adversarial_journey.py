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
    if key=='snapshot_rows':
        return '/snapshot-rows '+value['name']+' '+str(value['first'])+' '+str(value['last'])
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
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():
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
        unresolved=working/relative
        for parent in [unresolved,*unresolved.parents]:
            if parent==working.parent:
                break
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():
                raise RuntimeError('Independent expected absence contains linked state: '+relative)
        target=unresolved.resolve()
        target.relative_to(working.resolve())
        if target.exists():
            raise RuntimeError('Independent expected absence mismatch: '+relative)
    return dict(files=checked,absent=case.get('absent_paths',[]),passed=True)

def recorder(binary,project,case,env,*,export=True,rerecord=False):
    directory=DOC/project
    config=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'))
    spec=directory/(case['name']+'.json')
    output=spec if export else directory/('probe-'+str(time.time_ns())+'.json')
    args=[binary,'record','--output',output,'--name',case['purpose'],
          '--fixture',case.get('fixture',config.get('fixture','fixtures')),
          '--temporary-home','--temporary-temp','--width','100','--height','30',
          '--timeout-ms',str(case['timeout_ms']),'--run-timeout-ms','120000']
    for key,value in config.get('environment',{}).items():
        args+=['--env',key+'='+value]
    args+=['--',*case['command']]
    steps=list(case['steps'])
    snapshot_name=case['name']+('.rows.json' if case.get('snapshot_rows') else '.txt')
    # These error strings contain random workspace paths: readiness/exit remain
    # explicit, and only the earlier stable prompt screen is snapshotted.
    if case['name']=='edge-existing-rejected':
        steps.insert(-4,{'snapshot':case['name']+'.txt'})
    else:
        if case.get('snapshot_rows'):
            first,last=case['snapshot_rows']
            capture={'snapshot_rows':dict(name=snapshot_name,first=first,last=last)}
        else:
            capture={'snapshot':snapshot_name}
        # TUIs usually restore the previous screen on quit. Capture the actual
        # meaningful live state at a declared position, then observe clean exit.
        position=case.get('snapshot_after_step',len(steps))
        if not isinstance(position,int) or not 0<=position<=len(steps):
            raise RuntimeError('Invalid declared snapshot position')
        steps.insert(position,capture)
    body='\n'.join(control(s) for s in steps)+'\n'
    if rerecord:
        if len(steps)<4:
            raise RuntimeError('Suffix maintenance needs a meaningful retained prefix')
        body+='/rerecord 3\n'+'\n'.join(control(s) for s in steps[3:])+'\n'
    body+='/review\n'
    commands=body.splitlines()
    next_command=0
    last_prompt=-1
    sent=False
    rejected=False
    async def inspect(proc,output,evidence):
        nonlocal sent,rejected,next_command,last_prompt
        screen=output.decode('utf-8',errors='replace')
        if sent:
            return
        if 'Recorder:' in screen:
            sent=True
            rejected=True
            proc.stdin.write(b'/screen\n/quit\n')
            await proc.stdin.drain()
            # Let the bounded process harness drain the requested real final
            # screen and observe recorder cancellation before raising. Killing
            # immediately after writing /screen used to lose useful evidence.
            proc.stdin.close()
            return
        if not screen.rstrip().endswith('record>'):
            return
        prompt=screen.rfind('record>')
        if prompt<=last_prompt:
            return
        last_prompt=prompt
        if next_command<len(commands):
            proc.stdin.write((commands[next_command]+'\n').encode('utf-8'))
            next_command+=1
            await proc.stdin.drain()
            return
        if f"Baseline {snapshot_name}:" not in screen or not screen.rstrip().endswith('record>'):
            return
        matches=re.findall(r'working-directory=(".*")',screen)
        if not matches:
            raise RuntimeError('Recorder omitted current workspace identity')
        working=Path(json.loads(matches[-1]))
        if not export:
            baseline=directory/'snapshots'/snapshot_name
            match=re.search(r'Baseline '+re.escape(snapshot_name)+r':\r?\n(.*?)\r?\nrecord>',screen,re.S)
            if match is None:
                return
            observed=match[1].replace('\r\n','\n').rstrip('\n')+'\n'
            expected=baseline.read_text(encoding='utf-8')
            if snapshot_name.endswith('.rows.json'):
                if json.loads(observed)!=json.loads(expected):
                    raise RuntimeError('Independent row capture differs from the reviewed row contract')
            elif observed!=expected:
                raise RuntimeError('Independent capture differs from the reviewed screen contract')
        state=check_state(working,case)
        (evidence/'state-oracle.json').write_text(json.dumps(state,indent=2)+'\n')
        sent=True
        proc.stdin.write(b'/replay\n/save\n' if export else b'/quit\n')
        await proc.stdin.drain()
        proc.stdin.close()
    def completed(exit_code,output,evidence):
        if rejected:
            raise RuntimeError('Public recorder rejected a step; final screen retained')
        if not sent or not (evidence/'state-oracle.json').is_file():
            raise RuntimeError('Recorder completed without independent state evidence')
        if export and (not spec.exists() or b'Recorder:' in output):
            raise RuntimeError('Recorder export/replay failed')
    result=run(args,project,case['name']+('-record' if export else '-state-probe'),env=env,
        expected=0 if export else 130,on_output=inspect,on_complete=completed)
    if rejected:
        raise RuntimeError('Public recorder rejected a step; final screen retained')
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
        suffix=case.get('baseline_suffix_by_host',config.get('baseline_suffix_by_host',{})).get(platform.system(),'')
        if suffix:
            case=dict(case,name=case['name']+suffix)
        elif case['name']=='edge-cancel-after-edit' and os.name!='nt':
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
