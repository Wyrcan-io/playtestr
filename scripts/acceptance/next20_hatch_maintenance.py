"""Exercise public diagnosis, selective/cancelled updates, rerecord and relocation."""
import asyncio
import base64
import copy
import json
import os
import shutil
import subprocess
import uuid

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC,RAW,ROOT,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    if os.name!='nt':raise ValueError('this local maintenance window is explicitly native Windows')
    canonical=DOC/'hatch';target=RAW/'active/hatch';runner=executable('native-exit-v1')
    root=RAW/'hatch'/('maintenance-'+uuid.uuid4().hex);package=root/'reviewed route';package.mkdir(parents=True)
    shutil.copytree(canonical/'fixtures/n01',package/'fixture');(package/'snapshots').mkdir()
    snapshot_name='normal-init-existing-tables.txt';shutil.copyfile(canonical/'snapshots'/snapshot_name,package/'snapshots'/snapshot_name)
    snapshot=package/'snapshots'/snapshot_name;snapshot_hash=sha256(snapshot)
    approved=json.loads((canonical/'n01.json').read_text());approved['workspace']['fixture']='fixture'
    approved['command'][0]=os.path.relpath(json.loads((target/'runtime.json').read_text())['python'],package).replace('\\','/')
    spec=package/'maintained.json';immutable_json(spec,approved)
    index=next(i for i,s in enumerate(approved['steps']) if s.get('state',{}).get('path')=='pyproject.toml')
    body=base64.b64decode(approved['steps'][index]['state']['bytes_base64'],validate=True)
    header='# Reviewed synthetic header.\n';cancelled='# Cancelled synthetic header.\n'
    immutable_json(root/'planned.json',dict(schema_version=1,canonical_spec_sha256=sha256(canonical/'n01.json'),
        expected_header_utf8=header,cancelled_header_utf8=cancelled,selected_state_number=index+1,
        independently_expected_suffix_description='Rerecorded description',source_restoration_required=True,
        scope='Prepared-agent maintenance and technical route, not beginner timing or final qualification. Canonical86 inputs remain unchanged.'))
    campaign=NextCampaign();env=environment(target);attempts=[];reports=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'hatch',label,cwd=ROOT,env=env,timeout=180,expected=expected,input=input,campaign=campaign)
        attempts.append(dict(id=result['id'],label=label,seconds=result['seconds']));return result
    async def test(selected,label,expected=0):
        report=root/(label+'.report.json')
        await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/(label+'-evidence')).relative_to(ROOT),selected.relative_to(ROOT)],label,expected)
        row=json.loads(report.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('maintenance target/workspace cleanup incomplete')
        if expected==0 and (row['status']!='passed' or any(s['status']!='passed' for s in row['steps'])):raise ValueError('maintenance positive case incomplete')
        reports.append(dict(label=label,report=report.relative_to(ROOT).as_posix(),sha256=sha256(report),invocation=row['invocation_id'],category=row.get('failure',{}).get('category')))
        return report,row
    fault=json.loads((canonical/'fault-declaration.json').read_text())['faults'][2]
    source=target/'src'/fault['path'];original=source.read_bytes()
    if original.count(fault['before'].encode())!=1:raise ValueError('saved fault anchor not unique')
    try:
        source.write_bytes(original.replace(fault['before'].encode(),fault['after'].encode()))
        report,row=await test(spec,'hatch-diagnosis-real-wrong-build-requirement',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('real saved fault not behind positive terminal/exit/snapshot')
        html=root/'diagnosis.html'
        await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),'--output',html.relative_to(ROOT)],'hatch-diagnosis-offline-html')
        text=html.read_text(encoding='utf-8')
        if 'state_assertion_failure' not in text or 'pyproject.toml' not in text:raise ValueError('useful saved-file diagnosis missing')
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('diagnostic source restoration failed')
    await test(spec,'hatch-diagnosis-restored-recovery')
    anchor=b'f.write(tomlkit.dumps(raw_config))'
    if original.count(anchor)!=1:raise ValueError('intended formatting writer not unique')
    def formatted(comment):return original.replace(anchor,('f.write('+repr(comment)+' + tomlkit.dumps(raw_config))').encode())
    try:
        source.write_bytes(formatted(header))
        _,row=await test(spec,'hatch-maintenance-intended-comment',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('intended comment not isolated to selected file')
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'hatch-maintenance-selected-update',input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
        changed=json.loads(spec.read_text());expected=copy.deepcopy(approved)
        expected['steps'][index]['state']['bytes_base64']=base64.b64encode(header.replace('\n',os.linesep).encode()+body).decode()
        if changed!=expected or sha256(snapshot)!=snapshot_hash:raise ValueError('selected update changed unrelated approvals or unexpected bytes')
        await test(spec,'hatch-maintenance-selected-replay');saved=spec.read_bytes()
        source.write_bytes(formatted(cancelled))
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'hatch-maintenance-cancelled-update',130,input=f'/update-state {index+1}\n/quit\n')
        if spec.read_bytes()!=saved or sha256(snapshot)!=snapshot_hash:raise ValueError('cancelled update changed approved bytes')
        source.write_bytes(formatted(header));await test(spec,'hatch-maintenance-cancel-restored-replay')
        relocated=root/'relocated caf\u00e9 \u96ea';shutil.copytree(package,relocated)
        if sha256(relocated/spec.name)!=sha256(spec):raise ValueError('relocation changed spec')
        await test(relocated/spec.name,'hatch-relocated-maintained')
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('formatting source restoration failed')
    suffix=package/'suffix.json'
    controls=['/expect Description','/text "Original description"','/expect Original description','/key Enter',
        '/expect Updated: pyproject.toml','/exit 0','/rerecord 1','/text "Rerecorded description"','/expect Rerecorded description','/key Enter',
        '/expect Updated: pyproject.toml','/exit 0','/file pyproject.toml','/file hatch.toml','/file sentinel.txt','/entries .','/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','120','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in approved['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*approved['command']]
    await run(argv,'hatch-maintenance-fresh-suffix-rerecord',input='\n'.join(controls+['']))
    rerecorded=json.loads(suffix.read_text());selected=next(s['state'] for s in rerecorded['steps'] if s.get('state',{}).get('path')=='pyproject.toml')
    expected=body.replace(b'"Synthetic package"',b'"Rerecorded description"')
    if body.count(b'"Synthetic package"')!=1 or base64.b64decode(selected['bytes_base64'],validate=True)!=expected or any(s.get('text')=='Original description' for s in rerecorded['steps']):raise ValueError('rerecord retained discarded input or wrong complete metadata')
    await test(suffix,'hatch-maintenance-suffix-ordinary');shutil.copyfile(suffix,relocated/'suffix.json')
    if sha256(suffix)!=sha256(relocated/'suffix.json'):raise ValueError('relocated suffix differs')
    await test(relocated/'suffix.json','hatch-relocated-suffix')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();workflow=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision',revision,'--os','linux','--suite','artifacts/'+RAW.name+'/hatch/host-contracts/n01.json',
        '--build','python -B scripts/acceptance/next20_jrnl_native_prepare.py --project hatch','--output',workflow.relative_to(ROOT)],'hatch-public-free-workflow-generation')
    for name,digest in json.loads((canonical/'development-test-freeze.json').read_text())['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('canonical frozen input changed')
    immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,reports=reports,runner_sha256=sha256(runner),
        diagnostic_commands=2,html_sha256=sha256(html),selected_state_number=index+1,selected_update_controls=4,cancelled_update_controls=2,
        unrelated_approved_bytes_preserved=True,snapshot_sha256=snapshot_hash,suffix_controls=len(controls),suffix_sha256=sha256(suffix),
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),generated_workflow_sha256=sha256(workflow),workflow_dispatched=False,
        source_restored=True,human_time='unmeasured',human_participants=0,project_admissions=0,final_ordinary_credit=0,
        scope='Actual public diagnosis/maintenance/rerecord/relocation and generation only. Workflow explicitly builds host profile from committed canonical inputs; no delivered-CI execution claim.'))
    print('Hatch real-fault HTML diagnosis, selective/cancelled updates, suffix rerecord, Unicode relocation and generated workflow passed; all target source restored.')


if __name__=='__main__':asyncio.run(main())
