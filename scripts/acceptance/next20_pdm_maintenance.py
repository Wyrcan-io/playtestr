"""Exercise actual saved-fault diagnosis and selective public PDM maintenance."""
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
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    canonical=DOC/'pdm';target=RAW/'active/pdm';runner=executable('native-exit-v1')
    root=RAW/'pdm'/('maintenance-'+uuid.uuid4().hex);root.mkdir()
    package=root/'reviewed route';package.mkdir()
    shutil.copytree(canonical/'fixture',package/'fixture');shutil.copytree(canonical/'snapshots',package/'snapshots')
    env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'pdm',label,cwd=ROOT,env=env,timeout=180,expected=expected,input=input,campaign=campaign)
        attempts.append(dict(id=result['id'],label=label,seconds=result['seconds']));return result
    async def test(spec,label,expected=0):
        report=root/(label+'.report.json')
        await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        row=json.loads(report.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('maintenance cleanup incomplete')
        return report,row
    spec=package/'maintained.json';data=json.loads((canonical/'normal-minimal-runtime-v2.json').read_text())
    python=json.loads((target/'runtime.json').read_text())['python']
    data['command'][0]=os.path.relpath(python,package).replace('\\','/')
    immutable_json(spec,data);approved=copy.deepcopy(data)
    index=next(i for i,s in enumerate(data['steps']) if s.get('state',{}).get('path')=='pyproject.toml')
    body=base64.b64decode(data['steps'][index]['state']['bytes_base64'],validate=True)
    snapshot=package/'snapshots/normal-minimal-runtime-v2.txt';snapshot_hash=sha256(snapshot)
    fault=json.loads((canonical/'fault-declaration.json').read_text())['faults'][2]
    source=target/'src'/fault['path'];original=source.read_bytes();anchor=fault['before'].encode()
    if original.count(anchor)!=1:raise ValueError('writer mutation anchor changed')
    try:
        source.write_bytes(original.replace(anchor,fault['after'].encode()))
        report,row=await test(spec,'pdm-diagnosis-real-wrong-name',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):
            raise ValueError('saved fault did not follow positive terminal/exit/snapshot')
        html=root/'diagnosis.html'
        await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),
            '--output',html.relative_to(ROOT)],'pdm-diagnosis-offline-html')
        text=html.read_text(encoding='utf-8')
        if 'state_assertion_failure' not in text or 'pyproject.toml' not in text:raise ValueError('missing useful saved-file diagnosis')
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('diagnostic source restoration failed')
    await test(spec,'pdm-diagnosis-restored-recovery')
    header='# Reviewed synthetic header.\n';cancelled='# Cancelled synthetic header.\n'
    def formatting(comment):
        return original.replace(anchor,('fp.write('+repr(comment)+' + tomlkit.dumps(content))').encode())
    immutable_json(root/'intended-formatting-change.json',dict(source=source.relative_to(ROOT).as_posix(),
        original_sha256=sha256(source),expected_header_utf8=header,
        scope='Explicit synthetic TOML-comment formatting change, not a product correction or final source. Terminal and semantic metadata remain unchanged.'))
    try:
        source.write_bytes(formatting(header))
        _,row=await test(spec,'pdm-maintenance-intended-comment',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):
            raise ValueError('intended change did not reach selected file oracle')
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'pdm-maintenance-selected-update',
            input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
        changed=json.loads(spec.read_text());expected=copy.deepcopy(approved)
        expected['steps'][index]['state']['bytes_base64']=base64.b64encode(header.replace('\n',os.linesep).encode()+body).decode()
        if changed!=expected or sha256(snapshot)!=snapshot_hash:raise ValueError('selected update changed unrelated approval or wrong bytes')
        await test(spec,'pdm-maintenance-selected-replay');saved=spec.read_bytes()
        source.write_bytes(formatting(cancelled))
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'pdm-maintenance-cancelled-update',130,
            input=f'/update-state {index+1}\n/quit\n')
        if spec.read_bytes()!=saved or sha256(snapshot)!=snapshot_hash:raise ValueError('cancelled update persisted approval')
        source.write_bytes(formatting(header));await test(spec,'pdm-maintenance-cancel-restored-replay')
        relocated=root/'relocated caf\u00e9 \u96ea';shutil.copytree(package,relocated)
        if sha256(relocated/spec.name)!=sha256(spec):raise ValueError('relocation changed reviewed spec')
        await test(relocated/spec.name,'pdm-relocated-maintained')
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('formatting source restoration failed')
    suffix=package/'suffix.json'
    controls=['/expect Project version','/key Enter','/key Enter','/key Enter','/text "Ada"','/key Enter',
        '/text "ada@example.invalid"','/key Enter','/text ">=3.10"','/key Enter',
        '/expect Project is initialized successfully','/exit 0','/rerecord 4','/text "Grace"','/key Enter',
        '/text "ada@example.invalid"','/key Enter','/text ">=3.10"','/key Enter',
        '/expect Project is initialized successfully','/exit 0','/file pyproject.toml','/file sentinel.txt',
        '/file .git/config','/entries .','/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','120','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in data['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*data['command']]
    await run(argv,'pdm-maintenance-fresh-suffix-rerecord',input='\n'.join(controls+['']))
    rerecorded=json.loads(suffix.read_text())
    saved=next(s['state'] for s in rerecorded['steps'] if s.get('state',{}).get('path')=='pyproject.toml')
    if body.count(b'"Ada"')!=1 or base64.b64decode(saved['bytes_base64'],validate=True)!=body.replace(b'"Ada"',b'"Grace"'):
        raise ValueError('suffix owner differs from independent complete expected bytes')
    if any(s.get('text')=='Ada' for s in rerecorded['steps']):raise ValueError('discarded author survived rerecord')
    await test(suffix,'pdm-maintenance-suffix-ordinary')
    relocated_suffix=relocated/'suffix.json';shutil.copyfile(suffix,relocated_suffix)
    if sha256(suffix)!=sha256(relocated_suffix):raise ValueError('suffix relocation changed bytes')
    await test(relocated_suffix,'pdm-relocated-suffix')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    workflow=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision',revision,'--os','linux,windows','--suite',
        'docs/validation/runner-readiness-next-twenty-project-pass/pdm/normal-minimal-runtime-v2.json',
        '--build','python -B scripts/acceptance/next20_jrnl_native_prepare.py --project pdm',
        '--output',workflow.relative_to(ROOT)],'pdm-public-free-workflow-generation')
    for name,digest in json.loads((canonical/'development-test-freeze.json').read_text())['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('canonical frozen input changed')
    immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,runner_sha256=sha256(runner),
        actual_fault_report_sha256=sha256(report),html_sha256=sha256(html),real_fault_diagnostic_commands=2,
        selected_update_controls=4,cancelled_update_controls=2,suffix_controls=len(controls),selected_state_number=index+1,
        unrelated_approved_bytes_preserved=True,snapshot_sha256=snapshot_hash,
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),
        suffix_sha256=sha256(suffix),workflow_sha256=sha256(workflow),workflow_dispatched=False,
        source_restored=True,historical_screen_gap_open=True,project_admissions=0,human_time='unmeasured'))
    print('Actual-fault HTML diagnosis, selected/cancelled update, suffix rerecord, Unicode relocation and generated workflow passed; source restored. No admission.')


if __name__=='__main__':asyncio.run(main())
