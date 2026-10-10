#!/usr/bin/env python3
"""Persist selected real evidence and count all retained local attempts."""
import json,re,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/validation/ten-project-user-pass'
RAW=ROOT/'artifacts/ten-project-user-pass'
for directory in DOC.iterdir():
 if not directory.is_dir() or not (directory/'result.json').exists():continue
 raw=RAW/directory.name;out=directory/'reports';out.mkdir(exist_ok=True)
 totals=dict(machine_reports=0,observed_passed_results=0,observed_failed_results=0,expected_negative_failed_results=0,expected_intentional_change_failures=0,other_failed_results=0,capture_logs=0,rejected_captures=0)
 failures=[]
 for p in raw.rglob('*.json'):
  try:d=json.loads(p.read_text(encoding='utf-8'))
  except (ValueError,UnicodeError):continue
  if 'report_version' not in d:continue
  totals['machine_reports']+=1
  for r in d.get('results',[]):
   if r['status']=='passed':totals['observed_passed_results']+=1
   else:
    totals['observed_failed_results']+=1
    key='expected_negative_failed_results' if 'defect' in p.name and 'setup-failed' not in p.name else 'expected_intentional_change_failures' if 'intentional-expected-change' in p.name else 'other_failed_results'
    totals[key]+=1
    failures.append(dict(raw_path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),classification=key,failure=r.get('failure'),cleanup=r.get('cleanup'),runner_version=d.get('runner_version'),spec_path=r.get('spec_path')))
 for p in raw.rglob('*.log'):
  content=p.read_text(encoding='utf-8',errors='replace')
  if 'Recorder controls (target input is separate):' not in content:continue
  totals['capture_logs']+=1
  if 'Recorder:' in content:
   totals['rejected_captures']+=1
   capture_directory=out/'rejected-captures';capture_directory.mkdir(exist_ok=True)
   shutil.copyfile(p,capture_directory/p.name)
 totals['scope']='Counts of retained artifacts, not total-ever execution claims. Early pre-archive overwritten passing retries are not recoverable; all known first failures are retained and described separately.'
 for name in ['record-summary.json','defect-summary.json','recovery-summary.json','final-summary.json','oracle-all-summary.json','independent-state-negative.json','installed-target-identity.json','mutation-identities.json','maintenance-summary.json','patch-reacquisition-setup-failure.json','mounted-python-startup.json','fixture-mode-regression.json','fixture-baseline-review.json']:
  if (raw/name).exists():shutil.copyfile(raw/name,out/name)
 case=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'))['cases'][0]['name']
 report=raw/(case+'-defect-0.json')
 if report.exists():
  d=json.loads(report.read_text(encoding='utf-8'))
  for r in d['results']:
   for field,path in r.get('evidence',{}).items():
    source=Path(path)
    if path.startswith('/mnt/c/'):
     source=Path('C:/'+path[len('/mnt/c/'):])
    if source.is_file():
     name='defect-'+field.replace('_path','')+'.txt';shutil.copyfile(source,out/name);r['evidence'][field]=str((out/name).relative_to(ROOT)).replace('\\','/')
  (out/'defect.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
 totals['raw_evidence_bytes']=sum(p.stat().st_size for p in raw.rglob('*') if p.is_file())
 if totals['raw_evidence_bytes']>64*1024*1024:raise SystemExit('Project raw evidence bound exceeded: '+directory.name)
 (out/'retained-attempt-counts.json').write_text(json.dumps(totals,indent=2)+'\n',encoding='utf-8')
 (out/'retained-failures.json').write_text(json.dumps(failures,indent=2)+'\n',encoding='utf-8')
 print(directory.name,totals,flush=True)
