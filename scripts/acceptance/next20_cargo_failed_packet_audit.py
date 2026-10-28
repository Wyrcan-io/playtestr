"""Audit a rejected complete-window attempt from actual retained logical records."""
import json
import re
import tarfile
import io
import hashlib

from next20_check import RAW,DOC
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256


def main():
    run='40746186639';revision='fa779f299a61cfb2d9f5cc276a8a61433292eba6';generation=6;project='cargo-generate'
    root=RAW/project/('retained-native-v'+str(generation));index,files=read_packet(project,generation)
    prefix='native/'+run+'/next20-cargo-linux-final/';project_prefix=prefix+project+'/';native_prefix='artifacts/runner-readiness-next-twenty-project-pass/'
    def document(name):return json.loads(files[prefix+name])
    provider=json.loads((root/'provider.json').read_text())
    if provider['headSha']!=revision or provider['status']!='completed' or provider['conclusion']!='failure':raise ValueError('wrong original rejected provider/source')
    build=document('active/'+project+'/build.json');runtime=document('active/'+project+'/runtime.json')
    if build['binary_sha256']!=runtime['native_sha256'] or runtime['kind']!='native':raise ValueError('rejected native runtime/build differs')
    source=document('active/'+project+'/acquisition.json');provenance=json.loads((DOC/project/'source-provenance.json').read_text())
    actual={}
    with tarfile.open(fileobj=io.BytesIO(files[prefix+'active/'+project+'/source.tar.gz']),mode='r:gz') as stream:
        for member in stream:
            if member.isdir():continue
            name='/'.join(member.name.split('/')[1:])
            if not member.isfile() or name not in provenance['files'] or name in actual or member.size>8*1024**2:raise ValueError('unsafe original rejected source archive')
            actual[name]=hashlib.sha256(stream.extractfile(member).read(member.size+1)).hexdigest()
    if actual!=provenance['files'] or source['source_files']!=actual:raise ValueError('rejected actual source pin archive differs')
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']=='linux')
    profile=document(project+'/host-contracts/scenarios.json');case_names={c['spec']:c['id'] for c in profile['cases']}
    reports=[];seen=set();attempts=set()
    for name,data in sorted(files.items()):
        match=re.fullmatch(re.escape(project_prefix)+r'final-series-native-exit-v1/([0-9]+)/([NE][0-9]{2})\.report\.json',name)
        if not match:continue
        batch=int(match[1]);case=match[2];report=json.loads(data);row=report['results'][0]
        plan=document(project+'/final-series-native-exit-v1/'+str(batch)+'/'+case+'.planned.json');spec=prefix+plan['spec'].removeprefix(native_prefix)
        if hashlib.sha256(files[spec]).hexdigest()!=plan['spec_sha256'] or plan['runner_sha256']!=candidate['binary_sha256'] or plan['archive_sha256']!=candidate['archive_sha256']:raise ValueError('rejected actual contract/candidate differs')
        matching=[]
        for event_name,event_data in files.items():
            if event_name.startswith(prefix+'events/') and event_name.endswith('-started.json'):
                event=json.loads(event_data)
                if event['label']=='final-batch-'+str(batch)+'-'+case:matching.append(event['id'])
        if len(matching)!=1 or matching[0] in attempts or row['invocation_id'] in seen:raise ValueError('missing/duplicate rejected fresh invocation')
        attempt=matching[0];attempts.add(attempt);seen.add(row['invocation_id']);events={e:document('events/'+attempt+'-'+e+'.json') for e in ['started','identified','launched','finished']}
        failed=batch==2 and case=='E02';expected=1 if failed else 0
        if any(event['phase']!='final-archive' for event in events.values()) or events['started']['ci_run_id']!=run or events['finished']['exit_code']!=expected or events['finished']['cleanup_errors'] or events['finished']['harness_cleanup']!='harness_process_reaped':raise ValueError('wrong original phase/outcome/harness cleanup')
        if hashlib.sha256(files[project_prefix+attempt+'/console.log']).hexdigest()!=events['finished']['console_sha256']:raise ValueError('original rejected console changed')
        if report['runner_version']!='v0.4.0-rc.6' or report['os']!='linux' or report['arch']!='amd64' or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('wrong native report or incomplete cleanup')
        if not failed and (row['status']!='passed' or not all(s['status']=='passed' for s in row['steps'])):raise ValueError('missing original positive steps')
        if failed and (row['failure']['category']!='state_assertion_failure' or row['steps'][16]['status']!='failed' or not all(s['status']=='passed' for s in row['steps'][:16])):raise ValueError('original saved-state failure differs or earlier step failed')
        for step in row['steps']:
            if step.get('state') and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):raise ValueError('rejected state came from another invocation')
        reports.append(dict(batch=batch,case=case,attempt=attempt,status=row['status'],report_sha256=hashlib.sha256(data).hexdigest(),category=row.get('failure',{}).get('category')))
    expected={(batch,c['id']) for batch in range(2) for c in profile['cases']}
    expected.update((2,c['id']) for c in profile['cases'][:10])
    if {(r['batch'],r['case']) for r in reports}!=expected or len(reports)!=50:raise ValueError('original49/1 partial-window boundary differs')
    failure=document(project+'/final-series-native-exit-v1/2/E02.report.json')['results'][0];screen_name=prefix+failure['evidence']['screen_path'].removeprefix(native_prefix);screen=files[screen_name].decode('utf-8')
    if 'Project owner: Adxa' not in screen:raise ValueError('original rendered wrong owner not preserved')
    receipt=dict(schema_version=1,run=run,revision=revision,retained_generation=generation,source_files=len(actual),actual_target_binary_sha256=build['binary_sha256'],
        retained_index_sha256=sha256(root/'index.json'),retained_archive_sha256=index['archive_sha256'],positive_observations=49,failed_observations=1,reports=reports,
        failure_screen_sha256=hashlib.sha256(files[screen_name]).hexdigest(),failure_screen=screen,
        finding='N01 with added full-input checks passed three batches. E02 rendered owner Adxa and the same-invocation saved-state checkpoint rejected reviewed Ada bytes after terminal and exit assertions passed. Backspace loss still requires direct trace diagnosis.',
        ordinary_qualification_credit=0,calibration_credit=0,project_admissions=0,
        scope='Whole Linux window2 rejected;49 passes do not transfer. All50 target/workspace and wrapper cleanups verified; failed hosted source/runtime filesystem deletion not claimed. Actual newer ELF differs from old preflight and cannot be identically aliased.')
    immutable_json(DOC/project/'native-linux-second-final-rejection.json',receipt)
    immutable_json(RAW/project/'window-two-rejected-audit.json',receipt)
    print('Verified and preserved rejected Linux window2:49 positive /1 state failure, zero final qualification credit')


if __name__=='__main__':main()
