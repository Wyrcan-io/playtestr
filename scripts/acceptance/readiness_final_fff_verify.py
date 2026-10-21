"""Strict actual final fff batches, supported input boundary and source-fault audit."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import packet_file,read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','macos'],required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    host=args.host;parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'complete native final jobs required')
    packet=parent/('final-fff-'+('Linux' if host=='linux' else 'macOS'))
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    profile=docs/'native-profiles/macos' if host=='macos' else docs
    frozen=load(profile/'reviewed-contract-freeze.json');candidate=load(docs.parent/'migration-candidate-freeze.json')
    cell=next(c for c in candidate['cells'] if c['host']==('darwin' if host=='macos' else host))
    installed=load(packet/'private-install/migration-v2'/('darwin-arm64' if host=='macos' else 'linux-amd64')/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],'different private archive')
    source_review=load(docs/'source-review.json');canonical=source_review['archive_sha256']
    target=packet/'fff';retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    require(build['binary_sha256']==source_review['reviewed_inputs']['fff'] and build['build_kind']=='interpreted Bash source; no compilation or installation','different real interpreted target')
    expected_runner_sha256=cell['binary_sha256']
    require(installed['source_revision']==candidate['source_revision'],'installed archive source differs')
    package=target/'host-contracts'
    for name,h in frozen['all_package_inputs'].items():require(sha256(package/name)==h,'original native input changed')
    ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
    def witness(identity,expected=0):
        events=attempts[identity];end=events['finished']
        require(all(e['phase']=='final-archive' for e in events.values()),'actual final phase differs')
        require('launched' in events and events['started']['expected_exit']==expected and end['category']=='passed'
            and end['exit_code']==expected and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command or cleanup differs')
        require(sha256(packet/events['started']['project']/identity/'console.log')==end['console_sha256'],'actual command output changed')
        return load_manifest(packet,events['identified']['identity'])['files']
    def result_ok(row,status):
        require(row['status']==status and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'actual result/cleanup differs')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-execution state')
    final_root=target/'final-series';intent=load(final_root/'intent.json')
    declaration_file='final-series-declaration-v2.json'
    declaration=load(docs/declaration_file)
    require(intent['declaration_file']==declaration_file,'final series declaration differs')
    for name,indices in declaration['segmented_text_steps_by_host'][host].items():
        original=load(profile/'contracts'/name);derived=[]
        for i,step in enumerate(original['steps']):
            text=step.get('text','');prior=original['steps'][i-1].get('expect','') if i else ''
            if (len(text)>1 and all(ord(c)>=32 and ord(c)!=127 for c in text) and prior.endswith(':')
                    and (prior in {'mkfile:','mkdir:','go to dir:'} or prior.startswith('rename '))):derived.append(i+1)
        require(indices==derived,'declared segmentation exceeds the reviewed printable-field boundary')
    require(intent['declaration_sha256']==sha256(docs/declaration_file)
            and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256']
            and intent['target_build_sha256']==sha256(retained/'build.json') and intent['target_pin']==build['pin']
            and intent['canonical_package_inputs']==frozen['all_package_inputs'], 'final intent changed')
    require(declaration['candidate_freeze_sha256']==sha256(docs.parent/'migration-candidate-freeze.json'), 'declared final archive changed')
    all_rows=[];invocations=set();commands=set();reports=[]
    for batch in declaration['batches']:
        folder=final_root/str(batch['number']);prepared=load(folder/'prepared.json');current=folder/batch['package_directory']
        require(prepared['batch']==batch and set(prepared['package_inputs'])==set(frozen['all_package_inputs']), 'batch input coverage differs')
        for name,h in prepared['package_inputs'].items():
            require(sha256(current/name)==h,'prepared batch bytes changed')
            if name not in frozen['contracts']:require(h==frozen['all_package_inputs'][name],'fixture or snapshot changed')
        summary=load(folder/'complete.json');require(summary['observed']==20 and len(summary['records'])==20,'incomplete final batch')
        for number,name in enumerate(sorted(frozen['contracts'])):
            spec=current/name;contract=load(spec);before=load(profile/'contracts'/name);expected=dict(before)
            require(sha256(profile/'contracts'/name)==frozen['contracts'][name],'canonical native contract changed')
            if batch['input_chunks']:
                size=batch['input_chunks'];steps=[]
                allowed=declaration['segmented_text_steps_by_host'][host][name]
                for step_number,step in enumerate(before['steps'],1):
                    if set(step)=={'text'} and len(step['text'])>size and step_number in allowed:
                        steps.extend({'text':step['text'][i:i+size]} for i in range(0,len(step['text']),size))
                    else:steps.append(step)
                expected['steps']=steps
            require(contract==expected,'executed contract exceeds declared input segmentation')
            require(load(folder/(name+'.planned.json'))==dict(batch=batch['number'],number=number,spec=name,
                runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],spec_sha256=sha256(spec),
                prepared_sha256=sha256(folder/'prepared.json'),owned_two_second_worker=batch['contention']), 'actual launch plan differs')
            observed=load(folder/(name+'.observed.json'));command=observed['attempt'];report_path=folder/(name+'.report.json')
            require(command not in commands,'duplicate final command');commands.add(command)
            report=load(report_path);result=report['results'][0]
            require(report['runner_version']==candidate['version'] and report['summary']==dict(total=1,passed=1,failed=0,cancelled=0,not_run=0)
                and observed['report_sha256']==sha256(report_path) and observed['invocation_id']==result['invocation_id'], 'actual final report differs')
            result_ok(result,'passed')
            require(len(result['steps'])==len(contract['steps']) and all(x['status']=='passed' for x in result['steps']), 'incomplete positive step evidence')
            require(result['invocation_id']==result['workspace']['id'] and result['invocation_id'] not in invocations,'final workspace reused')
            invocations.add(result['invocation_id'])
            event=attempts[command]
            require(event['started']['label']=='final-batch-'+str(batch['number'])+'-'+name
                and event['started']['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if batch['contention'] else 'ordinary'), 'actual schedule differs')
            bound=witness(command)
            for input_name in prepared['package_inputs']:
                # Only selected fixtures/snapshots are invocation inputs.
                path=current/input_name
                selected=(input_name==name or input_name.startswith(contract['workspace']['fixture'].rstrip('/')+'/')
                    or any(x.get('snapshot')==input_name.removeprefix('snapshots/') for x in contract['steps']))
                if selected:require(bound['artifacts/runner-readiness-ten-project-pass/'+path.relative_to(packet).as_posix()]==sha256(path),'actual selected input not bound')
            require(bound[installed['binary']]==cell['binary_sha256'] and bound['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff']==source_review['reviewed_inputs']['fff'],'actual runner or interpreted target differs')
            all_rows.append(observed);reports.append(report_path)
        require(summary['records']==all_rows[-20:],'batch summary does not match actual observations')
    require(len(all_rows)==240 and len(invocations)==240,'final native denominator differs')
    summaries=list((packet/'fff/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=summaries[0];faults=load(summary)
    require(faults['runner_sha256']==expected_runner_sha256 and {f['id'] for f in faults['faults']}=={'F01','F02','F03'},'fault coverage mismatch')
    build=load(packet/'fff/retained-source/build.json')
    target_key='artifacts/runner-readiness-ten-project-pass/active/fff/'+build['binary_relative_path']
    runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'
    source_review={f['id']:f for f in load(docs/'source-fault-review.json')['faults']}
    for fault in faults['faults']:
        require(all(fault[k]==source_review[fault['id']][k] for k in ['path','original_source_sha256','mutated_source_sha256']),'source fault differs from independent pinned review')
        require(fault['restored_exact'],'source restoration unconfirmed')
        require(not fault['held_out'],'final calibration is a replica, not another original heldout')
        key='artifacts/runner-readiness-ten-project-pass/active/fff/src/'+fault['path']
        require(fault['original_source_sha256']!=fault['mutated_source_sha256'],'unchanged actual mutated script')
        for phase,expected,digest,binary_digest in [
            ('baseline',0,fault['original_source_sha256'],fault['original_source_sha256']),
            ('mutated',1,fault['mutated_source_sha256'],fault['mutated_source_sha256']),
            ('restored',0,fault['original_source_sha256'],fault['original_source_sha256'])]:
            event=fault[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
            files=witness(event,expected)
            require(files[key]==digest and files[target_key]==binary_digest and files[runner_key]==expected_runner_sha256,'actual source/executable identity mismatch')
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
    calibration_rows=[]
    for fault in faults['faults']:
        for phase,event_key in [('baseline','baseline_attempt'),('mutated','mutation_attempt'),('restored','restored_attempt')]:
            path=summary.parent/(fault['id']+'-'+phase+'.json');value=load(path);row=value['results'][0]
            require(value['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==fault['spec'],'actual calibration used another runner/contract')
            require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'calibration workspace/invocation reused')
            invocations.add(row['invocation_id']);command=fault[event_key]
            require(command not in commands,'calibration command reused');commands.add(command)
            bound=witness(command,1 if phase=='mutated' else 0);contract=load(package/fault['spec'])
            for relative,digest in frozen['all_package_inputs'].items():
                selected=(relative==fault['spec'] or relative.startswith(contract['workspace']['fixture'].rstrip('/')+'/')
                    or any(s.get('snapshot')==relative.removeprefix('snapshots/') for s in contract['steps']))
                if selected:require(bound['artifacts/runner-readiness-ten-project-pass/fff/host-contracts/'+relative]==digest,'calibration changed an approved input')
            calibration_rows.append(dict(fault=fault['id'],phase=phase,command=command,invocation_id=row['invocation_id'],report_sha256=sha256(path)))

    removal=load(retained/'removed.json');index=load(retained/'verified-index.json')
    require(removal['removed'] and removal['owned_relative_path']=='active/fff' and removal['source_archive_sha256']==canonical==index['archive_sha256'],'source/runtime removal differs')
    require(load(retained/'removal-prepared.json')['runtime_processes_verified'],'actual runtime cleanup not checked')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected original restore differs')
    immutable_json(docs/('final-v2-verified-'+host+'-r2.json'),dict(auditor_revision=2,run=args.run,host=host,scenarios=20,ordinary_executions=240,
        calibration_executions=9,runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],
        source_fault_summary_sha256=sha256(summary),cleanup_receipt_sha256=sha256(retained/'removed.json'),observations=all_rows,
        calibration_observations=calibration_rows,
        scope='Exact native final archive/phase, twelve fresh executions per reviewed case, supported printable-field variations preserving batched command/control groups, real Bash source faults/restoration and checked cleanup. First final failures and unexplained Linux quit timeout remain preserved; no universal stability or causal repair claim.',final_archive_credit=0))
    print('Verified final fff 240 ordinary executions, actual source faults/restoration and cleanup:',host)


if __name__=='__main__':main()
