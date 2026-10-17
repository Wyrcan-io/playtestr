"""Independently inspect actual native Vis events, inputs, outcomes and restore."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load

SOURCE='e7b5f29e575e44babe7fdaa2e83e55b62d318305'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    args=parser.parse_args()
    runs={'playtestr-Linux':args.run,'playtestr-macOS':args.run}
    for identity in set(runs.values()):require(identity.isascii() and identity.isdecimal(),'invalid native run ID')
    reviewed=ROOT/'docs/validation/runner-readiness-ten-project-pass/vis'
    freeze=load(reviewed/'reviewed-contract-freeze.json')
    require(len(freeze['contracts'])==20,'twenty frozen contracts required')
    for name,digest in freeze['all_package_inputs'].items():
        require(sha256(reviewed/'contracts'/name)==digest,'canonical input changed')
    canonical=load(reviewed/'source-review.json')['archive_sha256'];cells=[]
    for host in ['playtestr-Linux','playtestr-macOS']:
        run=RAW/'native'/runs[host];metadata=load(run/'run-metadata.json')
        require(metadata['status']=='completed','native run incomplete')
        if runs[host]==args.run:require(metadata['conclusion']=='success','new native run failed')
        expected_job='terminal ('+('macos-15' if host.endswith('macOS') else 'ubuntu-24.04')+')'
        jobs=[j for j in metadata['jobs'] if j['name']==expected_job]
        require(len(jobs)==1 and jobs[0]['status']=='completed' and jobs[0]['conclusion']=='success','selected native job missing or failed')
        base=run/host;packet=base
        ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/'vis-native-runner.json')
        require(runner['source_revision']==SOURCE and runner['candidate_sha256']==runner['copied_sha256'],'runner identity mismatch')
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
        contracts=packet/'vis/host-contracts'
        for name in freeze['contracts']:
            original=load(reviewed/'contracts'/name);native=load(contracts/name)
            if host.endswith('macOS'):
                require(original['env']==dict(LC_ALL='C.UTF-8',TERM='xterm-256color'),'unexpected canonical locale')
                original['env']['LC_ALL']='en_US.UTF-8'
            require(original==native,'unreviewed native contract change')
        for name,digest in freeze['all_package_inputs'].items():
            if name not in freeze['contracts']:require(sha256(contracts/name)==digest,'changed fixture or snapshot')
        reports=list((packet/'vis/suites').glob('*/results.json'));require(len(reports)==1,'ambiguous ordinary suite report')
        report_path=reports[0];report=load(report_path)
        require(report['runner_version']=='source-'+SOURCE,'wrong runner source')
        require(report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'incomplete ordinary suite')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'wrong ordinary selection')
        suites=[k for k,v in attempts.items() if v['started']['label']=='public-recorded-suite']
        require(len(suites)==1,'ambiguous ordinary suite witness');files=witness(suites[0],0)
        for name in freeze['contracts']:
            require(files['artifacts/runner-readiness-ten-project-pass/vis/host-contracts/'+name]==sha256(contracts/name),'suite input not bound')
        for result in report['results']:result_ok(result,'passed')
        summaries=list((packet/'vis/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
        summary=summaries[0];faults=load(summary)
        require(faults['runner_sha256']==runner['copied_sha256'] and {f['id'] for f in faults['faults']}=={'F01','F02','F03'},'fault coverage mismatch')
        build=load(packet/'vis/retained-source/build.json')
        target_key='artifacts/runner-readiness-ten-project-pass/active/vis/'+build['binary_relative_path']
        runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'
        source_review={f['id']:f for f in load(reviewed/'source-fault-review.json')['faults']}
        for fault in faults['faults']:
            require(all(fault[k]==source_review[fault['id']][k] for k in ['path','original_source_sha256','mutated_source_sha256']),'source fault differs from independent pinned review')
            require(fault['restored_exact'],'source restoration unconfirmed')
            if fault['held_out']:require(host.endswith('Linux') and args.run=='39064393286' and fault['id']=='F03','heldout incorrectly reused')
            key='artifacts/runner-readiness-ten-project-pass/active/vis/src/'+fault['path']
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
                revisions=list((packet/'vis/retained-source/build-revisions').glob(label+'-*.json'))
                require(len(revisions)==1,'ambiguous actual build revision');revision=load(revisions[0])
                require(revision['binary_sha256']==fault[phase]['binary_sha256'],'build result identity mismatch')
                witness(revision['build_attempt'],0)
                files=witness(revision['version_attempt'],0)
                require(files[target_key]==revision['binary_sha256'],'built version probe used wrong executable')
        journeys=list((packet/'vis').glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous maintenance')
        journey_path=journeys[0];journey=load(journey_path)
        require(len(journey['attempts'])==12 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'incomplete maintenance')
        for row in journey['attempts']:witness(row['id'],1 if row['label'] in {'intended-file-change','intended-viewport-change'} else 0)
        require(sha256(journey_path.parent/'generated-workflow.yml')==journey['generated_workflow_sha256'],'workflow changed')
        removed=packet/'vis/retained-source/removed.json';removal=load(removed);index=load(removed.parent/'verified-index.json')
        require(removal['removed'] and removal['owned_relative_path']=='active/vis' and removal['source_archive_sha256']==canonical==index['archive_sha256'],'source removal or archive mismatch')
        for name in index['selected_restore']:require(sha256(removed.parent/'selected-restore'/name)==index['files'][name]['sha256'],'source restore mismatch')
        cells.append(dict(host=host,run=runs[host],run_conclusion=metadata['conclusion'],
            job_conclusion=jobs[0]['conclusion'],scenarios=20,report_sha256=sha256(report_path),
            source_fault_summary_sha256=sha256(summary),maintenance_sha256=sha256(journey_path),
            cleanup_receipt_sha256=sha256(removed),runner_sha256=runner['copied_sha256']))
    immutable_json(RAW/'vis/native-development-verification.json',dict(runs=runs,runner_source=SOURCE,cells=cells,
        phase='development',claim='Native gates verified; local checked removal required before admission.',archive_qualified=False))
    print('Verified both native Vis cells from actual events, source/binary hashes, reports, builds and restores.')


if __name__=='__main__':main()
