"""Inspect actual native suite/fault/maintenance identities; no summary-only credit."""
import argparse
import base64
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import entry_sets
from readiness_hygen_verify_first_use import require
from readiness_new_control_matrix import packet_file, read_json as load


def verify_cell(run_id, artifact, original):
    run = RAW / 'native' / run_id
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in metadata['jobs']),
            'native qualification incomplete or failed')
    packet = run / ('playtestr-' + artifact)
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    profile = docs / 'native-profiles/macos' if artifact == 'macOS' else docs
    frozen = load(profile / 'reviewed-contract-freeze.json')
    candidate = load(docs.parent / 'provisional-candidate-freeze.json')
    host, arch = ('darwin', 'arm64') if artifact == 'macOS' else ('linux', 'amd64')
    cell = next(row for row in candidate['cells'] if row['host'] == host and row['architecture'] == arch)
    installed = load(packet / 'private-install/provisional-v1' / (host + '-' + arch) / 'installation.json')
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
    require(load(target / 'native-profile.json')['freeze_sha256'] == sha256(profile / 'reviewed-contract-freeze.json'),
            'actual native profile changed')
    for name, digest in frozen['all_package_inputs'].items():
        require(sha256(packet_file(package, name, 1024**2)) == digest, 'frozen native payload differs')
    ledger = object.__new__(Campaign)
    ledger.raw = packet
    attempts = ledger.attempts()

    def witness(identity, expected=0, source_override=None, runner_required=True):
        event = attempts[identity]
        finished = event['finished']
        require('launched' in event and event['started']['expected_exit'] == expected
                and finished['category'] == 'passed' and finished['exit_code'] == expected
                and finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'],
                'actual command outcome/cleanup differs')
        reference = event['identified']['identity']
        manifest = packet_file(packet, reference['manifest'], 1024**2)
        require(sha256(manifest) == reference['sha256'], 'prelaunch manifest changed')
        bound = load(manifest)
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

    reports = list((target / 'suites').glob('*/results.json'))
    require(len(reports) == 1, 'ambiguous ordinary suite')
    report = load(reports[0])
    require(report['runner_version'] == candidate['version']
            and report['summary'] == dict(total=20, passed=20, failed=0, cancelled=0, not_run=0)
            and {Path(r['spec_path']).name for r in report['results']} == set(frozen['contracts']), 'wrong native suite denominator')
    for result in report['results']:
        result_ok(result, 'passed')
    suites = [identity for identity, event in attempts.items() if event['started']['label'] == 'public-recorded-suite']
    require(len(suites) == 1, 'actual full suite command ambiguous')
    files = witness(suites[0])
    for name, digest in frozen['all_package_inputs'].items():
        require(files['artifacts/runner-readiness-ten-project-pass/hygen/host-contracts/' + name] == digest,
                'actual full suite inputs not bound')
    modules = {name: digest for name, digest in files.items() if '/active/hygen/src/node_modules/' in name}
    require(bool(modules), 'actual production modules not captured')
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

    journeys = list(target.glob('maintenance*/journey.json'))
    require(len(journeys) == 1, 'ambiguous maintenance journey')
    journey_path = journeys[0]
    journey = load(journey_path)
    require(len(journey['attempts']) == 13 and journey['maintained_spec_sha256'] == journey['relocated_spec_sha256']
            and journey['runner_sha256'] == cell['binary_sha256'] and journey['provisional_archive_sha256'] == cell['archive_sha256'],
            'maintenance scope/identity differs')
    for attempt in journey['attempts']:
        witness(attempt['id'], 1 if attempt['label'].startswith('intended-') else 0)
    for label in ['intended-file-change', 'selected-file-replay', 'intended-viewport-change',
                  'selected-screen-update', 'selected-screen-replay', 'suffix-ordinary-replay',
                  'relocated-N01', 'relocated-E01', 'relocated-rerecorded-suffix']:
        maintained_report = load(journey_path.parent / (label + '.json'))
        red = label.startswith('intended-')
        require(maintained_report['runner_version'] == candidate['version']
                and maintained_report['summary'] == dict(total=1, passed=0 if red else 1,
                                                        failed=1 if red else 0, cancelled=0, not_run=0),
                'maintenance report denominator differs')
        maintained_result = maintained_report['results'][0]
        result_ok(maintained_result, 'failed' if red else 'passed')
        if red:
            require(maintained_result['failure']['category'] ==
                    ('state_assertion_failure' if label == 'intended-file-change' else 'snapshot_mismatch'),
                    'maintenance intended red has wrong diagnosis')
    maintained = journey_path.parent / 'package/N01.json'
    before = load(package / 'N01.json')
    updated = load(maintained)
    index = next(i for i, s in enumerate(before['steps']) if s.get('state', {}).get('path') == 'sentinel.bin')
    require(base64.b64decode(updated['steps'][index]['state']['bytes_base64']) == b'reviewed sentinel revision two\x00\r\n',
            'selected sentinel bytes differ')
    updated['steps'][index] = before['steps'][index]
    require(updated == before and sha256(maintained) == journey['maintained_spec_sha256'], 'selected state update changed unrelated steps')
    screen_review = load(journey_path.parent / 'selected-screen-review.json')
    require(screen_review['original_width'] == 100 and screen_review['updated_width'] == 28
            and screen_review['original']['text'] != screen_review['updated']['text']
            and screen_review['original']['text'].rstrip('\n').startswith(screen_review['updated']['text'].rstrip('\n')),
            'selected viewport review differs')
    screen_spec = journey_path.parent / 'package/E01.json'
    screen = load(screen_spec)
    require(sha256(screen_spec) == journey['screen_spec_sha256'] and screen['width'] == 28, 'maintained screen spec changed')
    original_screen = load(package / 'E01.json')
    screen['width'] = original_screen['width']
    wrapped = next(s for s in screen['steps'] if s.get('expect') == 'added: generated/resu\nlt.txt')
    wrapped['expect'] = 'added: generated/result.txt'
    require(screen == original_screen, 'viewport maintenance changed unrelated expectations')
    suffix = load(journey_path.parent / 'package/rerecorded-suffix.json')
    saved = {s['state']['path']: base64.b64decode(s['state']['bytes_base64']) for s in suffix['steps'] if s.get('state', {}).get('kind') == 'file'}
    expected_suffix = {s['state']['path']: base64.b64decode(s['state']['bytes_base64']) for s in before['steps']
                       if s.get('state', {}).get('kind') == 'file'}
    expected_suffix.update({'generated/result.txt': b'Hello, corrected!\n', 'sentinel.bin': b'reviewed sentinel revision two\x00\r\n'})
    suffix_entries = {s['state']['path']: s['state']['entries'] for s in suffix['steps'] if s.get('state', {}).get('kind') == 'entries'}
    require(saved == expected_suffix and {n: sorted(v) for n, v in suffix_entries.items()} == entry_sets(expected_suffix)
            and all(len(v) == len(set(v)) for v in suffix_entries.values())
            and all(s.get('text') != 'wrong' and s.get('expect') != 'wrong' for s in suffix['steps']), 'rerecorded suffix differs')
    for name in ['N01.json', 'E01.json', 'rerecorded-suffix.json']:
        require(sha256(journey_path.parent / 'package' / name) ==
                sha256(journey_path.parent / 'relocated \u96ea route' / name), 'actual relocated contract differs')
    require(sha256(journey_path.parent / 'generated-workflow.yml') == journey['generated_workflow_sha256']
            and not journey['generated_workflow_execution'], 'generated workflow identity/execution claim differs')
    removed = load(retained / 'removed.json')
    prepared = load(retained / 'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path'] == 'active/hygen'
            and removed['source_archive_sha256'] == source_review['archive_sha256']
            and prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'], 'source/runtime cleanup unconfirmed')
    source_index = load(retained / 'verified-index.json')
    for name in source_index['selected_restore']:
        require(sha256(retained / 'selected-restore' / name) == source_index['files'][name]['sha256'], 'selected source restore changed')
    return dict(host='playtestr-' + artifact, run=run_id, scenarios=20, runner_sha256=cell['binary_sha256'],
                provisional_archive_sha256=cell['archive_sha256'], report_sha256=sha256(reports[0]),
                source_fault_summary_sha256=sha256(summary_path), maintenance_sha256=sha256(journey_path),
                cleanup_receipt_sha256=sha256(retained / 'removed.json')), summary_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linux-run', required=True)
    parser.add_argument('--macos-run')
    parser.add_argument('--original-only', action='store_true')
    args = parser.parse_args()
    require(all(r.isascii() and r.isdecimal() for r in [args.linux_run, *([args.macos_run] if args.macos_run else [])]), 'invalid native run')
    require(bool(args.macos_run) != args.original_only, 'choose original Linux review or complete two-host review')
    linux, summary = verify_cell(args.linux_run, 'Linux', True)
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    if args.original_only:
        destination = docs / 'original-source-faults'
        destination.mkdir(exist_ok=False)
        for name in ['summary.json', 'selected-faults.json', 'F01.patch', 'F02.patch', 'F03.patch']:
            shutil.copyfile(summary.parent / name, destination / name)
        immutable_json(docs / 'original-fault-verification.json', dict(run=args.linux_run, cell=linux,
                       source_revision=load(docs.parent / 'provisional-candidate-freeze.json')['source_revision'],
                       original_heldout='F03 only, initial hosted Linux after committed freeze8b80490', final_archive_credit=0))
        print('Verified original Linux three source faults, F03 positive prior proofs, maintenance and checked cleanup.')
    else:
        macos, _ = verify_cell(args.macos_run, 'macOS', False)
        require(sha256(docs / 'original-source-faults/summary.json') == sha256(summary), 'original Linux fault summary changed')
        immutable_json(RAW / 'hygen/native-development-verification.json', dict(cells=[linux, macos],
                       runner_source=load(docs.parent / 'provisional-candidate-freeze.json')['source_revision'],
                       candidate_version=load(docs.parent / 'provisional-candidate-freeze.json')['version'],
                       real_faults=3, original_heldout=dict(host='Linux', run=args.linux_run, fault='F03'), final_archive_credit=0))
        print('Verified both native Hygen suites, three real source faults/restores, maintenance and cleanup.')


if __name__ == '__main__':
    main()
