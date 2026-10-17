"""Independently inspect actual native editor events, inputs, outcomes and restore."""
import argparse
import base64
from pathlib import Path

from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load

SOURCE='e7b5f29e575e44babe7fdaa2e83e55b62d318305'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--windows-run',help='Keep a verified Windows job from an earlier run when only Linux needed a profile correction.')
    parser.add_argument('--source-revision',default=SOURCE)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    source_revision=args.source_revision
    require(len(source_revision)==40 and all(c in '0123456789abcdef' for c in source_revision),'invalid source revision')
    runs={'playtestr-Linux':args.run,'playtestr-Windows':args.windows_run or args.run}
    for identity in set(runs.values()):require(identity.isascii() and identity.isdecimal(),'invalid native run ID')
    reviewed=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit'
    freeze=load(reviewed/'reviewed-contract-freeze.json')
    require(len(freeze['contracts'])==20,'twenty frozen contracts required')
    for name,digest in freeze['all_package_inputs'].items():
        require(sha256(reviewed/'contracts'/name)==digest,'canonical input changed')
    canonical=load(reviewed/'source-review.json')['archive_sha256'];cells=[]
    for host in ['playtestr-Linux','playtestr-Windows']:
        run=RAW/'native'/runs[host];metadata=load(run/'run-metadata.json')
        require(metadata['status']=='completed','native run incomplete')
        if runs[host]==args.run:require(metadata['conclusion']=='success','new native run failed')
        expected_job='terminal ('+('windows-2025' if host.endswith('Windows') else 'ubuntu-24.04')+')'
        jobs=[j for j in metadata['jobs'] if j['name']==expected_job]
        require(len(jobs)==1 and jobs[0]['status']=='completed' and jobs[0]['conclusion']=='success','selected native job missing or failed')
        base=run/host;packet=base/'runner-readiness-ten-project-pass'
        ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/'edit-native-runner.json')
        require(runner['source_revision']==source_revision and runner['candidate_sha256']==runner['copied_sha256'],'runner identity mismatch')
        def witness(identity,expected):
            events=attempts[identity]
            require('launched' in events and events['started']['expected_exit']==expected,'missing or wrong launch')
            finished=events['finished']
            require(finished['category']=='passed' and finished['exit_code']==expected,'unexpected command outcome')
            require(finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],'unconfirmed command cleanup')
            reference=events['identified']['identity'];path=packet_file(packet,reference['manifest'],1024**2)
            require(sha256(path)==reference['sha256'],'changed prelaunch manifest')
            console=packet_file(packet,events['started']['project']+'/'+identity+'/console.log',4*1024**2)
            require(sha256(console)==finished['console_sha256'],'changed command output')
            return load(path)['files']
        def result_ok(result,status):
            require(result['status']==status and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'scenario outcome or cleanup mismatch')
            for step in result['steps']:
                if 'state' in step:
                    state=step['state']
                    require(state['invocation_id']==result['invocation_id'] and state['workspace_id']==result['workspace']['id'],'cross-execution state')
        contracts=packet/'edit/host-contracts'
        for name in freeze['contracts']:
            original=load(reviewed/'contracts'/name);native=load(contracts/name)
            if host.endswith('Linux'):
                original.pop('inherit_env',None)
                if name=='N02.json':
                    state=original['steps'][8]['state']
                    require(state==dict(path='new-note.txt',kind='file',bytes_base64=base64.b64encode(b'fresh document').decode()),'unexpected canonical new-document assertion')
                    state['bytes_base64']=base64.b64encode(b'fresh document\n').decode()
            require(original==native,'unreviewed native contract change')
        for name,digest in freeze['all_package_inputs'].items():
            if name not in freeze['contracts']:require(sha256(contracts/name)==digest,'changed fixture or snapshot')
        report=load(base/'playtestr/results.json')
        require(report['runner_version']=='source-'+source_revision,'wrong runner source')
        require(report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'incomplete ordinary suite')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'wrong ordinary selection')
        suites=[k for k,v in attempts.items() if v['started']['label']=='public-recorded-suite']
        require(len(suites)==1,'ambiguous ordinary suite witness');files=witness(suites[0],0)
        for name in freeze['contracts']:
            require(files['artifacts/runner-readiness-ten-project-pass/edit/host-contracts/'+name]==sha256(contracts/name),'suite input not bound')
        for result in report['results']:result_ok(result,'passed')
        summaries=list((packet/'edit/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
        summary=summaries[0];faults=load(summary)
        require(faults['runner_sha256']==runner['copied_sha256'] and {f['id'] for f in faults['faults']}=={'F01','F02','F03'},'fault coverage mismatch')
        build=load(packet/'edit/retained-source/build.json')
        target_key='artifacts/runner-readiness-ten-project-pass/active/edit/'+build['binary_relative_path']
        runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'+('.exe' if host.endswith('Windows') else '')
        for fault in faults['faults']:
            require(fault['restored_exact'] and not fault['held_out'],'native replica mislabeled')
            key='artifacts/runner-readiness-ten-project-pass/active/edit/src/'+fault['path']
            require(fault['baseline_binary_sha256']!=fault['mutation_build']['binary_sha256'],'unchanged mutated executable')
            for phase,expected,digest,binary_digest in [
                ('baseline',0,fault['original_source_sha256'],fault['baseline_binary_sha256']),
                ('mutated',1,fault['mutated_source_sha256'],fault['mutation_build']['binary_sha256']),
                ('restored',0,fault['original_source_sha256'],fault['restored_build']['binary_sha256'])]:
                event=fault[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
                files=witness(event,expected)
                require(files[key]==digest and files[target_key]==binary_digest and files[runner_key]==runner['copied_sha256'],'actual source/executable identity mismatch')
                outcome=load(summary.parent/(fault['id']+'-'+phase+'.json'))['results'][0]
                result_ok(outcome,'failed' if expected else 'passed')
                if expected:require(outcome['failure']['category']==fault['category'],'wrong mutant diagnosis')
                if phase=='mutated' and fault['id']=='F03':
                    failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed');prior=outcome['steps'][:failed]
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior},'F03 lacks prior passing screen/exit')
            for phase in ['mutation_build','restored_build']:
                witness(fault[phase]['attempt'],0)
                label=fault['id'].lower()+('-mutated' if phase=='mutation_build' else '-restored')
                revisions=list((packet/'edit/retained-source/build-revisions').glob(label+'-*.json'))
                require(len(revisions)==1,'ambiguous actual build revision');revision=load(revisions[0])
                require(revision['binary_sha256']==fault[phase]['binary_sha256'],'build result identity mismatch')
                witness(revision['build_attempt'],0)
                files=witness(revision['version_attempt'],7 if fault['id']=='F02' and phase=='mutation_build' else 0)
                require(files[target_key]==revision['binary_sha256'],'built version probe used wrong executable')
        journeys=list((packet/'edit').glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous maintenance')
        journey_path=journeys[0];journey=load(journey_path)
        require(len(journey['attempts'])==12 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'incomplete maintenance')
        for row in journey['attempts']:witness(row['id'],1 if row['label'] in {'intended-file-change','intended-viewport-change'} else 0)
        require(sha256(journey_path.parent/'generated-workflow.yml')==journey['generated_workflow_sha256'],'workflow changed')
        removed=packet/'edit/retained-source/removed.json';removal=load(removed);index=load(removed.parent/'verified-index.json')
        require(removal['removed'] and removal['owned_relative_path']=='active/edit' and removal['source_archive_sha256']==canonical==index['archive_sha256'],'source removal or archive mismatch')
        for name in index['selected_restore']:require(sha256(removed.parent/'selected-restore'/name)==index['files'][name]['sha256'],'source restore mismatch')
        cells.append(dict(host=host,run=runs[host],run_conclusion=metadata['conclusion'],
            job_conclusion=jobs[0]['conclusion'],scenarios=20,report_sha256=sha256(base/'playtestr/results.json'),
            source_fault_summary_sha256=sha256(summary),maintenance_sha256=sha256(journey_path),
            cleanup_receipt_sha256=sha256(removed),runner_sha256=runner['copied_sha256']))
    output=(args.output or RAW/'edit/native-development-verification.json').resolve();output.relative_to(ROOT)
    immutable_json(output,dict(runs=runs,runner_source=source_revision,cells=cells,
        phase='development',claim='Native gates verified; local checked removal required before admission.',archive_qualified=False))
    print('Verified both native editor cells from actual events, source/binary hashes, reports, builds and restores.')


if __name__=='__main__':main()
