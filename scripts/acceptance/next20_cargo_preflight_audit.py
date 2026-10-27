"""Audit and retain the original19/20 Linux preflight without granting qualification."""
import asyncio
import hashlib
import json
import tarfile

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NAME,NextCampaign,owned_environment
from next20_verify_jrnl import source_hashes
from readiness_compact_native import compact
from readiness_evidence import immutable_json,sha256


async def main():
    run='40462439055';revision='bb1fa7aa5bf847de74327ca077e31b7ab87f631e'
    root=RAW/'native'/run;packet=root/'next20-cargo-linux-preflight';project='cargo-generate'
    if len(list(root.iterdir()))!=1:raise ValueError('audit exactly one original retrieved packet')
    observed=await execute(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','status,conclusion,headSha,jobs'],
        'core','cargo-linux-preflight-original-provider',cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(observed['output'])
    if provider['headSha']!=revision or provider['status']!='completed' or provider['conclusion']!='failure' or len(provider['jobs'])!=1:raise ValueError('wrong original provider outcome/source')
    steps={s['name']:s['conclusion'] for s in provider['jobs'][0]['steps']}
    if steps.get('Acquire, verify reviewed dependencies and compile ordinary CLI within twenty minutes')!='success' or steps.get('Retain exact actual compiled binary and provenance')!='success' or steps.get('Execute all twenty development scenarios on native Linux')!='failure':raise ValueError('original native step outcomes differ')
    target=packet/'active'/project;build=json.loads((target/'build.json').read_text());runtime=json.loads((target/'runtime.json').read_text())
    owner=json.loads((target/'task-owned.json').read_text());prefix='artifacts/'+NAME+'/'
    if owner['workspace']!='/home/runner/work/playtestr/playtestr' or owner['pin']!=json.loads((DOC/project/'source-review.json').read_text())['pin']:raise ValueError('wrong native source owner/pin')
    provenance=json.loads((DOC/project/'source-provenance.json').read_text());acquired=json.loads((target/'acquisition.json').read_text())
    if acquired['source_files']!=provenance['files'] or sha256(target/'source.tar.gz')!=acquired['archive_sha256']:raise ValueError('native source provenance differs')
    source_members={}
    with tarfile.open(target/'source.tar.gz','r:gz') as stream:
        for member in stream:
            if member.isdir():continue
            parts=member.name.split('/');name='/'.join(parts[1:])
            if not member.isfile() or name not in provenance['files'] or name in source_members or member.size>8*1024**2:raise ValueError('unsafe native source archive member')
            data=stream.extractfile(member).read(member.size+1)
            source_members[name]=hashlib.sha256(data).hexdigest()
    if source_members!=provenance['files']:raise ValueError('actual native source archive does not match all pinned source bytes')
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']=='linux')
    install=json.loads((packet/'candidate-native-exit-v1/linux/installed.json').read_text())
    if install['archive_sha256']!=candidate['archive_sha256'] or install['binary_sha256']!=candidate['binary_sha256']:raise ValueError('wrong native Playtestr archive')
    events={}
    for path in (packet/'events').glob('*.json'):
        value=json.loads(path.read_text());eid=value['id']
        if value['campaign']!=NAME or value['event'] in events.setdefault(eid,{}):raise ValueError('duplicate/wrong original event')
        events[eid][value['event']]=value
    def identity(ref):
        manifest=packet/ref['manifest']
        if sha256(manifest)!=ref['sha256']:raise ValueError('original identity changed')
        value=json.loads(manifest.read_text())
        if 'base' in value:return identity(value['base'])
        return value
    def command(eid,expected):
        rows=events[eid]
        if set(rows)!={'started','identified','launched','finished'} or rows['started']['ci_run_id']!=run:raise ValueError('incomplete/wrong original command')
        finish=rows['finished']
        if finish['exit_code']!=expected or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':raise ValueError('original command outcome/cleanup differs')
        console=packet/('core' if rows['started']['project']=='core' else rows['started']['project'])/eid/'console.log'
        if sha256(console)!=finish['console_sha256']:raise ValueError('original console changed')
        base=identity(rows['identified']['identity'])
        for helper in ['next20_check.py','adversarial_process.py','readiness_evidence.py','next20_cargo_build.py','next20_cargo_host_contracts.py','next20_jrnl_development.py']:
            name='scripts/acceptance/'+helper
            if base['files'].get(name) not in source_hashes(revision,name):raise ValueError('stale native helper binding: '+helper)
        return rows,base
    command(build['build_attempt'],0)
    version=json.loads((target/'version-check.json').read_text());command(version['attempt'],0)
    packed=packet/project/'native-preflight/linux';binary_index=json.loads((packed/'compiled-binary-index.json').read_text());binary_archive=packed/'compiled-binary.tar.xz'
    if sha256(binary_archive)!=binary_index['archive_sha256'] or build['binary_sha256']!=runtime['native_sha256']:raise ValueError('native binary archive/runtime differs')
    actual_binary={}
    with tarfile.open(binary_archive,'r:xz') as stream:
        for member in stream:
            if not member.isfile() or member.name not in binary_index['files'] or member.name in actual_binary or member.size>64*1024**2:raise ValueError('unsafe native binary member')
            digest=hashlib.sha256();size=0;header=b''
            with stream.extractfile(member) as payload:
                while block:=payload.read(65536):
                    if not header:header=block[:20]
                    digest.update(block);size+=len(block)
            record=dict(bytes=size,sha256=digest.hexdigest())
            if record!=binary_index['files'][member.name]:raise ValueError('actual packed native binary/metadata differs')
            if member.name=='cargo-generate' and (header[:5]!=b'\x7fELF\x02' or int.from_bytes(header[18:20],'little')!=62 or record['sha256']!=build['binary_sha256']):raise ValueError('packed target is not exact native Linuxamd64 ELF')
            actual_binary[member.name]=record
    if set(actual_binary)!=set(binary_index['files']):raise ValueError('incomplete retained native binary')
    summaries=list((packet/project/'development').glob('*/summary.json'))
    if len(summaries)!=1:raise ValueError('ambiguous original native development series')
    summary=json.loads(summaries[0].read_text());seen=set();results=[]
    if summary['passed']!=19 or summary['failed']!=1 or len(summary['results'])!=20:raise ValueError('original19/20 outcomes differ')
    for case in summary['results']:
        report=packet/case['report'].removeprefix(prefix);data=json.loads(report.read_text());row=data['results'][0]
        if sha256(report)!=case['report_sha256'] or data['runner_version']!='v0.4.0-rc.6' or row['invocation_id'] in seen or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('report/version/invocation/target-workspace cleanup differs')
        seen.add(row['invocation_id']);expected=1 if case['case']=='N01' else 0;rows,base=command(case['attempt'],expected)
        plan=json.loads((summaries[0].parent/(case['case']+'.planned.json')).read_text());spec=packet/plan['spec'].removeprefix(prefix)
        if sha256(spec)!=case['spec_sha256'] or sha256(spec)!=plan['spec_sha256'] or plan['runner_sha256']!=candidate['binary_sha256'] or plan['source_build_sha256']!=sha256(target/'build.json'):raise ValueError('actual native spec/build/runner binding differs')
        ref=rows['identified']['identity'];wrapped=json.loads((packet/ref['manifest']).read_text());catalog_ref=wrapped['target_catalog'];catalog=packet/catalog_ref['manifest']
        if sha256(catalog)!=catalog_ref['sha256']:raise ValueError('original native target catalog changed')
        files=json.loads(catalog.read_text())['files']
        if files.get(prefix+'active/'+project+'/bin/cargo-generate')!=build['binary_sha256']:raise ValueError('actually launched target differs from retained compiled binary')
        if case['case']=='N01':
            if row['failure']['category']!='snapshot_mismatch':raise ValueError('first native failure is not preserved snapshot mismatch')
        elif row['status']!='passed' or not all(s['status']=='passed' for s in row['steps']):raise ValueError('missing original positive native steps')
        results.append(dict(case=case['case'],attempt=case['attempt'],status=row['status'],category=row.get('failure',{}).get('category'),report_sha256=sha256(report)))
    immutable_json(root/'run-metadata.json',provider)
    receipt=dict(schema_version=1,run=run,qualification_revision=revision,source_pin=owner['pin'],actual_source_files=len(source_members),
        native_source_build=True,target_binary_sha256=build['binary_sha256'],binary_archive_sha256=sha256(binary_archive),
        candidate_archive_sha256=candidate['archive_sha256'],candidate_binary_sha256=candidate['binary_sha256'],results=results,
        passed=19,failed=1,complete_native_cell_credits=0,final_ordinary_credits=0,project_credits=0,
        scope='Original failed preflight preserved; real native build and actual19 positive cases are historical observations, not a complete native qualification. Source/runtime filesystem deletion not claimed.')
    immutable_json(root/'native-preflight-audit.json',receipt);immutable_json(DOC/project/'native-linux-preflight-first-audit.json',receipt)
    compact(RAW,project,[run],16*1024**2,generation=1)
    await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,'-Generation','1'],
        'core','remove-audited-first-cargo-linux-preflight',cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    print('Audited/retained original Linux native build,19pass/1snapshot failure and all actual target cleanups; zero final/admission credit.')


if __name__=='__main__':asyncio.run(main())
