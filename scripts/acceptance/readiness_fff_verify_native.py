"""Independently inspect actual native fff events, inputs, outcomes and restore."""
import argparse
import base64
from pathlib import Path

from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load

SOURCE='f46f2409985af077fd29723ab963d24792eabbbe'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--source-revision',default=SOURCE)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    source_revision=args.source_revision
    require(len(source_revision)==40 and all(c in '0123456789abcdef' for c in source_revision),'invalid source revision')
    runs={'playtestr-Linux':args.run,'playtestr-macOS':args.run}
    for identity in set(runs.values()):require(identity.isascii() and identity.isdecimal(),'invalid native run ID')
    reviewed=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
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
        runner=load(packet/'fff-native-runner.json')
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
        profile=reviewed/'native-profiles/macos' if host.endswith('macOS') else reviewed
        native_freeze=load(profile/'reviewed-contract-freeze.json')
        contracts=packet/'fff/host-contracts'
        for name,digest in native_freeze['all_package_inputs'].items():
            require(sha256(contracts/name)==digest,'actual native profile payload missing or changed')
        build=load(packet/'fff/retained-source/build.json')
        runtime=load(packet/'fff/retained-source/runtime.json')
        require(build['build_kind']=='interpreted Bash source; no compilation or installation','incorrect execution-kind claim')
        require(build['binary_sha256']==load(reviewed/'source-review.json')['reviewed_inputs']['fff'],'wrong original interpreted script')
        reports=list((packet/'fff/suites').glob('*/results.json'));require(len(reports)==1,'ambiguous ordinary suite report')
        report_path=reports[0];report=load(report_path)
        require(report['runner_version']=='source-'+source_revision,'wrong runner source')
        require(report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'incomplete ordinary suite')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'wrong ordinary selection')
        suites=[k for k,v in attempts.items() if v['started']['label']=='public-recorded-suite']
        require(len(suites)==1,'ambiguous ordinary suite witness');files=witness(suites[0],0)
        for name in native_freeze['all_package_inputs']:
            require(files['artifacts/runner-readiness-ten-project-pass/fff/host-contracts/'+name]==sha256(contracts/name),'suite input not bound')
        require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr']==runner['copied_sha256'],'suite used another runner')
        for result in report['results']:result_ok(result,'passed')
        summaries=list((packet/'fff/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
        summary=summaries[0];faults=load(summary)
        require(faults['runner_sha256']==runner['copied_sha256'] and {f['id'] for f in faults['faults']}=={'F01','F02','F03'},'fault coverage mismatch')
        build=load(packet/'fff/retained-source/build.json')
        target_key='artifacts/runner-readiness-ten-project-pass/active/fff/'+build['binary_relative_path']
        runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'
        source_review={f['id']:f for f in load(reviewed/'source-fault-review.json')['faults']}
        for fault in faults['faults']:
            require(all(fault[k]==source_review[fault['id']][k] for k in ['path','original_source_sha256','mutated_source_sha256']),'source fault differs from independent pinned review')
            require(fault['restored_exact'],'source restoration unconfirmed')
            if fault['held_out']:require(host.endswith('Linux') and args.run=='39070554085' and fault['id']=='F03','heldout incorrectly reused')
            key='artifacts/runner-readiness-ten-project-pass/active/fff/src/'+fault['path']
            require(fault['original_source_sha256']!=fault['mutated_source_sha256'],'unchanged actual mutated script')
            for phase,expected,digest,binary_digest in [
                ('baseline',0,fault['original_source_sha256'],fault['original_source_sha256']),
                ('mutated',1,fault['mutated_source_sha256'],fault['mutated_source_sha256']),
                ('restored',0,fault['original_source_sha256'],fault['original_source_sha256'])]:
                event=fault[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
                files=witness(event,expected)
                require(files[key]==digest and files[target_key]==binary_digest and files[runner_key]==runner['copied_sha256'],'actual source/executable identity mismatch')
                outcome=load(summary.parent/(fault['id']+'-'+phase+'.json'))['results'][0]
                result_ok(outcome,'failed' if expected else 'passed')
                if expected:require(outcome['failure']['category']==fault['category'],'wrong mutant diagnosis')
                if phase=='mutated' and fault['id']=='F03':
                    failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed');prior=outcome['steps'][:failed]
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior},'F03 lacks prior passing screen/exit')
            for phase,digest in [('mutation_validation',fault['mutated_source_sha256']),('restored_validation',fault['original_source_sha256'])]:
                revision=fault[phase]
                require(revision['script_sha256']==digest and revision['interpreter_sha256']==runtime['bash_sha256'],'interpreted validation identity differs')
                for event in [revision['syntax_attempt'],revision['version_attempt']]:
                    actual=witness(event,0)
                    require(actual[key]==digest,'syntax/version inspected another script')
        require(faults['interpreter_sha256']==runtime['bash_sha256']==build['interpreter_sha256'],'interpreter receipts disagree')
        journeys=list((packet/'fff').glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous maintenance')
        journey_path=journeys[0];journey=load(journey_path)
        require(len(journey['attempts'])==12 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'incomplete maintenance')
        for row in journey['attempts']:witness(row['id'],1 if row['label'] in {'intended-file-change','intended-screen-format-change'} else 0)
        require(sha256(journey_path.parent/'generated-workflow.yml')==journey['generated_workflow_sha256'],'workflow changed')
        maintained=journey_path.parent/'package'
        original=load(contracts/'N01.json');updated=load(maintained/'N01.json')
        step=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.txt')
        require(base64.b64decode(updated['steps'][step]['state']['bytes_base64'])==b'reviewed sentinel revision two\n','maintained sentinel differs from independent expected bytes')
        updated['steps'][step]=original['steps'][step]
        require(updated==original,'selected file update changed unrelated expectations')
        screen=load(maintained/'N04.json');original=load(contracts/'N04.json')
        require(screen['env'].pop('FFF_FILE_FORMAT')=='reviewed %f' and screen==original,'selected screen update changed unrelated contract')
        snapshot=next(s['snapshot'] for s in original['steps'] if 'snapshot' in s)
        expected=load(contracts/'snapshots'/snapshot)
        expected['text']=''.join('reviewed '+line if line.strip() else line for line in expected['text'].splitlines(keepends=True))
        require(load(maintained/'snapshots'/snapshot)==expected,'selected screen differs from independent prefix oracle')
        suffix=load(maintained/'rerecorded-suffix.json')
        saved={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in suffix['steps'] if s.get('state',{}).get('kind')=='file'}
        require(saved=={'maintained.txt':b'','source.txt':b'reviewed source\n','sentinel.txt':b'reviewed sentinel revision two\n'},'suffix file expectations differ')
        require(not any('discarded.txt' in s.get('text','') for s in suffix['steps']) and any(s.get('state')=={'kind':'absent','path':'discarded.txt'} for s in suffix['steps']),'old suffix input retained or absence missing')
        removed=packet/'fff/retained-source/removed.json';removal=load(removed);index=load(removed.parent/'verified-index.json')
        require(removal['removed'] and removal['owned_relative_path']=='active/fff' and removal['source_archive_sha256']==canonical==index['archive_sha256'],'source removal or archive mismatch')
        for name in index['selected_restore']:require(sha256(removed.parent/'selected-restore'/name)==index['files'][name]['sha256'],'source restore mismatch')
        cells.append(dict(host=host,run=runs[host],run_conclusion=metadata['conclusion'],
            job_conclusion=jobs[0]['conclusion'],scenarios=20,report_sha256=sha256(report_path),
            source_fault_summary_sha256=sha256(summary),maintenance_sha256=sha256(journey_path),
            cleanup_receipt_sha256=sha256(removed),runner_sha256=runner['copied_sha256']))
    output=(args.output or RAW/'fff/native-development-verification.json').resolve();output.relative_to(ROOT)
    immutable_json(output,dict(runs=runs,runner_source=source_revision,cells=cells,
        phase='development',claim='Native gates verified; local source-only checked removal required before admission.',archive_qualified=False))
    print('Verified both native fff cells from actual events, source/binary hashes, reports, builds and restores.')


if __name__=='__main__':main()
