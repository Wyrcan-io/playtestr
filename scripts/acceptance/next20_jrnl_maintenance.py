"""Public actual-fault diagnosis, selected maintenance, rerecord and relocation."""
import asyncio
import base64
import copy
import json
import os
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/jrnl';original_package=DOC/'jrnl';campaign=NextCampaign();env=environment(target)
    root=RAW/'jrnl'/('maintenance-'+uuid.uuid4().hex);root.mkdir()
    package=root/'reviewed route';package.mkdir()
    shutil.copytree(original_package/'fixture',package/'fixture')
    shutil.copytree(original_package/'snapshots',package/'snapshots')
    runner=RAW/'candidate/windows/playtestr.exe';attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'jrnl',label,cwd=ROOT,env=env,timeout=140,expected=expected,
            input=input,campaign=campaign)
        attempts.append(dict(label=label,id=result['id'],seconds=result['seconds']))
        return result
    async def test(spec,label,expected=0):
        report=root/(label+'.json');evidence=root/(label+'-evidence')
        await run([runner,'test','--report',report.relative_to(ROOT),
            '--artifacts-dir',evidence.relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        row=json.loads(report.read_text())['results'][0]
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:
            raise ValueError('public maintenance target/workspace cleanup incomplete')
        return report,row
    # Diagnose a real target source fault, rather than a changed expectation.
    fault=json.loads((original_package/'fault-declaration.json').read_text())['faults'][2]
    source=target/'src'/fault['path'];original=source.read_bytes()
    if original.count(fault['before'].encode())!=1:raise ValueError('diagnostic source anchor changed')
    try:
        source.write_bytes(original.replace(fault['before'].encode(),fault['after'].encode()))
        report,row=await test(original_package/'normal-delete.json','diagnosis-real-saved-corruption',1)
        if row['failure']['category']!='state_assertion_failure':raise ValueError('wrong real seeded-fault diagnosis')
        html=root/'diagnosis.html'
        await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),
            '--output',html.relative_to(ROOT)],'diagnosis-offline-html')
        rendered=html.read_text(encoding='utf-8')
        if 'journal.txt' not in rendered or 'state_assertion_failure' not in rendered:raise ValueError('HTML missing useful selected-state diagnosis')
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('diagnostic fault restoration failed')
    await test(original_package/'normal-delete.json','diagnosis-restored-recovery')
    # A reviewed synthetic input change intentionally changes only retained beta.
    spec=package/'maintained.json';data=json.loads((original_package/'normal-delete.json').read_text())
    python=json.loads((target/'runtime.json').read_text())['python']
    data['command'][0]=os.path.relpath(python,package).replace('\\','/')
    immutable_json(spec,data);approved=copy.deepcopy(data)
    fixture=package/'fixture/journal.txt';seed=fixture.read_bytes()
    revised=seed.replace(b'Second body.',b'Second body reviewed.')
    if revised==seed:raise ValueError('intentional fixture-change anchor missing')
    fixture.write_bytes(revised)
    _,row=await test(spec,'maintenance-intended-state-change',1)
    if row['failure']['category']!='state_assertion_failure':raise ValueError('intentional change did not reach file oracle')
    snapshot=package/'snapshots/normal-delete.txt';screen_hash=sha256(snapshot)
    await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-selected-state-update',
        input='/update-state 7\n/review\n/replay\n/save\n')
    changed=json.loads(spec.read_text());expected=b'[2020-01-02 10:15] beta retained.\nSecond body reviewed.\n'
    if base64.b64decode(changed['steps'][6]['state']['bytes_base64'])!=expected:raise ValueError('unreviewed selected update bytes')
    comparison=copy.deepcopy(changed);comparison['steps'][6]=approved['steps'][6]
    if comparison!=approved or sha256(snapshot)!=screen_hash:raise ValueError('selected update changed unrelated approvals')
    await test(spec,'maintenance-selected-update-replay')
    saved=spec.read_bytes()
    fixture.write_bytes(revised.replace(b'Second body reviewed.',b'Second body cancelled.'))
    await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-cancelled-update',expected=130,
        input='/update-state 7\n/quit\n')
    if spec.read_bytes()!=saved or sha256(snapshot)!=screen_hash:raise ValueError('cancelled maintenance changed approved bytes')
    fixture.write_bytes(revised)
    await test(spec,'maintenance-cancel-restored-replay')
    # Demonstrate technical suffix replacement in a separate reviewed contract.
    suffix=package/'suffix.json'
    controls=['/expect Delete entry','/text "y"','/key Enter','/expect 1 entry deleted','/exit 0',
        '/rerecord 1','/text "n"','/key Enter','/expect No edits to save, because nothing was changed',
        '/exit 0','/file journal.txt','/entries .','/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture','--temporary-home',
        '--temporary-temp','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in changed['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*changed['command']]
    await run(argv,'maintenance-fresh-suffix-rerecord',input='\n'.join(controls+['']))
    suffix_data=json.loads(suffix.read_text())
    state=next(s['state'] for s in suffix_data['steps'] if s.get('state',{}).get('kind')=='file')
    if base64.b64decode(state['bytes_base64'])!=revised:raise ValueError('rerecorded decline failed to preserve full journal')
    if any(s.get('text')=='y' for s in suffix_data['steps']):raise ValueError('discarded deletion input survived suffix rerecord')
    await test(suffix,'maintenance-suffix-ordinary-replay')
    relocated=root/'relocated café 雪';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        if sha256(relocated/selected.name)!=sha256(selected):raise ValueError('relocation changed reviewed contract')
        await test(relocated/selected.name,'relocated-'+selected.stem)
    workflow=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision','406169061ffb022c0fd0a4b1f99309836b6a96b1',
        '--os','linux,windows','--suite','docs/validation/runner-readiness-next-twenty-project-pass/jrnl/normal-delete.json',
        '--build','python -B scripts/acceptance/next20_jrnl_native_prepare.py',
        '--output',workflow.relative_to(ROOT)],'maintenance-generate-delivered-workflow')
    immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,
        real_fault_diagnostic_commands=2,selected_update_controls=4,cancelled_update_controls=2,
        suffix_controls=len(controls),unrelated_steps_preserved=True,snapshot_sha256=screen_hash,
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),
        generated_workflow_sha256=sha256(workflow),human_time='unmeasured',project_admitted=False,
        workflow_status='Generated private source-build route only; referenced target-preparation helper and future revision must exist/be reviewed before dispatch. No delivered CI execution credit.'))
    print('Actual-source-fault diagnosis, selected/cancelled updates, suffix replacement and unchanged-byte Unicode relocation passed. Generated workflow is not dispatched.')


if __name__=='__main__':asyncio.run(main())
