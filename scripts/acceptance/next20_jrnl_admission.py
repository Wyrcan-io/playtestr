"""Close jrnl's actual project package without claiming the twenty-project gate."""
import base64
import copy
import json
from pathlib import Path

from next20_check import RAW, ROOT, DOC, NAME
from next20_verify_jrnl import build_model, validate, require
from readiness_compact_native import verify
from readiness_evidence import immutable_json, sha256
from readiness_storage import measure


def main():
    package=DOC/'jrnl';raw=RAW/'jrnl'
    def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    require(not (RAW/'active/jrnl').exists(),'local source/runtime still active')
    freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json')
    binary=next(c['binary_sha256'] for c in freeze['cells'] if c['host']=='windows')
    references={};invocations=set()
    def subject(path):references[path.relative_to(ROOT).as_posix()]=sha256(path)
    def command(eid,original_failure=False):
        events={k:load(RAW/'events'/(eid+'-'+k+'.json')) for k in ['started','identified','launched','finished']}
        require(all(e['campaign']==NAME and e['project']=='jrnl' and e['phase']=='development' and e['id']==eid for e in events.values()),'wrong local project event identity')
        end=events['finished']
        expected_category,expected_exit=('exit_mismatch',1) if original_failure else ('passed',events['started']['expected_exit'])
        require(end['category']==expected_category and end['exit_code']==expected_exit and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'wrong/unaccounted local journey command failure or cleanup')
        if original_failure:require(events['started']['expected_exit']==0,'historical ordinary failure relabelled as expected success')
        console=raw/eid/'console.log';require(sha256(console)==end['console_sha256'],'changed actual public journey console');subject(console)
        reference=events['identified']['identity'];manifest=RAW/reference['manifest'];require(sha256(manifest)==reference['sha256'],'changed local prelaunch identity');subject(manifest)
        value=load(manifest)
        if 'base' in value:
            reference=value['base'];manifest=RAW/reference['manifest'];require(sha256(manifest)==reference['sha256'],'changed base identity');subject(manifest);value=load(manifest)
        require(value['files'].get('artifacts/'+NAME+'/candidate/windows/playtestr.exe')==binary,'public local journey used another runner')
        return events['started']['label']
    def report(path,status='passed',category=None):
        value=load(path);subject(path);require(len(value['results'])==1,'wrong local report selection');row=value['results'][0]
        require(value['runner_version']==freeze['version'] and row['status']==status and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'wrong or unclean actual local report')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'cross/duplicate local invocation');invocations.add(row['invocation_id'])
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive local steps')
        else:require(row['failure']['category']==category,'wrong local failure diagnosis')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation local saved evidence')
        return row
    first=load(package/'first-use.json');subject(package/'first-use.json')
    labels={command(eid) for eid in first['attempts']}
    expected={'first-use-runner-version','first-public-record-review-replay-export','first-reviewed-ordinary-test'}
    require(labels==expected and len(first['attempts'])==first['shell_invocations']==3 and first['recorder_controls']==11 and not first['handwritten_playtestr_json'],'first public route metrics changed')
    actual=[load(p)['id'] for p in (RAW/'events').glob('*-started.json') if load(p).get('project')=='jrnl' and load(p).get('label') in expected]
    require(set(actual)==set(first['attempts']) and len(actual)==3,'missing earlier first-route failure')
    spec=load(package/'normal-delete.json');require(sha256(package/'normal-delete.json')==first['spec_sha256'],'first approved spec changed')
    require(sha256(raw/'first-ordinary-report.json')==first['report_sha256'],'first ordinary report changed');report(raw/'first-ordinary-report.json')
    expected_file=base64.b64decode(spec['steps'][6]['state']['bytes_base64'])
    import hashlib
    require(hashlib.sha256(expected_file).hexdigest()==first['independent_expected_file_sha256'],'first-use independently expected file changed')
    # Reconcile both complete development series, including every first failure.
    development=[]
    for series,want_pass,want_fail in [('47a0241f55c547e0a4694c5feca4e6f6',16,4),('39f35ad700594698a29d6b6aa3466b77',20,0)]:
        summary=load(raw/'development'/series/'summary.json');subject(raw/'development'/series/'summary.json')
        require(summary['phase']=='development' and len(summary['results'])==20 and summary['final_ordinary_credit']==0,'development relabelled as final')
        outcomes=[]
        for row in summary['results']:
            path=ROOT/row['report'];require(sha256(path)==row['report_sha256'],'original development evidence changed')
            actual=report(path,row['status'],row['category']);command(row['attempt'],original_failure=(row['status']=='failed'));outcomes.append(actual['status'])
        require(outcomes.count('passed')==want_pass and outcomes.count('failed')==want_fail,'original development denominator changed')
        development.append(dict(series=series,passed=want_pass,failed=want_fail))
    journey_root=raw/'maintenance-66622571feed43e6a8aafc3801566720';journey=load(journey_root/'journey.json');subject(journey_root/'journey.json')
    for row in journey['attempts']:require(command(row['id'])==row['label'],'wrong actual maintenance command')
    for path in journey_root.glob('*.json'):
        if path.name=='journey.json':continue
        failed=path.stem in {'diagnosis-real-saved-corruption','maintenance-intended-state-change'}
        report(path,'failed' if failed else 'passed','state_assertion_failure' if failed else None)
    maintained=journey_root/'reviewed route/maintained.json';changed=load(maintained)
    approved=copy.deepcopy(spec);approved['command'][0]=changed['command'][0]
    comparison=copy.deepcopy(changed);comparison['steps'][6]=approved['steps'][6]
    require(comparison==approved and sha256(maintained)==journey['maintained_spec_sha256'],'maintenance changed unrelated approvals')
    require(base64.b64decode(changed['steps'][6]['state']['bytes_base64'])==expected_file.replace(b'Second body.',b'Second body reviewed.'),'maintenance saved expectation not independently correct')
    snapshot=journey_root/'reviewed route/snapshots/normal-delete.txt'
    require(sha256(snapshot)==journey['snapshot_sha256']==sha256(package/'snapshots/normal-delete.txt'),'unrelated snapshot changed')
    relocated=journey_root/'relocated caf\u00e9 \u96ea'
    require(sha256(relocated/'maintained.json')==sha256(maintained)==journey['relocated_spec_sha256'],'relocation edited approved spec')
    suffix=load(journey_root/'reviewed route/suffix.json')
    require(not any(s.get('text')=='y' for s in suffix['steps']) and any(s.get('text')=='n' for s in suffix['steps']),'discarded suffix input survived')
    require(sha256(relocated/'suffix.json')==sha256(journey_root/'reviewed route/suffix.json'),'suffix relocation edited reviewed bytes')
    # Rebuild native positives from actual retained payloads, rather than trust receipts.
    native=[]
    for host,generation in [('linux',1),('windows',2)]:
        retained=raw/('retained-native-v'+str(generation));model,index=build_model(retained,'39797356210',host);counts=validate(model)
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'native expansion not removed')
        subject(retained/'index.json');subject(retained/'expanded-removed.json');native.append(dict(host=host,**counts))
    ci=[]
    for generation in range(3,15):
        retained=raw/('retained-native-v'+str(generation));index=load(retained/'index.json')
        require(sha256(retained/'packets.tar.gz')==index['archive_sha256'],'changed retained CI payload');verify(retained/'packets.tar.gz',index['files'])
        audit=load(retained/'delivered-ci-audit.json');require(audit['index_sha256']==sha256(retained/'index.json') and audit['archive_sha256']==index['archive_sha256'] and audit['source_restored'] and audit['target_removed'],'changed/unclosed actual CI audit')
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'CI expansion remains')
        subject(retained/'delivered-ci-audit.json');subject(retained/'index.json');ci.append(audit)
    require({(c['host'],c['mode'],c['route']) for c in ci}=={(h,m,r) for h in ['linux','windows'] for m in ['baseline','fault','recovered'] for r in ['source','private-archive']} and len({c['invocation'] for c in ci})==12,'missing/duplicate delivered-CI triplet phase')
    require(load(raw/'retained-source/removed.json')['removed'],'local target removal not recorded')
    controls=list((raw/'audit-controls').glob('*/results.json'));require(len(controls)==1,'missing actual cell-model challenge set')
    negatives=load(controls[0])['controls'];require(len(negatives)==24 and all(c['rejected'] for c in negatives),'incomplete actual cell-model negatives');subject(controls[0])
    retained_bytes=measure(raw)['total_bytes'];require(retained_bytes<=64*1024**2,'project retention cap exceeded')
    receipt=dict(schema_version=1,project='jrnl',repository='jrnl-org/jrnl',pin=load(package/'source-provenance.json')['pin'],
        admitted=True,scope='One engineering project; full next-twenty and global control/audit closure still pending.',
        candidate=freeze['version'],native_cells=native,canonical_scenarios=20,normal=8,edge=12,ordinary=480,
        real_source_faults=3,calibrations=18,development=development,first_use_commands=3,first_use_controls=11,
        diagnosis_commands=2,maintenance_and_suffix_and_relocation=True,delivered_ci_observations=12,
        cell_model_negative_controls=24,local_target_absent=True,retained_bytes=retained_bytes,subjects=references,
        human_participants=0,human_usability='unmeasured',paid_admissions=0,
        residual='Cross-entry retime storage ordering remains an observed upstream gap; original failing workflow retained and excluded. No real PR/fork or public release claim.')
    immutable_json(package/'admission.json',receipt)
    print('Admitted jrnl: 20 scenarios, two exact-archive native cells, 480 ordinary, 18 calibration; twelve separate delivered-CI observations. Campaign remains incomplete.')


if __name__=='__main__':main()
