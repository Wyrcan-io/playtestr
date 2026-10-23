"""Measured diagnosis, selected update, cancellation, suffix and relocation."""
import asyncio
import base64
import copy
import json
import os
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    project='commitizen-python';canonical=DOC/project;target=RAW/'active'/project
    root=RAW/project/('maintenance-'+uuid.uuid4().hex);root.mkdir()
    package=root/'reviewed route';package.mkdir();shutil.copytree(canonical/'fixture',package/'fixture');shutil.copytree(canonical/'snapshots',package/'snapshots')
    runner=RAW/'candidate/windows/playtestr.exe';env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(argv,label,expected=0,input=None):
        value=await execute(argv,project,label,cwd=ROOT,env=env,expected=expected,input=input,timeout=180,campaign=campaign)
        attempts.append(dict(id=value['id'],label=label,seconds=value['seconds']));return value
    async def test(spec,label,expected=0):
        path=root/(label+'.json')
        await run([runner,'test','--report',path.relative_to(ROOT),'--artifacts-dir',(root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        row=json.loads(path.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('public journey cleanup incomplete')
        return path,row
    faults=json.loads((canonical/'fault-declaration.json').read_text())['faults'];fault=faults[2]
    source=target/'src'/fault['path'];original=source.read_bytes()
    try:
        if original.count(fault['before'].encode())!=1:raise ValueError('diagnostic source anchor changed')
        source.write_bytes(original.replace(fault['before'].encode(),fault['after'].encode()))
        failed,row=await test(canonical/'normal-init-portable.json','diagnosis-real-saved-tag-corruption',1)
        if row['failure']['category']!='state_assertion_failure':raise ValueError('wrong public diagnosis category')
        html=root/'diagnosis.html'
        await run([runner,'report','--input',failed.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),'--output',html.relative_to(ROOT)],'diagnosis-offline-html')
        if 'state_assertion_failure' not in html.read_text(encoding='utf-8') or '.cz.toml' not in html.read_text(encoding='utf-8'):raise ValueError('missing useful public diagnosis')
    finally:source.write_bytes(original)
    await test(canonical/'normal-init-portable.json','diagnosis-restored-recovery')
    spec=package/'maintained.json';data=json.loads((canonical/'normal-plain-toml.json').read_text())
    data['command'][0]=os.path.relpath(json.loads((target/'runtime.json').read_text())['python'],package).replace('\\','/')
    immutable_json(spec,data);approved=copy.deepcopy(data)
    index=next(i for i,s in enumerate(data['steps']) if s.get('state',{}).get('path')=='cz.toml')
    expected=base64.b64decode(data['steps'][index]['state']['bytes_base64']);snapshot=package/'snapshots/init-plain-complete.txt';snapshot_hash=sha256(snapshot)
    anchor=b'                config_doc.as_string().encode(self._settings["encoding"])\n'
    if original.count(anchor)!=1:raise ValueError('intentional formatting source anchor not unique')
    def formatting(header):
        return original.replace(anchor,b'                '+repr(header).encode('ascii')+b' + config_doc.as_string().encode(self._settings["encoding"])\n')
    header=b'# Reviewed synthetic header.\n';later=b'# Cancelled synthetic header.\n'
    immutable_json(root/'intended-formatting-change.json',dict(scope='Explicit synthetic target formatting change, not an upstream release or semantic regression. Adds one TOML comment; all saved settings, terminal output and unrelated snapshot unchanged.',source=source.relative_to(ROOT).as_posix(),original_sha256=sha256(source),header_base64=base64.b64encode(header).decode()))
    try:
        source.write_bytes(formatting(header))
        _,row=await test(spec,'maintenance-intended-comment-change',1)
        if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:index]):raise ValueError('intended formatting did not reach selected state behind passing snapshot')
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-selected-file-update',input='/update-state '+str(index+1)+'\n/review\n/replay\n/save\n')
        changed=json.loads(spec.read_text());comparison=copy.deepcopy(changed);comparison['steps'][index]=approved['steps'][index]
        if comparison!=approved or base64.b64decode(changed['steps'][index]['state']['bytes_base64'])!=header+expected or sha256(snapshot)!=snapshot_hash:
            raise ValueError('selected file update changed unrelated approvals or approved wrong bytes')
        await test(spec,'maintenance-selected-update-replay');saved=spec.read_bytes()
        source.write_bytes(formatting(later))
        await run([runner,'record','--edit',spec.relative_to(ROOT)],'maintenance-cancelled-file-update',expected=130,input='/update-state '+str(index+1)+'\n/quit\n')
        if spec.read_bytes()!=saved or sha256(snapshot)!=snapshot_hash:raise ValueError('cancelled update altered approved bytes')
        source.write_bytes(formatting(header));await test(spec,'maintenance-cancel-restored-replay')
        prompts=['Please choose a supported config file:','Please choose a cz (commit rule):','Choose the source of the version:',
            'Choose version scheme:','Please enter the correct version format:','Create changelog automatically on bump','Keep major version zero (0.x) during breaking changes']
        controls=[]
        for i,prompt in enumerate(prompts):
            controls+=['/expect '+prompt]
            if i==0:controls+=['/key ArrowDown']
            controls+=['/key Enter']
        controls+=['/expect Configuration complete','/exit 0','/snapshot discarded-before-cancel.txt','/rerecord 1',
            '/key CtrlC','/expect Stopped by user','/exit 25','/missing cz.toml','/entries .','/review','/replay','/save']
        suffix=package/'suffix.json';argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixture',
            '--temporary-home','--temporary-temp','--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
        for key,value in data['env'].items():argv+=['--env',key+'='+value]
        for key in data['inherit_env']:argv+=['--inherit-env',key]
        argv+=['--',*data['command']]
        await run(argv,'maintenance-suffix-rerecord-cancellation',input='\n'.join(controls+['']))
        replaced=json.loads(suffix.read_text())
        if any(s.get('key')=='Enter' or 'snapshot' in s for s in replaced['steps']) or (package/'snapshots/discarded-before-cancel.txt').exists():raise ValueError('discarded success suffix/snapshot survived cancellation rerecord')
        await test(suffix,'maintenance-suffix-ordinary-replay')
        relocated=root/'relocated caf\u00e9 \u96ea';shutil.copytree(package,relocated)
        for selected in [spec,suffix]:
            if sha256(relocated/selected.name)!=sha256(selected):raise ValueError('relocation edited approved bytes')
            await test(relocated/selected.name,'relocated-'+selected.stem)
        immutable_json(root/'journey.json',dict(schema_version=1,attempts=attempts,real_fault_diagnostic_commands=2,
            selected_update_controls=4,cancelled_update_controls=2,suffix_controls=len(controls),selected_state_number=index+1,
            unrelated_steps_preserved=True,snapshot_sha256=snapshot_hash,maintained_spec_sha256=sha256(spec),
            relocated_spec_sha256=sha256(relocated/spec.name),suffix_spec_sha256=sha256(suffix),
            intentional_source_variant='One reviewed TOML comment; not final source or a product-fault calibration.',
            human_time='unmeasured',project_admitted=False))
    finally:
        source.write_bytes(original)
        if source.read_bytes()!=original:raise ValueError('maintenance source restoration failed')
    print('Public diagnosis, selected/cancelled file update, suffix cancellation/snapshot pruning and unchanged Unicode relocation passed; source restored.')


if __name__=='__main__':asyncio.run(main())
