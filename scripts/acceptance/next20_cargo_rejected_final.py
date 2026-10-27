"""Preserve the original rejected Linux final window, without repetition credit."""
import asyncio
import hashlib
import json
import tarfile

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from next20_packet_archive import verify
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


async def main():
    run='40477083665';revision='2524862c64499db7a182b5c3d9d88690ad186d47'
    root=RAW/'native'/run;packet=root/'next20-cargo-linux-final';project='cargo-generate';prefix='artifacts/runner-readiness-next-twenty-project-pass/'
    async def command(argv,label):return await execute(argv,'core',label,cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    observed=await command(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','status,conclusion,headSha,jobs'],'cargo-rejected-final-provider-readback')
    provider=json.loads(observed['output'])
    if provider['status']!='completed' or provider['conclusion']!='failure' or provider['headSha']!=revision or len(provider['jobs'])!=1:raise ValueError('wrong original provider/source failure')
    target=packet/'active'/project;build=json.loads((target/'build.json').read_text());runtime=json.loads((target/'runtime.json').read_text())
    canonical=RAW/project/'retained-native-v2';canonical_index=json.loads((canonical/'index.json').read_text());canonical_archive=canonical/'packets.tar.gz'
    if sha256(canonical_archive)!=canonical_index['archive_sha256']:raise ValueError('required existing retained runtime packet changed')
    verify(canonical_archive,canonical_index['files'])
    member='native/40467049451/next20-cargo-linux-preflight/active/cargo-generate/build.json'
    with tarfile.open(canonical_archive,'r:gz') as stream:prior=json.loads(stream.extractfile(member).read())
    if build['binary_sha256']!=prior['binary_sha256'] or runtime['native_sha256']!=build['binary_sha256']:raise ValueError('failed window actual target lacks exact already retained native executable')
    provenance=json.loads((DOC/project/'source-provenance.json').read_text());actual={}
    with tarfile.open(target/'source.tar.gz','r:gz') as stream:
        for entry in stream:
            if entry.isdir():continue
            name='/'.join(entry.name.split('/')[1:])
            if not entry.isfile() or name not in provenance['files'] or name in actual or entry.size>8*1024**2:raise ValueError('unsafe changed actual source archive')
            actual[name]=hashlib.sha256(stream.extractfile(entry).read(entry.size+1)).hexdigest()
    if actual!=provenance['files']:raise ValueError('actual compiled source archive differs from pinned primary source')
    final=packet/project/'final-series-native-exit-v1';summary=json.loads((final/'0/summary.json').read_text());results=[];seen=set()
    expected=[(0,c['case'],c['attempt'],0,c['report_sha256']) for c in summary['observations']]
    events={}
    for path in (packet/'events').glob('*.json'):
        value=json.loads(path.read_text());events.setdefault(value['id'],{})[value['event']]=value
    failed=[eid for eid,rows in events.items() if rows['started']['label']=='final-batch-1-N01']
    if len(expected)!=20 or len(failed)!=1 or (final/'1/summary.json').exists() or any((final/str(i)).exists() for i in range(2,12)):raise ValueError('original partial-window boundary differs')
    expected.append((1,'N01',failed[0],1,None))
    for batch,case,eid,code,report_hash in expected:
        report=final/str(batch)/(case+'.report.json');data=json.loads(report.read_text());row=data['results'][0];rows=events[eid]
        if report_hash and sha256(report)!=report_hash:raise ValueError('original positive report changed')
        if set(rows)!={'started','identified','launched','finished'} or any(r['phase']!='final-archive' for r in rows.values()) or rows['started']['ci_run_id']!=run or rows['finished']['exit_code']!=code or rows['finished']['cleanup_errors'] or rows['finished']['harness_cleanup']!='harness_process_reaped':raise ValueError('missing original execution/provider/cleanup')
        if sha256(packet/project/eid/'console.log')!=rows['finished']['console_sha256']:raise ValueError('original execution console changed')
        if data['runner_version']!='v0.4.0-rc.6' or data['os']!='linux' or data['arch']!='amd64' or row['invocation_id'] in seen or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('wrong report/native identity or incomplete cleanup')
        seen.add(row['invocation_id'])
        if code==0 and (row['status']!='passed' or not all(s['status']=='passed' for s in row['steps'])):raise ValueError('missing actual positive steps')
        if code==1 and (row['failure']['category']!='snapshot_mismatch' or row['steps'][7]['status']!='failed' or not all(s['status']=='passed' for s in row['steps'][:7])):raise ValueError('original first failure differs')
        results.append(dict(batch=batch,case=case,attempt=eid,status=row['status'],report_sha256=sha256(report),category=row.get('failure',{}).get('category')))
    failure=json.loads((final/'1/N01.report.json').read_text())['results'][0]
    evidence={}
    for key,name in failure['evidence'].items():
        path=packet/name.removeprefix(prefix);evidence[key]=dict(logical_path=name,sha256=sha256(path),text=path.read_text(encoding='utf-8'))
    receipt=dict(schema_version=1,run=run,revision=revision,actual_source_files=len(actual),actual_binary_sha256=build['binary_sha256'],
        required_already_retained_runtime_archive=canonical_archive.relative_to(RAW).as_posix(),required_runtime_archive_sha256=sha256(canonical_archive),
        positive_observations=20,failed_observations=1,results=results,first_failure=evidence,final_ordinary_credit=0,calibration_credit=0,project_admissions=0,
        scope='Original rejected entire Linux final window. First batch20 passes do not transfer into a replacement. Saved screen shows extra partial-input rows before stable final prompts; root cause still requires diagnosis. No source/runtime filesystem deletion claim for failed hosted job.')
    immutable_json(root/'run-metadata.json',provider);immutable_json(root/'rejected-final-audit.json',receipt)
    immutable_json(DOC/project/'native-linux-first-final-rejection.json',receipt)
    compact(RAW,project,[run],16*1024**2,generation=3)
    await command(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,'-Generation','3'],'cargo-rejected-final-native-expansion-removal')
    print('Preserved rejected Linux window20 positive/1 failed observation; original screen/diff/source/runtime proof retained, zero final qualification credit.')


if __name__=='__main__':asyncio.run(main())
