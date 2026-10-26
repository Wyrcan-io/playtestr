"""Exercise actual public yo diagnosis, approval, cancellation and relocation."""
import asyncio
import base64
import copy
import hashlib
import json
import os
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign
from next20_yo_assemble import assemble
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    project='yo';canonical=DOC/project;target=RAW/'active'/project
    root=RAW/project/('maintenance-'+uuid.uuid4().hex);root.mkdir()
    package=root/'reviewed route';package.mkdir()
    for name in ['fixture','snapshots']:shutil.copytree(canonical/name,package/name)
    runner=RAW/'candidate/windows/playtestr.exe';env=environment(target);campaign=NextCampaign()
    attempts=[];assemblies=[]
    async def run(argv,label,expected=0,input=None):
        value=await execute(argv,project,label,cwd=ROOT,env=env,expected=expected,input=input,timeout=180,campaign=campaign)
        attempts.append(dict(id=value['id'],label=label,seconds=value['seconds']));return value
    async def test(spec,label,expected=0):
        report=root/(label+'.json')
        await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        row=json.loads(report.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:
            raise ValueError('Actual public maintenance cleanup incomplete')
        return row
    provenance=json.loads((canonical/'source-provenance.json').read_text())
    fault=json.loads((canonical/'fault-declaration.json').read_text())['faults'][2]
    source=target/'src'/fault['path'];original=source.read_bytes()
    async def variant(content,label):
        source.write_bytes(content)
        expected=dict(provenance['files']);expected[fault['path']]=hashlib.sha256(content).hexdigest()
        proof=await assemble(expected,label);assemblies.append(proof)
    spec=package/'maintained.json';data=json.loads((canonical/'normal-javascript.json').read_text())
    runtime=json.loads((target/'runtime.json').read_text())
    data['command'][0]=os.path.relpath(runtime['node'],package).replace('\\','/')
    immutable_json(spec,data);approved=copy.deepcopy(data)
    index=next(i for i,s in enumerate(data['steps']) if s.get('state',{}).get('path')=='output/project.json')
    expected=base64.b64decode(data['steps'][index]['state']['bytes_base64'])
    snapshot=package/'snapshots/javascript-complete.txt';snapshot_hash=sha256(snapshot)
    anchor=fault['before'].encode()
    if original.count(anchor)!=1:raise ValueError('Actual source anchor changed')
    def formatted(suffix):
        return original.replace(anchor,anchor+b"\n      fs.appendFileSync(path.resolve('output/project.json'), "+json.dumps(suffix).encode()+b');')
    immutable_json(root/'intended-formatting-change.json',dict(schema_version=1,source=fault['path'],
        original_sha256=hashlib.sha256(original).hexdigest(),before=anchor.decode(),
        after=(anchor+b"\n      fs.appendFileSync(path.resolve('output/project.json'), \"\\n\");").decode(),
        scope='Explicit intended extra trailing newline after unchanged valid JSON; no upstream release or calibration credit.'))
    try:
        await variant(original.replace(anchor,fault['after'].encode()),'maintenance-diagnostic-source-copy')
        row=await test(canonical/'normal-project.json','diagnosis-real-saved-json-corruption',1)
        if row['failure']['category']!='state_assertion_failure':raise ValueError('Wrong actual diagnosis category')
        await run([runner,'report','--input',(root/'diagnosis-real-saved-json-corruption.json').relative_to(ROOT),
            '--evidence-root',root.relative_to(ROOT),'--output',(root/'diagnosis.html').relative_to(ROOT)],'diagnosis-offline-html')
        html=(root/'diagnosis.html').read_text(encoding='utf-8')
        if 'state_assertion_failure' not in html or 'project.json' not in html:raise ValueError('Missing useful rendered diagnosis')
        await variant(original,'maintenance-diagnostic-original-copy')
        await test(canonical/'normal-project.json','diagnosis-restored-recovery')
        await variant(formatted('\n'),'maintenance-intended-format-copy')
        row=await test(spec,'maintenance-intended-newline-change',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):
            raise ValueError('Intended formatting failed before approved terminal and exit')
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-selected-file-update',
            input='/update-state '+str(index+1)+'\n/review\n/replay\n/save\n')
        changed=json.loads(spec.read_text());comparison=copy.deepcopy(changed)
        comparison['steps'][index]=approved['steps'][index]
        if comparison!=approved or base64.b64decode(changed['steps'][index]['state']['bytes_base64'])!=expected+b'\n' or sha256(snapshot)!=snapshot_hash:
            raise ValueError('Selected update changed unrelated approvals or captured wrong JSON')
        await test(spec,'maintenance-selected-update-replay');saved=spec.read_bytes()
        await variant(formatted('\n\n'),'maintenance-cancelled-format-copy')
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-cancelled-file-update',expected=130,
            input='/update-state '+str(index+1)+'\n/quit\n')
        if spec.read_bytes()!=saved or sha256(snapshot)!=snapshot_hash:raise ValueError('Cancelled approval changed reviewed bytes')
        await variant(formatted('\n'),'maintenance-approved-format-recovery-copy')
        await test(spec,'maintenance-cancel-restored-replay')
        controls=json.loads((RAW/project/'snapshot-authoring-planned.json').read_text())['controls']
        controls=[c.replace('/snapshot javascript-complete.txt','/snapshot discarded-before-cancel.txt') for c in controls[:-3]]
        controls+=['/rerecord 1','/expect Project label','/key CtrlC','/exit 1','/missing output','/file sentinel.txt','/review','/replay','/save']
        suffix=package/'suffix.json'
        argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
            '--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
        for name,value in data['env'].items():argv+=['--env',name+'='+value]
        for name in data['inherit_env']:argv+=['--inherit-env',name]
        await run([*argv,'--',*data['command']],'maintenance-suffix-rerecord-cancellation',input='\n'.join(controls+['']))
        replaced=json.loads(suffix.read_text())
        if any(s.get('key')=='Enter' or 'snapshot' in s for s in replaced['steps']) or (package/'snapshots/discarded-before-cancel.txt').exists():
            raise ValueError('Discarded completion steps or snapshot survived cancellation suffix')
        await test(suffix,'maintenance-suffix-ordinary-replay')
        relocated=root/'relocated café 雪';shutil.copytree(package,relocated)
        for selected in [spec,suffix]:
            if sha256(selected)!=sha256(relocated/selected.name):raise ValueError('Relocation edited approved contract')
            await test(relocated/selected.name,'relocated-'+selected.stem)
        immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,source_assemblies=assemblies,
            real_fault_diagnostic_public_commands=2,assembly_operations_separate=True,compiler_execution=False,
            selected_state_number=index+1,selected_update_controls=4,cancelled_update_controls=2,suffix_controls=len(controls),
            snapshot_sha256=snapshot_hash,maintained_spec_sha256=sha256(spec),suffix_spec_sha256=sha256(suffix),
            relocated_spec_sha256=sha256(relocated/spec.name),unrelated_steps_preserved=True,
            intentional_source_variant='Extra trailing newline only, not upstream release or calibration credit.',
            human_time='unmeasured',project_admitted=False))
    finally:
        await variant(original,'maintenance-final-original-source-copy')
        if source.read_bytes()!=original:raise ValueError('Actual source not exactly restored')
    print('Public diagnosis, selected/cancelled approval, suffix pruning and unchanged Unicode relocation passed; actual interpreted source restored.')


if __name__=='__main__':asyncio.run(main())
