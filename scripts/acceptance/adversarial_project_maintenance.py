"""Public manual-edit, selected-update, diagnosis, relocation and workflow routes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from adversarial_process import ROOT,DOC,RAW,run

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--binary',type=Path)
    parser.add_argument('--text-step',type=int,required=True)
    parser.add_argument('--new-text',required=True)
    parser.add_argument('--new-visible',required=True)
    parser.add_argument('--checkpoint-step',type=int,action='append',default=[])
    parser.add_argument('--new-checkpoint',action='append',default=[])
    args=parser.parse_args()
    project=args.project
    directory=DOC/project
    app=args.runtime or ROOT/'.cache/ten-new-project-apps'/project
    identity=json.loads((app/'runtime.json').read_text())
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
    binary=args.binary or ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr-linux')
    primary=directory/'normal-project.json'
    primary_value=json.loads(primary.read_text(encoding='utf-8'))
    snapshot_name=next(step['snapshot'] for step in primary_value['steps'] if 'snapshot' in step)
    primary_baseline=directory/'snapshots'/snapshot_name
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [primary,primary_baseline]}
    maintenance=directory/'maintenance'/str(time.time_ns())
    maintenance.mkdir(parents=True,exist_ok=False)
    shutil.copytree(directory/'fixtures',maintenance/'fixtures')
    (maintenance/'snapshots').mkdir()
    baseline=maintenance/'snapshots'/snapshot_name
    baseline.write_bytes(primary_baseline.read_bytes())
    spec=maintenance/'intentional-name-change.json'
    value=json.loads(primary.read_text(encoding='utf-8'))
    value['name']='Reviewed intentional workflow change'
    if args.text_step<1 or args.text_step>len(value['steps']) or 'text' not in value['steps'][args.text_step-1]:
        raise RuntimeError('Selected maintenance step is not an actual text input')
    value['steps'][args.text_step-1]['text']=args.new_text
    if len(args.checkpoint_step)!=len(args.new_checkpoint) or len(set(args.checkpoint_step))!=len(args.checkpoint_step):
        raise RuntimeError('Associated checkpoint edits require paired explicit arguments and unique positions')
    for position,checkpoint in zip(args.checkpoint_step,args.new_checkpoint):
        if not 1<=position<=len(value['steps']) or 'expect' not in value['steps'][position-1]:
            raise RuntimeError('Selected associated checkpoint is not an actual text assertion')
        value['steps'][position-1]['expect']=checkpoint
    spec.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    old=hashlib.sha256(baseline.read_bytes()).hexdigest()
    report=RAW/project/('intentional-name-mismatch-'+str(time.time_ns())+'.json')
    mismatch=run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
                 project,'intended-change-ordinary-mismatch',env=env,expected=1)
    document=json.loads(report.read_text(encoding='utf-8'))
    if document['results'][0]['failure']['category']!='snapshot_mismatch':
        raise RuntimeError('Intentional maintenance did not reach reviewed screen mismatch')
    html=report.with_suffix('.html')
    diagnosis=run([binary,'report','--input',report,'--evidence-root',RAW,
                   '--output',html],project,'diagnose-intentional-change',env=env)
    if 'snapshot_mismatch' not in html.read_text(encoding='utf-8'):
        raise RuntimeError('Diagnosis lacks actual failure category')
    update=run([binary,'test','--update','--snapshot',snapshot_name,spec],
               project,'selected-intentional-update',env=env)
    observed=baseline.read_text(encoding='utf-8')
    if args.new_text not in observed or args.new_visible not in observed:
        raise RuntimeError('Selected update omitted intended changed state')
    restore=run([binary,'test',spec],project,'ordinary-maintained-pass',env=env)
    moved=app/('checkout with spaces café '+maintenance.name)
    moved.mkdir(exist_ok=False)
    shutil.copytree(directory/'fixtures',moved/'fixtures')
    shutil.copytree(directory/'snapshots',moved/'snapshots')
    moved_spec=moved/'normal-project.json'
    moved_spec.write_bytes(primary.read_bytes())
    relocation=run([binary,'test',moved_spec],project,'relocated-checkout-spaces-unicode',env=env)
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    candidate=next(c for c in json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))
                   if c['repo'].split('/')[-1]==project)
    setup='python scripts/acceptance/'+('adversarial_setup_go.py' if identity.get('toolchain','').startswith('go version')
          else 'adversarial_setup_rust.py' if identity.get('toolchain','').startswith('rustc ')
          else 'adversarial_setup_cookiecutter.py')+' --project '+project
    setup+='\npython scripts/acceptance/adversarial_export_target_path.py --project '+project
    workflow=run([binary,'workflow','--source-revision',source,'--os',','.join(candidate['planned_hosts']),
        '--suite',str(primary.relative_to(ROOT)),'--setup',
        setup,'--build',
        'true','--print'],
        project,'generated-workflow-preview',env=env)
    (directory/'workflow-template.yml').write_text(workflow['output'],encoding='utf-8')
    if {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [primary,primary_baseline]}!=original:
        raise RuntimeError('Maintenance altered the primary regression contract')
    result=dict(primary_contracts_unchanged=True,primary_hashes=original,
        old_maintenance_baseline_sha256=old,new_maintenance_baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
        mismatch=mismatch['id'],diagnosis=diagnosis['id'],selected_update=update['id'],
        maintained_pass=restore['id'],relocation=relocation['id'],workflow_preview=workflow['id'],
        hosted_execution='separate native workflow; generated template is preview only',
        target_build='The explicit owned setup recipe already builds/installs the target; the separate build command is intentionally unnecessary',
        manual_edit='Changed one text input and, when explicitly selected, its associated positive checkpoint in a separate ordinary JSON; all primary bytes preserved',
        associated_checkpoint_step=args.checkpoint_step[0] if len(args.checkpoint_step)==1 else None,
        associated_checkpoint_steps=args.checkpoint_step)
    (directory/'maintenance-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Manual maintenance, failure diagnosis, selected update and relocation passed')

if __name__=='__main__': main()
