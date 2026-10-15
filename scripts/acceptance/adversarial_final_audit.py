"""Audit retained final evidence; counts never come from configured jobs alone."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from adversarial_process import DOC,read_attempts
from adversarial_final_guard import inspect
from adversarial_freeze_runner import source_inputs


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def belongs_to_campaign(events,run,attempt=None):
    start=events.get('started',{})
    return (start.get('ci_run_id')==str(run) and
            (attempt is None or start.get('ci_run_attempt')==str(attempt)))


def repeated_cleanup_passed(events):
    passed=sum(e.get('Action')=='pass' and e.get('Test')=='TestAdversarialStubbornUnixDescendantCleanup' for e in events)
    return passed==50 and not any(e.get('Action')=='fail' for e in events)


def repetition_group(attempts,positions,project,case_name,ordinary_ids):
    """Find the actual completed parent containing the ten ordinary children."""
    if len(ordinary_ids)!=10 or len(set(ordinary_ids))!=10:
        raise RuntimeError('Ten distinct ordinary executions are required to bind a repetition group')
    candidates=[]
    for ident,events in attempts.items():
        start=events.get('started',{})
        if start.get('project')!=project or start.get('label')!='native-repetitions-'+case_name:continue
        first=positions.get((ident,'started'));last=positions.get((ident,'finished'))
        if first is None or last is None:continue
        if all(first<positions.get((child,'started'),-1)<positions.get((child,'finished'),-1)<last
               for child in ordinary_ids):
            candidates.append((ident,events,first,last))
    if len(candidates)!=1:
        raise RuntimeError('A unique actual repetition group is missing or ambiguous')
    ident,events,first,last=candidates[0]
    if (events.get('finished',{}).get('category')!='passed' or
        events.get('finished',{}).get('cleanup_errors') or 'launched' not in events):
        raise RuntimeError('Actual repetition group failed or was not launched')
    members={child for child,rows in attempts.items()
             if first<positions.get((child,'started'),-1)<positions.get((child,'finished'),-1)<last}
    return ident,members


def audit(run):
    if not run.isdigit():raise RuntimeError('Invalid native run identifier')
    corpus=inspect(require_development=True)
    root=DOC/'native'/run
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    info=manifest['run'];source=info['headSha'];errors=list(corpus['missing'])
    if info['status']!='completed' or info['conclusion']!='success':
        errors.append('Final native run did not complete successfully')
    records={a['artifact']:a for a in manifest['artifacts']}
    for record in records.values():
        folder=root/record['artifact']
        for relative,expected in record['files'].items():
            path=folder/relative
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(folder.resolve(strict=True)):
                raise RuntimeError('Retained evidence escapes its artifact')
            if digest(path)!=expected:raise RuntimeError('Retained artifact hash mismatch: '+str(path))
    frozen={};systems={'linux':'Linux','macos':'Darwin','windows':'Windows'}
    runners={'linux':'ubuntu-24.04','macos':'macos-15','windows':'windows-2025'}
    current_inputs=source_inputs()
    matrix=json.loads((DOC/'coverage-matrix.json').read_text(encoding='utf-8'))
    for host,runner in runners.items():
        name='adversarial-final-controls-'+runner
        if name not in records:errors.append('Missing native final controls: '+host);continue
        record=records[name];folder=root/name;freeze=folder/'frozen-runner.json'
        if not freeze.is_file():errors.append('Missing frozen manifest: '+host);continue
        identity=json.loads(freeze.read_text(encoding='utf-8'));frozen[host]=(identity,digest(freeze))
        if identity['source']!=source or identity['source_inputs_normalized_lf_sha256']!=current_inputs:
            errors.append('Frozen Go source identity differs: '+host)
        if str(identity.get('run_id'))!=run:errors.append('Frozen build belongs to another campaign: '+host)
        if identity['host_system']!=systems[host]:errors.append('Frozen native platform mismatch: '+host)
        applicable={c['id'] for c in matrix['controls'] if host in c['hosts']}
        if not applicable.issubset(set(record.get('passed_mapped_controls',[]))):
            errors.append('Applicable mapped native controls missing: '+host)
        if record.get('race_failed_tests') or not record.get('race_passed_tests'):
            errors.append('Native race evidence failed or missing: '+host)
        if host=='macos':
            repeated=folder/'stubborn-race-events.jsonl'
            if not repeated.is_file():
                errors.append('Repeated macOS cleanup evidence missing')
            else:
                events=[json.loads(line) for line in repeated.read_text(encoding='utf-8').splitlines()]
                if not repeated_cleanup_passed(events):
                    errors.append('Fifty repeated macOS cleanup checks did not pass')
        summaries=list((folder/'wizard-reproduction').glob('*/summary.json'))
        if len(summaries)!=(2 if host=='windows' else 1):errors.append('Missing wizard variant: '+host)
        for summary in summaries:
            value=json.loads(summary.read_text(encoding='utf-8'))
            if (len(value['attempts'])!=100 or value['failures'] or
                not all(a.get('passed') is True for a in value['attempts']) or
                value.get('runner_sha256')!=identity['binary_sha256']):
                errors.append('Historical wizard sequence failed or used another runner: '+host)
    attempts={};ledger=read_attempts()
    positions={(row['id'],row['event']):index for index,row in enumerate(ledger)}
    for row in ledger:attempts.setdefault(row['id'],{})[row['event']]=row
    by_label={}
    for events in attempts.values():
        start=events.get('started',{});provenance=events.get('identified',{}).get('identity',{})
        key=(start.get('project'),provenance.get('runner_sha256'),start.get('label'))
        by_label.setdefault(key,[]).append(events)
    for host,(identity,_) in frozen.items():
        build=attempts.get(identity['build_evidence_id'],{})
        if (build.get('started',{}).get('label')!='freeze-host-runner-build' or
            build.get('finished',{}).get('category')!='passed' or 'launched' not in build or
            not belongs_to_campaign(build,run)):
            errors.append('Actual frozen build event missing: '+host)
    pairs=[];fault_total=state_fault_total=0;distinct_faults=set();distinct_state_faults=set()
    for project in corpus['projects']:
        name=project['project'];config=json.loads((DOC/name/'scenarios.json').read_text(encoding='utf-8'))
        for host in project['planned_hosts']:
            artifact='adversarial-final-'+name+'-'+runners[host]
            if artifact not in records:errors.append('Missing final project artifact: '+artifact);continue
            folder=root/artifact;system=systems[host]
            native_path=folder/('native-'+name+'-'+system+'.json')
            cleanup_path=folder/('cleanup-'+system+'.json')
            if not native_path.is_file() or not cleanup_path.is_file():
                errors.append('Qualification or deletion receipt missing: '+artifact);continue
            native=json.loads(native_path.read_text(encoding='utf-8'))
            cleanup=json.loads(cleanup_path.read_text(encoding='utf-8'))
            if host not in frozen:continue
            identity,freeze_sha=frozen[host]
            if (native['phase']!='Final frozen-source qualification' or native['source']!=source or
                str(native['run_id'])!=run or native['runner_sha256']!=identity['binary_sha256'] or
                native.get('frozen_manifest_sha256')!=freeze_sha):
                errors.append('Project used another source, run or runner: '+artifact)
            if cleanup.get('removed') is not True or cleanup.get('source')!=source:
                errors.append('Owned application deletion not proved: '+artifact)
            if name=='yazi' and host=='windows' and (native.get('external_state_cleanup') or {}).get('removed') is not True:
                errors.append('Windows actual known-folder teardown not proved')
            inventory=json.loads((folder/'report-inventory.json').read_text(encoding='utf-8'))
            states=json.loads((folder/'state-inventory.json').read_text(encoding='utf-8'))
            state_ids={r['attempt_id'] for r in states if r['observed'].get('passed') is True}
            ordinary=0;state_count=0
            for case in config['cases']:
                suffix=case.get('baseline_suffix_by_host',config.get('baseline_suffix_by_host',{})).get(system,'')
                case_name=case['name']+suffix
                spec=DOC/name/(case_name+'.json');expected_spec=digest(spec)
                matches=[r for r in inventory if re.fullmatch(re.escape(case_name)+r'-final-[0-9]+-[0-9]+\.json',Path(r['path']).name)]
                indices={int(Path(r['path']).name[len(case_name)+7:].split('-')[0]) for r in matches}
                if len(matches)!=10 or indices!=set(range(10)):
                    errors.append('Ten unique repetitions missing: '+artifact+'/'+case_name)
                for report in matches:
                    if report['summary']['passed']!=1 or any(r['status']!='passed' or not r['cleanup'].get('confirmed_exited') for r in report['results']):
                        errors.append('Failed final repetition: '+report['path'])
                # Original identified events must bind the actual runner and
                # public contract to each launched, successfully finished run.
                qualified=[]
                final_attempts=[events for i in range(10)
                    for events in by_label.get((name,identity['binary_sha256'],case_name+'-final-'+str(i)),[])
                    if belongs_to_campaign(events,run,native['run_attempt'])]
                for events in final_attempts:
                    start=events.get('started',{});identified=events.get('identified',{});finish=events.get('finished',{})
                    provenance=identified.get('identity',{})
                    if provenance.get('runner_sha256')!=identity['binary_sha256']:continue
                    if provenance.get('target_revision')!=project['source_pin']:
                        errors.append('Final attempt used another upstream revision: '+start['id'])
                    input_manifest=DOC/provenance['manifest']
                    if digest(input_manifest)!=provenance['sha256']:raise RuntimeError('Run identity hash mismatch')
                    inputs=json.loads(input_manifest.read_text(encoding='utf-8'))
                    keys={k.replace('\\','/'):v for k,v in inputs['existing_json_inputs'].items()}
                    key='docs/validation/ten-new-project-adversarial-pass/'+name+'/'+spec.name
                    if keys.get(key)!=expected_spec:errors.append('Recorded final spec identity differs: '+case_name)
                    if finish.get('category')!='passed' or finish.get('cleanup_errors') or 'launched' not in events:
                        errors.append('Final attempt failed or was not launched: '+start['id'])
                    qualified.append(start['id'])
                if len(qualified)!=10:errors.append('Ten frozen attempt identities missing: '+artifact+'/'+case_name)
                ordinary+=len(matches)
                try:
                    group,members=repetition_group(attempts,positions,name,case['name'],qualified)
                    if not belongs_to_campaign(attempts[group],run,native['run_attempt']):
                        raise RuntimeError('Repetition group belongs to another campaign or attempt')
                except RuntimeError as error:
                    errors.append(artifact+'/'+case_name+': '+str(error));members=set()
                counted=[sid for sid in state_ids if sid in members and
                         attempts.get(sid,{}).get('started',{}).get('label')==case_name+'-state-probe']
                expected_files={k:hashlib.sha256(v.encode('utf-8')).hexdigest()
                                for k,v in case.get('expected_files',{}).items()}
                for state in states:
                    if state['attempt_id'] not in counted:continue
                    events=attempts[state['attempt_id']]
                    provenance=events.get('identified',{}).get('identity',{})
                    if (provenance.get('runner_sha256')!=identity['binary_sha256'] or
                        not belongs_to_campaign(events,run,native['run_attempt']) or
                        provenance.get('target_revision')!=project['source_pin'] or
                        events.get('finished',{}).get('category')!='passed' or
                        events.get('finished',{}).get('cleanup_errors') or 'launched' not in events):
                        errors.append('Final saved-state execution identity failed: '+state['attempt_id'])
                    input_manifest=DOC/provenance['manifest']
                    if digest(input_manifest)!=provenance['sha256']:raise RuntimeError('State identity hash mismatch')
                    inputs=json.loads(input_manifest.read_text(encoding='utf-8'))
                    if inputs['contracts'].get(spec.name)!=expected_spec:
                        errors.append('Final saved-state spec identity differs: '+state['attempt_id'])
                    observed=state['observed']
                    if (observed.get('files')!=expected_files or
                        set(observed.get('absent',[]))!=set(case.get('absent_paths',[])) or
                        set(observed.get('directories',[]))!=set(case.get('expected_directories',[])) or
                        set(observed.get('empty_directories',[]))!=set(case.get('empty_directories',[]))):
                        errors.append('Independent declared state differs: '+artifact+'/'+case_name)
                    if case.get('exact_tree'):
                        expected_entries=set(case.get('expected_files',{}))|set(case.get('expected_directories',[]))
                        for entry in list(expected_entries):
                            expected_entries.update(p.as_posix() for p in Path(entry).parents if p!=Path('.'))
                        if observed.get('entries')!=sorted(expected_entries):
                            errors.append('Independent complete tree differs: '+artifact+'/'+case_name)
                # Parent/child ledger boundaries exclude initial, rerecord and
                # restoration probes; configured completion counts cannot fill
                # a missing final execution.
                if len(counted)!=10:errors.append('Ten distinct final-group state probes missing: '+artifact+'/'+case_name)
                state_count+=len(counted)
            controls=[]
            for path in folder.glob('*-control.json'):
                control=json.loads(path.read_text(encoding='utf-8'))
                if not control.get('restored') or not control.get('contracts_unchanged'):
                    errors.append('Unrestored source fault: '+str(path));continue
                # Bind restoration to actual successful executions, including
                # the separate saved-state probe, rather than its summary flag.
                for key in ['recovery_id','state_recovery_id']:
                    events=attempts.get(control.get(key),{})
                    provenance=events.get('identified',{}).get('identity',{})
                    if (events.get('started',{}).get('project')!=name or
                        not belongs_to_campaign(events,run,native['run_attempt']) or
                        provenance.get('runner_sha256')!=identity['binary_sha256'] or
                        provenance.get('target_revision')!=project['source_pin'] or
                        events.get('finished',{}).get('category')!='passed' or
                        events.get('finished',{}).get('cleanup_errors') or 'launched' not in events):
                        errors.append('Source restoration execution missing or mismatched: '+artifact+'/'+control['name']+'/'+key)
                if control.get('state_recovery_id') not in state_ids:
                    errors.append('Source restoration saved-state evidence missing: '+artifact+'/'+control['name'])
                controls.append(control)
            if len({c['name'] for c in controls})<2:errors.append('Two distinct real source faults missing: '+artifact)
            if not any(c.get('state_oracle_detected') for c in controls):errors.append('Saved-state false-green control missing: '+artifact)
            fault_total+=len(controls);state_fault_total+=sum(bool(c.get('state_oracle_detected')) for c in controls)
            distinct_faults.update((name,c['name']) for c in controls)
            distinct_state_faults.update((name,c['name']) for c in controls if c.get('state_oracle_detected'))
            pairs.append(dict(project=name,host=host,ordinary_repetitions=ordinary,
                              separate_final_state_probes=state_count,runner_sha256=native['runner_sha256'],
                              actual_host=native['actual_host'],source_fault_controls=len(controls),owned_application_removed=True))
    linux_runs=sum(p['ordinary_repetitions'] for p in pairs if p['host']=='linux')
    if linux_runs<1000:errors.append('Fewer than 1,000 primary Linux final repetitions')
    if len(distinct_faults)<20:errors.append('Fewer than twenty distinct real target controls')
    return dict(complete=not errors,errors=errors,source=source,run=run,
                distinct_scenarios=corpus['distinct_scenarios'],project_host_pairs=pairs,
                ordinary_final_repetitions=sum(p['ordinary_repetitions'] for p in pairs),
                linux_final_repetitions=linux_runs,source_fault_controls_across_hosts=fault_total,
                distinct_target_fault_controls=len(distinct_faults),
                distinct_saved_state_controls=len(distinct_state_faults),
                state_corruption_controls_across_hosts=state_fault_total,
                full_product_100_project_launch_credit=0,
                limits='Scoped deterministic terminal/state evidence; no exhaustive user coverage, novice study or commercial-readiness claim')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    args=parser.parse_args();result=audit(args.run)
    print(json.dumps(result,indent=2))
    if not result['complete']:raise SystemExit('Final audit rejected incomplete or inconsistent evidence')


if __name__=='__main__':main()
