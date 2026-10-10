#!/usr/bin/env python3
"""Reacquire one real application at a time; qualify exact final runner and clean."""
import argparse,json,os,subprocess,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
started=time.monotonic()
DOC=ROOT/'docs/validation/ten-project-user-pass'
LINUX='/mnt/c/'+str(ROOT)[3:].replace('\\','/')
SCRIPT=LINUX+'/scripts/acceptance/'
p=argparse.ArgumentParser();p.add_argument('index',type=int);p.add_argument('--source',required=True);p.add_argument('--resume-pristine-go',action='store_true');a=p.parse_args()
c=json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))[a.index]
frozen=json.loads((DOC/'final-runner.json').read_text(encoding='utf-8'))
if frozen['source']!=a.source or hashlib.sha256((ROOT/'bin/playtestr-linux').read_bytes()).hexdigest()!=frozen['binaries']['playtestr-linux']:raise SystemExit('Final runner identity differs from frozen reviewed source')
slug='create-vite' if c['repo']=='vitejs/vite' else c['repo'].split('/')[-1]
application=slug+'-'+str(a.index+1).zfill(2);app=ROOT/'.cache/ten-project-apps'/application
raw=ROOT/'artifacts/ten-project-user-pass'/slug;raw.mkdir(parents=True,exist_ok=True)
def run(args,timeout=1200):
 subprocess.run(list(map(str,args)),cwd=ROOT,check=True,timeout=timeout)
if a.resume_pristine_go:
 if a.index>=5:raise SystemExit('Resume is restricted to verified pristine Go acquisition')
 owner=json.loads((app/'task-owned.json').read_text(encoding='utf-8'))
 if owner!=dict(project=slug,repo=c['repo'],sha=c['sha'],created_by='ten-project-user-pass',workspace=str(ROOT)):raise SystemExit('Unknown resume ownership')
 if subprocess.check_output(['git','-C',app/'source','rev-parse','HEAD'],text=True).strip()!=c['sha'] or subprocess.check_output(['git','-C',app/'source','status','--porcelain']).strip():raise SystemExit('Resume requires exact pristine source')
else:run(['python','scripts/acceptance/user_project_admin.py','acquire',str(a.index),'--quiet',*(['--native-source-only'] if a.index>=5 else [])])
if a.index<5:
 for name in ['LICENSE','LICENSE.md','LICENSE.txt','LICENSE.rst','LICENSE.gpl3','LICENCE','COPYING','COPYING.txt']:
  license_file=app/'source'/name
  if license_file.is_file():
   (DOC/slug/'UPSTREAM-LICENSE.txt').write_bytes(license_file.read_bytes());break
 target={0:'.',1:'.',2:'./cmd/micro',3:'.',4:'./cmd/gdu'}[a.index]
 def build_go():
  with (raw/'final-build.log').open('a',encoding='utf-8') as log:
   subprocess.run(['go','build','-trimpath','-o','../'+slug,target],cwd=app/'source',env=dict(os.environ,GOOS='linux',GOARCH='amd64',CGO_ENABLED='0'),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
 build_go()
 identity=dict(source=c['sha'],target_binary_sha256=hashlib.sha256((app/slug).read_bytes()).hexdigest())
else:
 run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_runtime_bootstrap.py','uv' if a.index<=7 else 'node'])
 run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_python_runtime.py','acquire',application])
 native_source=json.loads((app/'native-source.json').read_text(encoding='utf-8'))['path']
 for name in ['LICENSE','LICENSE.md','LICENSE.txt','LICENSE.rst','LICENSE.gpl3','LICENCE','COPYING','COPYING.txt']:
  read=subprocess.run(['wsl','-d','Ubuntu','--','cat',native_source+'/'+name],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
  if read.returncode==0:
   (DOC/slug/'UPSTREAM-LICENSE.txt').write_bytes(read.stdout);break
 if a.index<=7:run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_python_runtime.py','install',application])
 else:run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_node_runtime.py','install',application])
 identity=json.loads((raw/'installed-target-identity.json').read_text(encoding='utf-8'))
if a.index<5:
 patch=DOC/slug/'target-regression.patch'
 run(['git','-C',app/'source','apply','--check',patch])
 run(['git','-C',app/'source','apply',patch])
 try:
  build_go()
  mutated_identity=dict(target_binary_sha256=hashlib.sha256((app/slug).read_bytes()).hexdigest(),patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest())
  run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_journeys.py','defect',slug])
 finally:
  run(['git','-C',app/'source','apply','--reverse',patch])
  build_go()
 restored=hashlib.sha256((app/slug).read_bytes()).hexdigest()
 if restored!=identity['target_binary_sha256']:raise SystemExit('Restored target binary differs from pristine build')
else:
 helper='user_mutation.py' if a.index<=7 else 'user_node_mutation.py'
 run(['wsl','-d','Ubuntu','--','python3',SCRIPT+helper,'apply',slug])
 try:
  mutated_identity=dict(patch_sha256=hashlib.sha256((DOC/slug/'target-regression.patch').read_bytes()).hexdigest(),actual_target=json.loads((raw/'mutation-identities.json').read_text(encoding='utf-8'))[-1])
  run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_journeys.py','defect',slug])
 finally:run(['wsl','-d','Ubuntu','--','python3',SCRIPT+helper,'restore',slug])
run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_journeys.py','recovery',slug])
negative=json.loads((raw/'defect-summary.json').read_text(encoding='utf-8'))
recovery=json.loads((raw/'recovery-summary.json').read_text(encoding='utf-8'))
if negative['scenarios'][0]['contract_hashes']!=recovery['scenarios'][0]['contract_hashes']:raise SystemExit('Final negative control altered test contracts')
run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_journeys.py','final',slug])
run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_journeys.py','oracle-all',slug])
config=json.loads((DOC/slug/'scenarios.json').read_text(encoding='utf-8'))
if config.get('maintenance_controls'):run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_maintenance_checks.py',slug])
result_path=DOC/slug/'result.json';result=json.loads(result_path.read_text(encoding='utf-8'))
summary=json.loads((raw/'final-summary.json').read_text(encoding='utf-8'))
result.update(status='qualified_on_final_source',deleted=False,upstream=c,final_source=a.source,final_qualification=summary,final_target_identity=identity,final_mutated_identity=mutated_identity,final_defect=negative,final_recovery=recovery,final_negative_contracts_unchanged=True,final_oracles=json.loads((raw/'oracle-all-summary.json').read_text(encoding='utf-8')),operator_elapsed_seconds_before_deletion=round(time.monotonic()-started,3),operator_measurement_scope='Fresh pinned acquisition, build, regression/restoration, ten repetitions per scenario and independent state checks; shared Go caches warm, not independent-user onboarding research')
if config.get('maintenance_controls'):result['final_maintenance']=json.loads((raw/'maintenance-summary.json').read_text(encoding='utf-8'))
result_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
ledger_path=DOC/'ledger.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'));ledger['projects']=[result if v['project']==slug else v for v in ledger['projects']];ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
if a.index>=5:run(['wsl','-d','Ubuntu','--','python3',SCRIPT+'user_python_runtime.py','remove',application])
run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/acceptance/remove-user-project.ps1','-Project',slug,'-Application',application])
print('FINAL PROJECT QUALIFIED AND REMOVED:',slug,flush=True)
