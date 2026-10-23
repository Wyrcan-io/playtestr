"""Close the second actual project only after every declared evidence gate."""
import argparse
import base64
import copy
import hashlib
import json

from next20_check import RAW,ROOT,DOC,NAME
from next20_verify_jrnl import build_model,validate,require
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--local-and-native-only',action='store_true');args=parser.parse_args()
    project='commitizen-python';raw=RAW/project;package=DOC/project
    def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    references={};seen=set()
    def subject(path):references[path.relative_to(ROOT).as_posix()]=sha256(path)
    freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json')
    binary=next(c['binary_sha256'] for c in freeze['cells'] if c['host']=='windows')
    require(not (RAW/'active'/project).exists(),'local source/runtime still active')
    def command(eid,original_failure=False):
        events={k:load(RAW/'events'/(eid+'-'+k+'.json')) for k in ['started','identified','launched','finished']}
        require(all(e['campaign']==NAME and e['project']==project and e['phase']=='development' and e['id']==eid for e in events.values()),'wrong local command identity')
        end=events['finished'];expected=events['started']['expected_exit']
        require(end['category']==('exit_mismatch' if original_failure else 'passed') and end['exit_code']==(1 if original_failure else expected) and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'unaccounted local outcome/cleanup')
        if original_failure:require(expected==0,'original failure relabelled as expected')
        console=raw/eid/'console.log';require(sha256(console)==end['console_sha256'],'changed local console');subject(console)
        reference=events['identified']['identity'];manifest=RAW/reference['manifest']
        require(sha256(manifest)==reference['sha256'],'changed actual launch identity');subject(manifest)
        identity=load(manifest)
        if 'base' in identity:
            reference=identity['base'];manifest=RAW/reference['manifest']
            require(sha256(manifest)==reference['sha256'],'changed actual base identity');subject(manifest);identity=load(manifest)
        require(identity['files'].get('artifacts/'+NAME+'/candidate/windows/playtestr.exe')==binary,'local public command used another runner')
        return events['started']['label']
    def report(path,status='passed',category=None):
        data=load(path);subject(path);require(len(data['results'])==1 and data['runner_version']==freeze['version'],'wrong local report/runner')
        row=data['results'][0]
        require(row['status']==status and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'wrong/unclean local report')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in seen,'cross/duplicate local report');seen.add(row['invocation_id'])
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive local steps')
        else:require(row['failure']['category']==category,'wrong local failure category')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation local saved evidence')
        return row
    routes=[('first-use.json','normal-init.json','first-ordinary-report.json',20),
            ('first-use-portable.json','normal-init-portable.json','portable-ordinary-report.json',20),
            ('snapshot-authoring.json','normal-plain-toml.json','snapshot-ordinary-report.json',22)]
    for receipt,spec_name,report_name,controls in routes:
        first=load(package/receipt);subject(package/receipt)
        require(first['shell_invocations']==3 and len(first['attempts'])==3 and first['recorder_controls']==controls and not first['handwritten_playtestr_json'],'public authoring measurement changed')
        for eid in first['attempts']:command(eid)
        require(sha256(package/spec_name)==first['spec_sha256'] and sha256(raw/report_name)==first['report_sha256'],'public approved contract/report changed')
        spec=load(package/spec_name)
        saved=next(s['state'] for s in spec['steps'] if s.get('state',{}).get('kind')=='file')
        require(hashlib.sha256(base64.b64decode(saved['bytes_base64'])).hexdigest()==first['independent_expected_file_sha256'],'first independently expected file changed')
        report(raw/report_name)
    development=[]
    for series,passed,failed in [('861e63b9a8f642e0becc0d5b983215e3',18,2),('29c098f8da174793ba75a16f20114ec3',20,0)]:
        path=raw/'development'/series/'summary.json';summary=load(path);subject(path)
        require(summary['phase']=='development' and summary['final_ordinary_credit']==0 and len(summary['results'])==20,'development relabelled as final')
        statuses=[]
        for result in summary['results']:
            path=ROOT/result['report'];require(sha256(path)==result['report_sha256'],'original development evidence changed')
            row=report(path,result['status'],result['category']);command(result['attempt'],row['status']=='failed');statuses.append(row['status'])
        require(statuses.count('passed')==passed and statuses.count('failed')==failed,'original development denominator changed')
        development.append(dict(series=series,passed=passed,failed=failed))
    root=raw/'maintenance-935afc6c2158425cacc61070ddd8dee3';journey=load(root/'journey.json');subject(root/'journey.json')
    for attempt in journey['attempts']:require(command(attempt['id'])==attempt['label'],'maintenance command selection changed')
    for path in root.glob('*.json'):
        data=load(path)
        if 'runner_version' not in data:continue
        failed=path.stem in {'diagnosis-real-saved-tag-corruption','maintenance-intended-comment-change'}
        report(path,'failed' if failed else 'passed','state_assertion_failure' if failed else None)
    require(journey['real_fault_diagnostic_commands']==2 and journey['selected_state_number']==19,'diagnosis/selected state measurement changed')
    original=load(package/'normal-plain-toml.json');maintained=root/'reviewed route/maintained.json';changed=load(maintained)
    original['command'][0]=changed['command'][0];comparison=copy.deepcopy(changed);comparison['steps'][18]=original['steps'][18]
    require(comparison==original,'maintenance changed unrelated approvals')
    require(base64.b64decode(changed['steps'][18]['state']['bytes_base64'])==b'# Reviewed synthetic header.\n'+base64.b64decode(original['steps'][18]['state']['bytes_base64']),'maintenance expected file differs from intended comment-only change')
    snapshot=root/'reviewed route/snapshots/init-plain-complete.txt'
    require(sha256(snapshot)==journey['snapshot_sha256']==sha256(package/'snapshots/init-plain-complete.txt'),'unrelated approved snapshot changed')
    relocated=root/'relocated caf\u00e9 \u96ea'
    for name,key in [('maintained.json','maintained_spec_sha256'),('suffix.json','suffix_spec_sha256')]:
        path=root/'reviewed route'/name
        require(sha256(path)==journey[key]==sha256(relocated/name),'relocation edited approved bytes');subject(path);subject(relocated/name)
    suffix=load(root/'reviewed route/suffix.json')
    require(not any(s.get('key')=='Enter' or 'snapshot' in s for s in suffix['steps']) and any(s.get('key')=='CtrlC' for s in suffix['steps']),'discarded success suffix survived cancellation')
    require(not (root/'reviewed route/snapshots/discarded-before-cancel.txt').exists(),'discarded snapshot survives')
    native=[];actual_models={}
    for host,generation in [('linux',1),('windows',2)]:
        retained=raw/('retained-native-v'+str(generation));model,index=build_model(retained,'39984863257',host,project)
        counts=validate(model);actual_models[host]=model
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'native expansion remains')
        subject(retained/'index.json');subject(retained/'expanded-removed.json');native.append(dict(host=host,**counts))
    if args.local_and_native_only:
        print('Local public journeys, both development series and actual native cells independently verified; remaining CI evidence still required. No admission.')
        return
    ci=[]
    for generation in range(3,15):
        retained=raw/('retained-native-v'+str(generation));audit=load(retained/'delivered-ci-audit.json')
        verify(retained/'packets.tar.gz',load(retained/'index.json')['files'])
        require(audit['archive_sha256']==sha256(retained/'packets.tar.gz') and audit['source_restored'] and audit['target_removed'],'changed/unclosed actual CI packet')
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'CI expansion remains')
        subject(retained/'index.json');subject(retained/'delivered-ci-audit.json');ci.append(audit)
    require({(c['host'],c['mode'],c['route']) for c in ci}=={(h,m,r) for h in ['linux','windows'] for m in ['baseline','fault','recovered'] for r in ['source','private-archive']} and len({c['invocation'] for c in ci})==12,'missing/duplicate generated-CI phase')
    controls=list((raw/'audit-controls').glob('*/results.json'));require(len(controls)==1,'missing actual model corruption controls')
    negatives=load(controls[0])['controls'];require(len(negatives)==24 and all(c['rejected'] for c in negatives),'incomplete actual model challenges');subject(controls[0])
    require(len({(c['host'],c['control']) for c in negatives})==24,'duplicate actual corruption control')
    from next20_project_audit_controls import encoded
    for control in negatives:
        positive=controls[0].parent/control['positive_model']
        require(positive.name==control['host']+'-actual-model.json' and positive.parent==controls[0].parent,'unsafe control model reference')
        require(sha256(positive)==control['positive_model_sha256'] and load(positive)==actual_models[control['host']],'corruption challenged a different actual model');subject(positive)
        altered=copy.deepcopy(actual_models[control['host']]);patch=control['mutation'];parent=altered
        for key in patch['path'][:-1]:parent=parent[key]
        key=patch['path'][-1]
        if patch['operation']=='truncate':parent[key]=parent[key][:patch['length']]
        else:
            require(patch['operation']=='replace','unknown actual corruption operation');parent[key]=patch['value']
        require(hashlib.sha256(encoded(altered)).hexdigest()==control['altered_canonical_json_sha256'],'reconstructed corruption bytes changed')
        try:validate(altered)
        except ValueError as error:require(str(error)==control['reason'],'corruption rejection reason changed')
        else:raise ValueError('Actual complete cell corruption accepted at admission')
    removed=raw/'retained-source/removed.json';require(load(removed)['removed'],'local removal missing');subject(removed)
    for name in ['first-development-disposition.json','maintenance-first-disposition.json','development-test-freeze.json','source-provenance.json','source-review.json','fault-declaration.json']:
        subject(package/name)
    size=measure(raw)['total_bytes'];require(size<=64*1024**2,'project retained storage exceeds bound')
    immutable_json(package/'admission.json',dict(schema_version=1,project=project,repository='commitizen-tools/commitizen',
        pin=load(package/'source-provenance.json')['pin'],admitted=True,candidate=freeze['version'],
        native_cells=native,canonical_scenarios=20,normal=8,edge=12,ordinary=480,
        real_source_faults=3,calibrations=18,additional_terminal_only_probes=2,
        development=development,first_use_commands=3,first_use_controls=20,
        first_use_scope='Prepared familiar agent; original local PATH confounder retained, repaired portable window separate.',
        diagnosis_commands=2,maintenance_and_suffix_and_relocation=True,delivered_ci_observations=12,
        cell_model_negative_controls=24,local_target_absent=True,retained_bytes=size,subjects=references,
        human_participants=0,human_usability='unmeasured',paid_admissions=0,
        scope='One engineering admission. Full next-twenty/global control/audit closure remains pending.'))
    print('Admitted Commitizen:480 ordinary,18 mandatory calibrations,2 separate probes;12 delivered-CI observations. Campaign incomplete.')


if __name__=='__main__':main()
