"""Independently audit twelve native final Hygen batches and actual source faults."""
import argparse
import base64
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import entry_sets
from readiness_hygen_verify_first_use import require
from readiness_new_control_matrix import packet_file, read_json as load


def verify_cell(run_id, artifact, series):
    original=False
    run = RAW / 'native' / run_id
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in metadata['jobs']),
            'native qualification incomplete or failed')
    packet = run / ('final-hygen-' + artifact)
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    profile = docs / 'native-profiles/macos' if artifact == 'macOS' else docs
    frozen = load(profile / 'reviewed-contract-freeze.json')
    candidate = load(docs.parent / 'migration-candidate-freeze.json')
    host, arch = ('darwin', 'arm64') if artifact == 'macOS' else ('linux', 'amd64')
    cell = next(row for row in candidate['cells'] if row['host'] == host and row['architecture'] == arch)
    installed = load(packet / 'private-install/migration-v2' / (host + '-' + arch) / 'installation.json')
    require(installed['archive_sha256'] == cell['archive_sha256'] and installed['binary_sha256'] == cell['binary_sha256'],
            'actual installed archive identity differs')
    source_review = load(docs / 'source-review.json')
    source_faults = {r['id']: r for r in load(docs / 'source-fault-review.json')['faults']}
    target = packet / 'hygen'
    package = target / 'host-contracts'
    retained = target / 'retained-source'
    runtime = load(retained / 'runtime.json')
    build = load(retained / 'build.json')
    require(build['pin'] == source_review['pin'] and build['tracked_upstream_dist']
            and build['scripts_disabled'] and not build['typescript_rebuilt'], 'actual source/build policy differs')
    for name, digest in frozen['all_package_inputs'].items():
        require(sha256(packet_file(package, name, 1024**2)) == digest, 'frozen native payload differs')
    ledger = object.__new__(Campaign)
    ledger.raw = packet
    attempts = ledger.attempts()

    def witness(identity, expected=0, source_override=None, runner_required=True):
        event = attempts[identity]
        if series=='v2':require(all(r['phase']=='final-archive' for r in event.values()),'actual final phase differs')
        finished = event['finished']
        require('launched' in event and event['started']['expected_exit'] == expected
                and finished['category'] == 'passed' and finished['exit_code'] == expected
                and finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'],
                'actual command outcome/cleanup differs')
        reference = event['identified']['identity']
        manifest = packet_file(packet, reference['manifest'], 1024**2)
        require(sha256(manifest) == reference['sha256'], 'prelaunch manifest changed')
        from readiness_identity_manifest import load_manifest
        bound = load_manifest(packet,reference)
        files = bound['files']
        require(bound['runtime_executables']['node'] == runtime['node_sha256'], 'actual Node executable differs')
        for name, digest in source_review['reviewed_inputs'].items():
            if name.startswith('dist/') and name.endswith('.js') or name == 'package.json':
                actual_digest = source_override[1] if source_override and name == source_override[0] else digest
                require(files['artifacts/runner-readiness-ten-project-pass/active/hygen/src/' + name] == actual_digest,
                        'actual interpreted source differs')
        if runner_required:
            require(files[installed['binary']] == cell['binary_sha256'], 'actual Playtestr archive binary differs')
        console = packet / event['started']['project'] / identity / 'console.log'
        require(sha256(console) == finished['console_sha256'], 'actual output changed')
        return files

    def result_ok(result, status):
        require(result['status'] == status and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'], 'public result or cleanup differs')
        for step in result['steps']:
            if 'state' in step:
                require(step['state']['invocation_id'] == result['invocation_id']
                        and step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')

    final_root=target/'final-series';intent=load(final_root/'intent.json')
    declaration_file='final-series-declaration-v2.json' if series=='v2' else 'final-series-declaration.json'
    declaration=load(docs/declaration_file)
    if series=='v2':require(intent['declaration_file']==declaration_file,'final series declaration differs')
    require(intent['declaration_sha256']==sha256(docs/declaration_file)
            and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256']
            and intent['target_build_sha256']==sha256(retained/'build.json') and intent['target_pin']==build['pin']
            and intent['canonical_package_inputs']==frozen['all_package_inputs'], 'final intent changed')
    require(declaration['candidate_freeze_sha256']==sha256(docs.parent/'migration-candidate-freeze.json'), 'declared final archive changed')
    all_rows=[];invocations=set();commands=set();modules=None;reports=[]
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
                for step in before['steps']:
                    if set(step)=={'text'} and len(step['text'])>size:
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
            actual_modules={n:h for n,h in bound.items() if '/active/hygen/src/node_modules/' in n}
            require(bool(actual_modules),'production dependency inputs missing')
            if modules is None:modules=actual_modules
            else:require(actual_modules==modules,'production dependencies changed across final batches')
            all_rows.append(observed);reports.append(report_path)
        require(summary['records']==all_rows[-20:],'batch summary does not match actual observations')
    require(len(all_rows)==240 and len(invocations)==240,'final native denominator differs')
    summaries = list((target / 'faults').glob('*/summary.json'))
    require(len(summaries) == 1, 'ambiguous source-fault batch')
    summary_path = summaries[0]
    summary = load(summary_path)
    require(summary['runner_sha256'] == cell['binary_sha256'] and summary['provisional_archive_sha256'] == cell['archive_sha256']
            and summary['interpreter_sha256'] == runtime['node_sha256']
            and {r['id'] for r in summary['faults']} == {'F01', 'F02', 'F03'} and len(summary['faults']) == 3,
            'wrong real source-fault scope')
    selected = load(summary_path.parent / 'selected-faults.json')
    require(selected['frozen_contract_sha256'] == sha256(docs / 'reviewed-contract-freeze.json')
            and selected['native_freeze_sha256'] == sha256(profile / 'reviewed-contract-freeze.json')
            and selected['original_heldout'] == original and not selected['local_exploratory'], 'wrong heldout/freeze binding')
    for fault in summary['faults']:
        review = source_faults[fault['id']]
        require(fault['restored_exact'] and fault['held_out'] == bool(original and fault['id'] == 'F03')
                and all(fault[k] == review[k] for k in ['path', 'original_source_sha256', 'mutated_source_sha256']),
                'actual source fault/restoration differs from selection')
        for phase, expected, digest in [('baseline', 0, fault['original_source_sha256']),
                                        ('mutated', 1, fault['mutated_source_sha256']),
                                        ('restored', 0, fault['original_source_sha256'])]:
            files = witness(fault[{'baseline': 'baseline_attempt', 'mutated': 'mutation_attempt', 'restored': 'restored_attempt'}[phase]],
                            expected, (fault['path'], digest))
            require({n: d for n, d in files.items() if '/active/hygen/src/node_modules/' in n} == modules,
                    'production module bytes changed during mutation')
            for name, contract_digest in frozen['all_package_inputs'].items():
                if name == fault['spec'] or name.startswith('fixtures/N01/') or name == 'snapshots/N01-prompt.rows.json':
                    require(files['artifacts/runner-readiness-ten-project-pass/hygen/host-contracts/' + name] == contract_digest,
                            'actual fault contract/fixture/snapshot changed')
            value = load(summary_path.parent / (fault['id'] + '-' + phase + '.json'))
            require(value['runner_version'] == candidate['version'], 'fault report uses another runner')
            outcome = value['results'][0]
            result_ok(outcome, 'failed' if expected else 'passed')
            if phase == 'mutated':
                require(outcome['failure']['category'] == fault['category'], 'wrong actual source-fault rejection')
                if fault['id'] == 'F02':
                    require(outcome['target']['exited'] and outcome['target']['exit_code'] == 7, 'actual OS exit7 missing')
                else:
                    failed = next(i for i, step in enumerate(outcome['steps']) if step['status'] == 'failed')
                    prior = outcome['steps'][:failed]
                    require(all(s['status'] == 'passed' for s in prior)
                            and {'snapshot', 'exit'} <= {s['action'] for s in prior}
                            and outcome['target']['exited'] and outcome['target']['exit_code'] == 0,
                            'false-green control lacks earlier passing screen/exit')
                    state = outcome['steps'][failed]['state']
                    require((state['kind'], state['path']) == (('entries', 'generated') if fault['id'] == 'F03' else ('file', 'generated/result.txt')),
                            'wrong same-execution state checkpoint')
                    if fault['id'] == 'F03':
                        require(sum(s.get('state', {}).get('kind') == 'file' for s in prior) == 5,
                                'extra-file fault lacks passing exact generated/preserved bytes')
                screen = packet_file(packet, outcome['evidence']['screen_path'].removeprefix('artifacts/runner-readiness-ten-project-pass/'), 1024**2)
                require('added: generated/result.txt' in screen.read_text(encoding='utf-8-sig'), 'useful final failure frame missing')
        for phase, digest in [('mutation_validation', fault['mutated_source_sha256']), ('restored_validation', fault['original_source_sha256'])]:
            validation = fault[phase]
            require(validation['source_sha256'] == digest and validation['interpreter_sha256'] == runtime['node_sha256'],
                    'source validation identity changed')
            for key in ['syntax_attempt', 'help_attempt']:
                witness(validation[key], source_override=(fault['path'], digest), runner_required=False)

    removed = load(retained / 'removed.json')
    prepared = load(retained / 'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path'] == 'active/hygen'
            and removed['source_archive_sha256'] == source_review['archive_sha256']
            and prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'], 'source/runtime cleanup unconfirmed')
    source_index = load(retained / 'verified-index.json')
    for name in source_index['selected_restore']:
        require(sha256(retained / 'selected-restore' / name) == source_index['files'][name]['sha256'], 'selected source restore changed')
    return dict(host='linux' if artifact=='Linux' else 'macos',run=run_id,scenarios=20,ordinary_executions=240,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],
        source_fault_summary_sha256=sha256(summary_path),cleanup_receipt_sha256=sha256(retained/'removed.json'),
        observations=all_rows,calibration_executions=9,final_archive_credit=0,
        scope='Independent exact-archive ordinary/fault/restoration/cleanup audit; overall final controls and matrix remain separate gates.',
        metadata_qualifier=('Every actual command has phase=final-archive and catalog references are fully resolved and hash-verified.' if series=='v2' else 'This first final series used the historical common event envelope phase=development. The prelaunch final-series declaration/intent and every final-batch label bind all 240 actual attempts to the final archive schedule. No earlier development/diagnostic attempt is credited.'))



def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','macos'],required=True)
    parser.add_argument('--series',choices=['v1','v2'],default='v1');args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native final run')
    receipt=verify_cell(args.run,'Linux' if args.host=='linux' else 'macOS',args.series)
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/hygen'/(('final-v2-verified-' if args.series=='v2' else 'final-verified-')+args.host+'.json'),receipt)
    print('Verified final Hygen native 240 ordinary outcomes, three actual faults/recovery and cleanup:',args.host)


if __name__=='__main__':main()
