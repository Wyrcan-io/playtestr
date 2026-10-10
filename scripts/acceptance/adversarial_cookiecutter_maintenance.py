"""Public manual-edit, selected-update, diagnosis, relocation and workflow routes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from adversarial_process import ROOT,DOC,RAW,run

def main():
    directory=DOC/'cookiecutter'
    app=ROOT/'.cache/ten-new-project-apps/cookiecutter'
    identity=json.loads((app/'runtime.json').read_text())
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    binary=ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr-linux')
    primary=directory/'normal-project.json'
    primary_baseline=directory/'snapshots/normal-project.txt'
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [primary,primary_baseline]}
    maintenance=directory/'maintenance'/str(time.time_ns())
    maintenance.mkdir(parents=True,exist_ok=False)
    shutil.copytree(directory/'fixtures',maintenance/'fixtures')
    (maintenance/'snapshots').mkdir()
    baseline=maintenance/'snapshots/normal-project.txt'
    baseline.write_bytes(primary_baseline.read_bytes())
    spec=maintenance/'intentional-name-change.json'
    value=json.loads(primary.read_text(encoding='utf-8'))
    value['name']='Reviewed intentional project label change'
    value['steps'][1]['text']='Maintained Fixture'
    spec.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    old=hashlib.sha256(baseline.read_bytes()).hexdigest()
    report=RAW/'cookiecutter'/('intentional-name-mismatch-'+str(time.time_ns())+'.json')
    mismatch=run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                 'cookiecutter','intended-change-ordinary-mismatch',env=env,expected=1)
    document=json.loads(report.read_text(encoding='utf-8'))
    if document['results'][0]['failure']['category']!='snapshot_mismatch':
        raise RuntimeError('Intentional maintenance did not reach reviewed screen mismatch')
    html=report.with_suffix('.html')
    diagnosis=run([binary,'report','--input',report,'--evidence-root',RAW,
                   '--output',html],'cookiecutter','diagnose-intentional-change',env=env)
    if 'snapshot_mismatch' not in html.read_text(encoding='utf-8'):
        raise RuntimeError('Diagnosis lacks actual failure category')
    update=run([binary,'test','--update','--snapshot','normal-project.txt',spec],
               'cookiecutter','selected-intentional-update',env=env)
    observed=baseline.read_text(encoding='utf-8')
    if 'Maintained Fixture' not in observed or 'maintained-fixture' not in observed:
        raise RuntimeError('Selected update omitted intended changed state')
    restore=run([binary,'test',spec],'cookiecutter','ordinary-maintained-pass',env=env)
    moved=app/'checkout with spaces café'
    moved.mkdir(exist_ok=False)
    shutil.copytree(directory/'fixtures',moved/'fixtures')
    shutil.copytree(directory/'snapshots',moved/'snapshots')
    moved_spec=moved/'normal-project.json'
    moved_spec.write_bytes(primary.read_bytes())
    relocation=run([binary,'test',moved_spec],'cookiecutter','relocated-checkout-spaces-unicode',env=env)
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    workflow=run([binary,'workflow','--source-revision',source,'--os','linux,windows',
        '--suite',str(primary.relative_to(ROOT)),'--setup',
        'python scripts/acceptance/adversarial_setup_cookiecutter.py','--build',
        'go build -o bin/playtestr ./cmd/playtestr','--print'],
        'cookiecutter','generated-workflow-preview',env=env)
    (directory/'workflow-template.yml').write_text(workflow['output'],encoding='utf-8')
    if {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [primary,primary_baseline]}!=original:
        raise RuntimeError('Maintenance altered the primary regression contract')
    result=dict(primary_contracts_unchanged=True,primary_hashes=original,
        old_maintenance_baseline_sha256=old,new_maintenance_baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
        mismatch=mismatch['id'],diagnosis=diagnosis['id'],selected_update=update['id'],
        maintained_pass=restore['id'],relocation=relocation['id'],workflow_preview=workflow['id'],
        hosted_execution='separate native workflow; generated template is preview only',
        manual_edit='Changed one text input in a separate ordinary JSON; all unrelated primary bytes preserved')
    (directory/'maintenance-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Manual maintenance, failure diagnosis, selected update and relocation passed')

if __name__=='__main__': main()
