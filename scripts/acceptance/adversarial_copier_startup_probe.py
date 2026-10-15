"""Measure actual synthetic Git-update preparation; never grants qualification."""
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from adversarial_process import ROOT,DOC,RAW
from adversarial_journey import recorder,host_case_name

def main():
    project='copier';package=DOC/project
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    case=next(c for c in config['cases'] if c['name']=='normal-git-update')
    case=dict(case,name=host_case_name(case,config,platform.system()),timeout_ms=30000)
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob('normal-git-update*.json')}
    original.update({'snapshots/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (package/'snapshots').glob('normal-git-update*')})
    runtime=json.loads((ROOT/'.cache/ten-new-project-apps/copier/runtime.json').read_text(encoding='utf-8'))
    env=dict(os.environ,PATH=runtime['path']+os.pathsep+os.environ['PATH'])
    binary=ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    results=[]
    for index in range(20):
        trace=RAW/project/('git-startup-trace-'+str(index)+'.jsonl')
        start=time.monotonic()
        result=recorder(binary,project,case,env,export=False,
            diagnostic_environment={'GIT_TRACE2_EVENT':str(trace)})
        timings=json.loads((RAW/project/result['id']/'recorder-control-timings.json').read_text(encoding='utf-8'))
        results.append(dict(index=index,id=result['id'],seconds=time.monotonic()-start,trace=trace.relative_to(ROOT).as_posix(),control_timings=timings))
        print('diagnostic',index,'passed',result['id'],flush=True)
    for name,expected in original.items():
        if hashlib.sha256((package/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Diagnostic changed reviewed contract')
    output=dict(host=platform.system(),diagnostic_step_budget_ms=30000,primary_contracts_unchanged=True,
        results=results,scope='Exploratory twenty real recorder/exact-state probes with Git trace and expanded diagnostic budget; zero final qualification credit')
    (RAW/project/('git-startup-probe-'+platform.system()+'.json')).write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
