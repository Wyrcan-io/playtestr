"""Exercise real failure diagnosis and public maintenance on the frozen candidate."""
import asyncio
import base64
import copy
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from next20_cargo_faults import NativeFaultCampaign
from readiness_evidence import immutable_json,sha256


async def main():
    project='cargo-generate';canonical=DOC/project;target=RAW/'active'/project
    freeze=json.loads((canonical/'development-test-freeze.json').read_text())
    for name,digest in freeze['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('frozen contract changed before maintenance')
    runner=executable('native-exit-v1');runtime=json.loads((target/'runtime.json').read_text());binary=Path(runtime['native'])
    if sha256(binary)!=runtime['native_sha256']:raise ValueError('pristine target executable not restored')
    root=RAW/project/('maintenance-'+uuid.uuid4().hex);package=root/'route';package.mkdir(parents=True)
    shutil.copytree(canonical/'fixture',package/'fixture');shutil.copytree(canonical/'snapshots',package/'snapshots')
    snapshot_hashes={p.relative_to(package).as_posix():sha256(p) for p in (package/'snapshots').rglob('*') if p.is_file()}
    env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(argv,label,expected=0,input=None,selected_campaign=None):
        result=await execute(argv,project,label,cwd=ROOT,env=env,timeout=140,expected=expected,input=input,campaign=selected_campaign or campaign)
        attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,selected_campaign=None):
        report=root/(label+'.report.json')
        await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec],label,expected,selected_campaign=selected_campaign)
        row=json.loads(report.read_text())['results'][0]
        if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('maintenance target/workspace cleanup incomplete')
        return row
    fault_root=RAW/project/'source-fault-development/v1';fault_summary=json.loads((fault_root/'summary.json').read_text())
    actual=next(r for r in fault_summary['observations'] if r['fault']=='F03')['mutated'];original_report=ROOT/actual['report']
    if sha256(original_report)!=actual['report_sha256'] or actual['category']!='state_assertion_failure':raise ValueError('actual source-fault report changed')
    # HTML deliberately refuses absolute evidence references. Preserve the first
    # absolute-layout report and capture a fresh actual fault with relative CLI
    # artifact arguments, as required by the documented offline report route.
    declaration_path=canonical/'fault-declaration.json';declaration=json.loads(declaration_path.read_text())
    fault=next(f for f in declaration['faults'] if f['id']=='F03');source=target/'src'/fault['path'];original_source=source.read_bytes()
    compiled_receipt=fault_root/'F03-compiled.json';compiled=json.loads(compiled_receipt.read_text())
    variant=ROOT/compiled['binary'];variant.resolve(strict=True).relative_to(target.resolve(strict=True))
    backup=target/'fault-builds/v1/original'/binary.name
    if sha256(variant)!=compiled['binary_sha256'] or sha256(backup)!=runtime['native_sha256'] or sha256(source)!=fault['original_source_sha256']:raise ValueError('original compiled fault/restoration inputs changed')
    try:
        source.write_bytes(original_source.replace(fault['before'].encode(),fault['after'].encode()))
        if sha256(source)!=fault['mutated_source_sha256']:raise ValueError('diagnostic source mutation differs')
        shutil.copyfile(variant,binary)
        inputs=[canonical/name for name in freeze['inputs']]+[declaration_path,canonical/'development-test-freeze.json',target/'build.json',target/'runtime.json']
        row=await test(canonical/'normal-project.json','cargo-diagnosis-relative-actual-source-fault',1,
            NativeFaultCampaign(binary,compiled_receipt,inputs))
        if row['failure']['category']!='state_assertion_failure':raise ValueError('relative diagnostic run did not detect actual saved corruption')
    finally:
        source.write_bytes(original_source);shutil.copyfile(backup,binary)
        if sha256(source)!=fault['original_source_sha256'] or sha256(binary)!=runtime['native_sha256']:raise ValueError('diagnostic source/executable restoration failed')
    diagnosis=root/'cargo-diagnosis-relative-actual-source-fault.report.json'
    html=root/'actual-source-fault.html'
    await run([runner,'report','--input',diagnosis.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),'--output',html.relative_to(ROOT)],'cargo-diagnosis-actual-source-fault-html')
    if 'synthetic-notes/profile.txt' not in html.read_text(encoding='utf-8') or 'state_assertion_failure' not in html.read_text(encoding='utf-8'):raise ValueError('HTML omitted useful saved-state diagnosis')
    await test(canonical/'normal-project.json','cargo-diagnosis-restored-recovery')
    spec=package/'maintained.json';data=json.loads((canonical/'normal-project.json').read_text())
    data['command'][0]=os.path.relpath(binary,package).replace('\\','/');immutable_json(spec,data)
    selected=next(i+1 for i,s in enumerate(data['steps']) if s.get('state',{}).get('path')=='synthetic-notes/profile.txt')
    seed=package/'fixture/template/profile.txt.liquid';original_seed=seed.read_bytes();revised=original_seed+b'reviewed=yes\n';seed.write_bytes(revised)
    row=await test(spec,'cargo-maintenance-intended-state-change',1)
    if row['failure']['category']!='state_assertion_failure':raise ValueError('intended fixture change did not reach saved bytes')
    await run([runner,'record','--edit',spec],'cargo-maintenance-selected-state-update',input=f'/update-state {selected}\n/review\n/replay\n/save\n')
    changed=json.loads(spec.read_text());expected=copy.deepcopy(data)
    expected['steps'][selected-1]['state']['bytes_base64']=base64.b64encode(b'project=synthetic-notes\nowner=Ada\nmode=basic\nreadme=true\nreviewed=yes\n').decode()
    if changed!=expected or any(sha256(package/name)!=digest for name,digest in snapshot_hashes.items()):raise ValueError('selected maintenance changed unrelated assertions or snapshots')
    await test(spec,'cargo-maintenance-selected-update-replay');saved=spec.read_bytes()
    seed.write_bytes(revised+b'cancelled=yes\n')
    await run([runner,'record','--edit',spec],'cargo-maintenance-cancelled-update',130,input=f'/update-state {selected}\n/quit\n')
    if spec.read_bytes()!=saved or any(sha256(package/name)!=digest for name,digest in snapshot_hashes.items()):raise ValueError('cancelled maintenance persisted changed approved bytes')
    seed.write_bytes(revised);await test(spec,'cargo-maintenance-cancel-restored-replay')
    suffix=package/'suffix.json'
    controls=['/expect Project Name','/text "synthetic-notes"','/key Enter','/expect Project owner','/text "Ada"','/key Enter',
        '/expect Project mode','/key Enter','/expect Include documentation','/key Enter','/expect New project created','/exit 0',
        '/rerecord 4','/text "Grace"','/key Enter','/expect Project mode','/key Enter','/expect Include documentation','/key Enter',
        '/expect New project created','/exit 0','/file synthetic-notes/profile.txt','/file synthetic-notes/README.md','/file sentinel.txt',
        '/entries synthetic-notes','/review','/replay','/save']
    argv=[runner,'record','--output',suffix,'--fixture','fixture','--temporary-home','--temporary-temp','--width','120','--height','24',
        '--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in data['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*data['command']]
    await run(argv,'cargo-maintenance-fresh-suffix-rerecord',input='\n'.join(controls+['']))
    rerecorded=json.loads(suffix.read_text());states={s['state']['path']:s['state'] for s in rerecorded['steps'] if s.get('state',{}).get('kind')=='file'}
    expected_profile=b'project=synthetic-notes\nowner=Grace\nmode=basic\nreadme=true\nreviewed=yes\n'
    if base64.b64decode(states['synthetic-notes/profile.txt']['bytes_base64'])!=expected_profile or any(s.get('text')=='Ada' for s in rerecorded['steps']):raise ValueError('rerecord retained discarded owner or wrong saved output')
    if base64.b64decode(states['synthetic-notes/README.md']['bytes_base64'])!=b'# synthetic-notes\n\nOwner: Grace\nMode: basic\n':raise ValueError('rerecorded README differs from independent expected output')
    await test(suffix,'cargo-maintenance-suffix-ordinary-replay')
    relocated=root/'relocated caf\u00e9 \u96ea';shutil.copytree(package,relocated)
    for selected_spec in [spec,suffix]:
        if sha256(relocated/selected_spec.name)!=sha256(selected_spec):raise ValueError('relocation changed reviewed contract bytes')
        await test(relocated/selected_spec.name,'cargo-relocated-'+selected_spec.stem)
    for name,digest in freeze['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('canonical frozen contract changed during maintenance')
    immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,runner_sha256=sha256(runner),
        actual_fault_report_sha256=sha256(diagnosis),original_absolute_layout_fault_report_sha256=sha256(original_report),
        additional_actual_mutation_probe=1,html_sha256=sha256(html),selected_state_step=selected,
        selected_update_controls=4,cancelled_update_controls=2,suffix_controls=len(controls),snapshot_hashes=snapshot_hashes,
        unrelated_assertions_preserved=True,maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),
        human_time='unmeasured',project_credits=0,workflow_status='Generated-workflow route remains pending the native preparation helper and real delivered CI.'))
    print('Actual-fault HTML diagnosis, selected/cancelled maintenance, suffix rerecord and unchanged-byte Unicode relocation passed.')


if __name__=='__main__':asyncio.run(main())
