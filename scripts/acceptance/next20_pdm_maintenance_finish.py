"""Finish workflow generation without repeating completed maintenance checks."""
import argparse
import asyncio
import base64
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--wrapper',required=True);args=parser.parse_args()
    root=args.root.resolve(strict=True);root.relative_to((RAW/'pdm').resolve(strict=True))
    if not root.name.startswith('maintenance-') or (root/'journey.json').exists():raise ValueError('existing/unexpected maintenance root')
    canonical=DOC/'pdm';target=RAW/'active/pdm';runner=executable('native-exit-v1')
    wanted={'pdm-diagnosis-real-wrong-name':'state_assertion_failure','pdm-diagnosis-restored-recovery':None,
        'pdm-maintenance-intended-comment':'state_assertion_failure','pdm-maintenance-selected-replay':None,
        'pdm-maintenance-cancel-restored-replay':None,'pdm-relocated-maintained':None,
        'pdm-maintenance-suffix-ordinary':None,'pdm-relocated-suffix':None}
    reports=[]
    for label,category in wanted.items():
        path=root/(label+'.report.json');row=json.loads(path.read_text())['results'][0]
        if row.get('failure',{}).get('category')!=category or row['status']!=('failed' if category else 'passed'):
            raise ValueError('existing maintenance outcome differs')
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('existing maintenance cleanup incomplete')
        if not category and any(s['status']!='passed' for s in row['steps']):raise ValueError('nonpositive existing steps')
        reports.append(dict(label=label,sha256=sha256(path),invocation=row['invocation_id'],category=category))
    package=root/'reviewed route';spec=package/'maintained.json';suffix=package/'suffix.json'
    data=json.loads((canonical/'normal-minimal-runtime-v2.json').read_text());original=copy.deepcopy(data)
    index=next(i for i,s in enumerate(data['steps']) if s.get('state',{}).get('path')=='pyproject.toml')
    body=base64.b64decode(data['steps'][index]['state']['bytes_base64'],validate=True)
    data['command'][0]=os.path.relpath(json.loads((target/'runtime.json').read_text())['python'],package).replace('\\','/')
    data['steps'][index]['state']['bytes_base64']=base64.b64encode(b'# Reviewed synthetic header.\r\n'+body).decode()
    if json.loads(spec.read_text())!=data or sha256(spec)!=sha256(root/'relocated caf\u00e9 \u96ea/maintained.json'):
        raise ValueError('maintained/relocated approvals changed')
    rerecorded=json.loads(suffix.read_text());state=next(s['state'] for s in rerecorded['steps'] if s.get('state',{}).get('path')=='pyproject.toml')
    if base64.b64decode(state['bytes_base64'])!=body.replace(b'"Ada"',b'"Grace"') or any(s.get('text')=='Ada' for s in rerecorded['steps']):raise ValueError('wrong suffix bytes')
    if sha256(suffix)!=sha256(root/'relocated caf\u00e9 \u96ea/suffix.json'):raise ValueError('relocated suffix changed')
    snapshot='snapshots/normal-minimal-runtime-v2.txt'
    if sha256(package/snapshot)!=sha256(canonical/snapshot):raise ValueError('unrelated snapshot changed')
    provenance=json.loads((canonical/'source-provenance.json').read_text())
    for name,digest in provenance['files'].items():
        if sha256(target/'src'/name)!=digest:raise ValueError('primary source not restored')
    start=json.loads((RAW/'events'/(args.wrapper+'-started.json')).read_text())
    finish=json.loads((RAW/'events'/(args.wrapper+'-finished.json')).read_text())
    if start['label']!='pdm-public-maintenance-corrected-suffix-boundary' or finish['exit_code']!=1:raise ValueError('wrong retained partial wrapper')
    lower=datetime.fromisoformat(start['utc']);upper=(RAW/'events'/(args.wrapper+'-finished.json')).stat().st_mtime
    attempts=[]
    for path in (RAW/'events').glob('*-started.json'):
        value=json.loads(path.read_text())
        if value['project']!='pdm' or not lower.timestamp()<=datetime.fromisoformat(value['utc']).timestamp()<=upper:continue
        ended=json.loads((RAW/'events'/(value['id']+'-finished.json')).read_text())
        if ended['cleanup_errors'] or ended['harness_cleanup']!='harness_process_reaped':raise ValueError('partial journey harness cleanup incomplete')
        attempts.append(dict(id=value['id'],label=value['label'],exit_code=ended['exit_code'],category=ended['category'],seconds=ended['seconds']))
    labels={r['label'] for r in attempts}
    if len(attempts)!=13 or labels!=set(wanted)|{'pdm-diagnosis-offline-html','pdm-maintenance-selected-update',
            'pdm-maintenance-cancelled-update','pdm-maintenance-fresh-suffix-rerecord','pdm-public-free-workflow-generation'}:
        raise ValueError('partial journey attempt window differs; no guessed commands')
    failed=next(r for r in attempts if r['label']=='pdm-public-free-workflow-generation')
    if failed['exit_code']!=2 or failed['category']!='exit_mismatch':raise ValueError('original workflow refusal differs')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();workflow=root/'generated-workflow.yml'
    result=await execute([runner,'workflow','--source-revision',revision,'--os','linux,windows','--suite',
        'docs/validation/runner-readiness-next-twenty-project-pass/pdm/normal-minimal-runtime-v2.json',
        '--build','python -B scripts/acceptance/next20_jrnl_native_prepare.py --project pdm',
        '--output',workflow.relative_to(ROOT)],'pdm','pdm-public-free-workflow-generation-with-build',
        cwd=ROOT,env=environment(target),timeout=90,campaign=NextCampaign())
    immutable_json(root/'journey.json',dict(schema_version=1,reports=reports,attempts=attempts,
        completion_attempt=result['id'],partial_wrapper=args.wrapper,original_workflow_refusal_preserved=True,
        runner_sha256=sha256(runner),generated_workflow_sha256=sha256(workflow),workflow_dispatched=False,
        maintained_spec_sha256=sha256(spec),suffix_spec_sha256=sha256(suffix),unrelated_approved_bytes_preserved=True,
        source_restored=True,real_fault_diagnostic_commands=2,selected_update_controls=4,cancelled_update_controls=2,
        suffix_controls=28,historical_screen_gap_open=True,project_admissions=0,human_time='unmeasured',
        scope='Completed the separate generation command after actual verification of the already executed maintenance window; no target checks rerun or earlier failed commands overwritten.'))
    print('Read back8 actual maintenance reports and13 original attempts; generated workflow with documented build argument; no target replay or admission.')


if __name__=='__main__':asyncio.run(main())
