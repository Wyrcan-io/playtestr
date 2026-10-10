"""Retain every bounded attempt of the historical native wizard sequence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from adversarial_process import ROOT,DOC,RAW,run

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--count',type=int,default=100)
    parser.add_argument('--trace',action='store_true')
    parser.add_argument('--target',type=Path)
    args=parser.parse_args()
    if not 1<=args.count<=1000:
        raise RuntimeError('Bounded reproduction count required')
    ext='.exe' if os.name=='nt' else ''
    directory=RAW/'wizard-reproduction'/str(time.time_ns())
    directory.mkdir(parents=True)
    original=ROOT/'examples/recorded/wizard.json'
    spec=json.loads(original.read_text(encoding='utf-8'))
    target=(args.target or ROOT/'bin'/('fixture'+ext)).resolve(strict=True)
    spec['command']=[str(target),'wizard']
    shutil.copytree(original.parent/'fixtures/wizard',directory/'fixture')
    spec['workspace']['fixture']='fixture'
    spec['timeout_ms']=1000
    spec['run_timeout_ms']=5000
    path=directory/'wizard.json'
    if args.trace:
        spec['inherit_env'].append('PLAYTESTR_WIZARD_TRACE')
    path.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    shutil.copytree(original.parent/'snapshots',directory/'snapshots')
    failures=[]
    attempts=[]
    for i in range(args.count):
        report=directory/(str(i)+'.json')
        env=dict(os.environ,PLAYTESTR_DELAY_MS=str([0,25,100,5,60,150,10,80,40,120][i%10]))
        if args.trace:
            env['PLAYTESTR_WIZARD_TRACE']=str(directory/(str(i)+'.trace'))
        try:
            result=run([ROOT/'bin'/('playtestr'+ext),'test','--report',report.relative_to(ROOT),
                '--artifacts-dir',(directory/str(i)).relative_to(ROOT),path],
                'wizard-reproduction','historical-sequence-'+str(i),env=env,timeout=15)
            attempts.append({'index':i,'id':result['id'],'passed':True})
        except RuntimeError:
            if not report.exists():
                raise
            data=json.loads(report.read_text(encoding='utf-8'))
            if data['results'][0]['failure']['category'] in ('invalid_spec','launch_failure','workspace_setup_failure'):
                raise RuntimeError('Reproduction setup failed; stop instead of repeating invalid runs')
            failures.append({'index':i,'result':data['results'][0]})
            attempts.append({'index':i,'passed':False})
            print('FIRST RETAINED FAILURE',i,json.dumps(data['results'][0]['failure']),flush=True)
        if i%10==0:
            print('Completed',i+1,'failures',len(failures),flush=True)
    (directory/'summary.json').write_text(json.dumps(dict(attempts=attempts,failures=failures,
        target_sha256=__import__('hashlib').sha256(target.read_bytes()).hexdigest(),
        scope='Reduced deadlines only; same target, keys, text, resize, reviewed snapshots. Exploratory, no external-project credit.'),indent=2)+'\n',encoding='utf-8')
    print(directory,'failures',len(failures))
    if failures:
        sys.exit(1)

if __name__=='__main__': main()
