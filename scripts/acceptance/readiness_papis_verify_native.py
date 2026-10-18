"""Inspect actual Papis fault, maintenance, executable and native suite evidence."""
import argparse
import base64
from pathlib import Path
import shutil
import uuid

from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load
from readiness_papis_first_use import fixture_files
from readiness_papis_verify_first_use import PIN,ARCHIVE,require

SOURCE='3d50d81aae8f1d24f7a718e6e05b39069697b1a6'


def verifier(packet,identities=None):
    event_root=packet
    if identities is not None:
        event_root=RAW/'papis/verification-event-sets'/uuid.uuid4().hex
        (event_root/'events').mkdir(parents=True)
        copied={}
        for identity in sorted(identities):
            require(len(identity)==32 and all(c in '0123456789abcdef' for c in identity),'invalid selected attempt ID')
            for phase in ['started','identified','launched','finished']:
                source=packet/'events'/(identity+'-'+phase+'.json')
                destination=event_root/'events'/source.name;shutil.copyfile(source,destination)
                require(sha256(source)==sha256(destination),'selected immutable event copy changed')
                copied[source.name]=sha256(source)
        immutable_json(event_root/'selection.json',dict(events=copied,scope='All fault/maintenance referenced events only; original global stream remains untouched. No whole-campaign completeness claim.'))
    ledger=object.__new__(Campaign);ledger.raw=event_root;attempts=ledger.attempts()
    def witness(identity,expected=0):
        event=attempts[identity];finished=event['finished']
        require('launched' in event and event['started']['expected_exit']==expected and
            finished['category']=='passed' and finished['exit_code']==expected,'missing actual expected command outcome')
        require(finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],'command cleanup unconfirmed')
        ref=event['identified']['identity'];manifest=packet_file(packet,ref['manifest'],1024**2)
        require(sha256(manifest)==ref['sha256'],'changed prelaunch identity')
        console=packet_file(packet,event['started']['project']+'/'+identity+'/console.log',4*1024**2)
        require(sha256(console)==finished['console_sha256'],'changed actual command output')
        return load(manifest)['files']
    return attempts,witness


def result_ok(result,status):
    require(result['status']==status and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'result or cleanup unconfirmed')
    for step in result['steps']:
        if 'state' in step:require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state')


def verify_faults(packet,docs,profile,runtime,build,runner_sha,host,witness,original=False,fresh=False,original_fresh=False):
    summaries=list((packet/'papis/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=summaries[0];data=load(summary);faults=data['faults']
    expected_ids={'F01','F02','F03','F04'} if fresh else {'F01','F02','F03'}
    require(len(faults)==len(expected_ids) and {r['id'] for r in faults}==expected_ids and data['runner_sha256']==runner_sha,'source fault coverage/runner differs')
    require(data['interpreter_sha256']==runtime['python_sha256'],'fault interpreter receipt differs')
    selected=load(docs/('fault-selection-revision-2.json' if fresh else 'fault-selection.json'));review={r['id']:r for r in load(docs/('source-fault-review-revision-2.json' if fresh else 'source-fault-review.json'))['faults']}
    require(load(summary.parent/'selected-faults.json')['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json'),'fault batch belongs to another freeze')
    runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'+('.exe' if host=='Windows' else '')
    interpreter_key='artifacts/runner-readiness-ten-project-pass/active/papis/venv/'+('Scripts/python.exe' if host=='Windows' else 'bin/python')
    for fault in faults:
        declaration=next(r for r in selected['faults'] if r['id']==fault['id'])
        require(all(fault[k]==declaration[k] for k in ['path','spec','before','after','category']),'actual selected fault changed')
        require(all(fault[k]==review[fault['id']][k] for k in ['path','original_source_sha256','mutated_source_sha256']),'actual complete source mutation differs')
        require(fault['held_out']==bool((original and fault['id']=='F03') or (original_fresh and fault['id']=='F04')) and fault['restored_exact'],'heldout reuse or missing exact restoration')
        key='artifacts/runner-readiness-ten-project-pass/active/papis/src/'+fault['path']
        for phase,expected,digest in [('baseline',0,fault['original_source_sha256']),('mutated',1,fault['mutated_source_sha256']),('restored',0,fault['original_source_sha256'])]:
            identity=fault[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
            inputs=witness(identity,expected)
            require(inputs[key]==digest and inputs[runner_key]==runner_sha,'actual source or runner differs')
            contract=profile/'contracts'/fault['spec']
            require(inputs['artifacts/runner-readiness-ten-project-pass/papis/host-contracts/'+fault['spec']]==sha256(contract),'unchanged frozen fault contract not bound')
            if not original:
                require(inputs[interpreter_key]==runtime['python_sha256'],'actual test interpreter differs')
                require(inputs['artifacts/runner-readiness-ten-project-pass/active/papis/'+build['launcher_relative_path']]==build['launcher_sha256'],'actual installed test launcher differs')
            report=load(summary.parent/(fault['id']+'-'+phase+'.json'))
            require(report['runner_version']==('dev' if original else 'source-'+SOURCE),'fault uses another runner source')
            result=report['results'][0];result_ok(result,'failed' if expected else 'passed')
            if expected:require(result['failure']['category']==fault['category'],'wrong real fault diagnosis')
            if fault['id'] in {'F03','F04'} and phase=='mutated':
                failed=next(i for i,s in enumerate(result['steps']) if s['status']=='failed');prior=result['steps'][:failed]
                require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior},'F03 lacks prior passing screen and exact exit')
                if fault['id']=='F04':
                    state=result['steps'][failed]['state']
                    require(state['kind']=='entries' and state['path']=='exported','F04 was not rejected by unchanged exact exported entries')
        for phase,digest in [('mutation_validation',fault['mutated_source_sha256']),('restored_validation',fault['original_source_sha256'])]:
            validation=fault[phase]
            require(validation['source_sha256']==digest and validation['interpreter_sha256']==runtime['python_sha256'],'syntax/version source receipt differs')
            for event in [validation['syntax_attempt'],validation['version_attempt']]:
                inputs=witness(event)
                require(inputs[key]==digest and inputs[interpreter_key]==runtime['python_sha256'],'actual validation source/interpreter differs')
    return summary


def verify_maintenance(packet,contracts,witness):
    journeys=list((packet/'papis').glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous maintenance batch')
    path=journeys[0];journey=load(path);package=path.parent/'package'
    require(len(journey['attempts'])==12 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'incomplete maintenance or relocation')
    for row in journey['attempts']:witness(row['id'],1 if row['label'].startswith('intended-') else 0)
    original=load(contracts/'N01.json');updated=load(package/'N01.json')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.txt')
    require(base64.b64decode(updated['steps'][index]['state']['bytes_base64'])==b'reviewed sentinel revision two\n','selected file bytes differ')
    updated['steps'][index]=original['steps'][index]
    command=updated['command'];position=command.index('export')
    require(command[position-3:position-1]==['--set','header-format'] and command[position-1].startswith('Reviewed <ansired>'),'unreviewed selected display override')
    del command[position-3:position]
    require(updated==original,'selected maintenance changed unrelated expectations')
    snapshot=next(s['snapshot'] for s in original['steps'] if 'snapshot' in s)
    expected=(contracts/'snapshots'/snapshot).read_bytes().replace(b'Alpha Book',b'Reviewed Alpha Book').replace(b'Beta Book',b'Reviewed Beta Book')
    require((package/'snapshots'/snapshot).read_bytes()==expected,'selected screen differs from independent prefix oracle')
    suffix=load(package/'rerecorded-suffix.json');expected=fixture_files();expected['sentinel.txt']=b'reviewed sentinel revision two\n'
    expected.update({'exported/info.yaml':expected['library/beta/info.yaml'],'exported/paper.txt':expected['library/beta/paper.txt']})
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in suffix['steps'] if s.get('state',{}).get('kind')=='file'}
    require(actual==expected and [s for s in suffix['steps'] if s.get('key')=='Enter']==[dict(key='Enter')],'suffix selected wrong document or retained discarded input')
    require(sha256(package/'N01.json')==journey['maintained_spec_sha256'] and sha256(path.parent/'relocated \u96ea route/N01.json')==journey['relocated_spec_sha256'],'maintained/relocated bytes differ')
    require(sha256(path.parent/'generated-workflow.yml')==journey['generated_workflow_sha256'],'generated workflow changed')
    return path


def main():
    global SOURCE
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--local-original',action='store_true');parser.add_argument('--fresh',action='store_true');parser.add_argument('--replicas',action='store_true');parser.add_argument('--source-revision',default=SOURCE);parser.add_argument('--output',type=Path);args=parser.parse_args()
    SOURCE=args.source_revision
    require(len(SOURCE)==40 and all(c in '0123456789abcdef' for c in SOURCE),'invalid source revision')
    require(bool(args.run)!=args.local_original,'select a native run or local original')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis'
    if args.local_original:
        packet=RAW;identities=set()
        summaries=list((packet/'papis/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous original batch')
        for fault in load(summaries[0])['faults']:
            identities.update(fault[key] for key in ['baseline_attempt','mutation_attempt','restored_attempt'])
            for phase in ['mutation_validation','restored_validation']:
                identities.update(fault[phase][key] for key in ['syntax_attempt','version_attempt'])
        journeys=list((packet/'papis').glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous maintenance')
        identities.update(row['id'] for row in load(journeys[0])['attempts'])
        attempts,witness=verifier(packet,identities);active=RAW/'active/papis'
        runtime=load(active/'runtime.json');build=load(active/'build.json');runner_sha=sha256(RAW/'bin/playtestr.exe')
        profile=docs/'native-profiles/windows'
        summary=verify_faults(packet,docs,profile,runtime,build,runner_sha,'Windows',witness,True)
        maintenance=verify_maintenance(packet,profile/'contracts',witness)
        record=dict(schema_version=1,runner_source='unqualified local dev binary; embedded VCS e351a3cb99162f2092f1d91bdf18637fd69a68ea, modified=true; actual Go source not established',original_host='local Windows',summary_sha256=sha256(summary),
            runner_sha256=runner_sha,build_metadata_observation='c628c4b9df1547e3abe3ff97cbf0e1b5',
            maintenance_sha256=sha256(maintenance),source_faults=3,current_source_fault_credit=0,
            original_heldout='Experimental F03 only; no current-source holdout credit. A fresh fault must be declared and executed with the exact pinned runner.',
            provenance='Actual editable source per test; actual interpreter hashes in syntax/version commands. Direct named-test interpreter/launcher hashing was added afterward; final native qualification must include it.',final_archive_credit=False)
        immutable_json(RAW/'papis/local-original-verification.json',record)
        destination=docs/'original-source-faults';destination.mkdir(exist_ok=False)
        for name in ['summary.json','selected-faults.json','F01.patch','F02.patch','F03.patch']:
            shutil.copyfile(summary.parent/name,destination/name)
        immutable_json(docs/'local-original-verification.json',record)
        print('Verified historical dev-binary source faults/restores and maintenance only; current-source qualification and holdout credit remain zero.')
        return
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    require(not args.fresh or args.replicas or args.run=='39099744836','fresh heldout verifier binds the first committed native consumption; later runs require replica verification')
    require(not args.replicas or (args.fresh and args.output),'replica verification requires current four-fault selection and a new output path')
    run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),'native qualification failed or incomplete')
    cells=[]
    for host in ['Linux','Windows']:
        packet=run/('playtestr-'+host);attempts,witness=verifier(packet)
        profile=docs/'native-profiles/windows' if host=='Windows' else docs
        freeze=load(profile/'reviewed-contract-freeze.json');contracts=packet/'papis/host-contracts'
        for name,digest in freeze['all_package_inputs'].items():require(sha256(contracts/name)==digest,'frozen native payload changed or missing')
        runner=load(packet/'papis-native-runner.json');require(runner['source_revision']==SOURCE and runner['candidate_sha256']==runner['copied_sha256'],'wrong native runner')
        retained=packet/'papis/retained-source';runtime=load(retained/'runtime.json');build=load(retained/'build.json')
        require(build['pin']==runtime['source_pin']==PIN,'wrong target pin')
        summaries=list((packet/'papis/suites').glob('*/results.json'));require(len(summaries)==1,'ambiguous native ordinary suite')
        report_path=summaries[0];report=load(report_path)
        require(report['runner_version']=='source-'+SOURCE and report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'ordinary twenty-case suite incomplete')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'wrong suite selection')
        suites=[identity for identity,event in attempts.items() if event['started']['label']=='public-recorded-suite'];require(len(suites)==1,'ambiguous actual suite')
        inputs=witness(suites[0]);suffix='.exe' if host=='Windows' else ''
        require(inputs['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix]==runner['copied_sha256'],'ordinary runner not bound')
        require(inputs['artifacts/runner-readiness-ten-project-pass/active/papis/'+build['launcher_relative_path']]==build['launcher_sha256'],'ordinary launcher not bound')
        require(inputs['artifacts/runner-readiness-ten-project-pass/active/papis/venv/'+('Scripts/python.exe' if host=='Windows' else 'bin/python')]==runtime['python_sha256'],'ordinary interpreter not bound')
        for name,digest in freeze['all_package_inputs'].items():require(inputs['artifacts/runner-readiness-ten-project-pass/papis/host-contracts/'+name]==digest,'ordinary payload not bound')
        require('artifacts/runner-readiness-ten-project-pass/papis/host-contracts/fixtures/E10/library' in load(packet_file(packet,attempts[suites[0]]['identified']['identity']['manifest'],1024**2))['fixture_directories'],'declared empty fixture directory not bound')
        for result in report['results']:result_ok(result,'passed')
        summary=verify_faults(packet,docs,profile,runtime,build,runner['copied_sha256'],host,witness,fresh=args.fresh,original_fresh=args.fresh and not args.replicas and host=='Linux')
        maintenance=verify_maintenance(packet,contracts,witness)
        removed=load(retained/'removed.json');index=load(retained/'verified-index.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/papis' and removed['source_archive_sha256']==ARCHIVE==index['archive_sha256'],'source cleanup or archive differs')
        for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'source restore changed')
        cells.append(dict(host='playtestr-'+host,run=args.run,scenarios=20,runner_sha256=runner['copied_sha256'],
            report_sha256=sha256(report_path),source_fault_summary_sha256=sha256(summary),maintenance_sha256=sha256(maintenance),cleanup_receipt_sha256=sha256(retained/'removed.json')))
    output=(args.output or RAW/'papis'/('native-fresh-development-verification.json' if args.fresh else 'native-development-verification.json')).resolve();output.relative_to(ROOT)
    immutable_json(output,dict(runner_source=SOURCE,cells=cells,phase='development',real_faults=4 if args.fresh else 3,original_current_source_heldout=dict(run='39099744836' if args.replicas else args.run,host='Linux',fault='F04') if args.fresh else None,faults_are_replicas=args.replicas,final_archive_credit=False))
    if args.fresh and not args.replicas:
        original=list((run/'playtestr-Linux/papis/faults').glob('*/summary.json'))[0]
        destination=docs/'original-current-source-faults';destination.mkdir(exist_ok=False)
        for name in ['summary.json','selected-faults.json','F01.patch','F02.patch','F03.patch','F04.patch']:
            shutil.copyfile(original.parent/name,destination/name)
    print('Independently verified both native Papis suites, actual runtimes, source fault replicas, public maintenance and cleanup.')


if __name__=='__main__':main()
