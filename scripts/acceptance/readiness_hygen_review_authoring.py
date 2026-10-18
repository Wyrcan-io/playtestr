"""Verify actual native public exports and full suites before curating a freeze."""
import argparse
import base64
import copy
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import plan_hash, rows
from readiness_hygen_verify_first_use import require
from readiness_new_control_matrix import packet_file, read_json as load


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(), 'invalid native authoring run')
    run = RAW / 'native' / args.run
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and len(metadata['jobs']) == 2 and all(j['conclusion'] == 'success' for j in metadata['jobs']),
            'complete successful two-host authoring required')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    candidate = load(docs.parent / 'provisional-candidate-freeze.json')
    source_review = load(docs / 'source-review.json')
    profiles = []
    for artifact, host, arch, suffix in [('Linux', 'linux', 'amd64', ''), ('macOS', 'darwin', 'arm64', 'native-profiles/macos')]:
        packet = run / ('playtestr-' + artifact)
        target = packet / 'hygen'
        package = target / 'contracts'
        frozen_path = target / 'reviewed-contract-freeze.json'
        frozen = load(frozen_path)
        runtime = load(target / 'retained-source/runtime.json')
        ledger = object.__new__(Campaign)
        ledger.raw = packet
        attempts = ledger.attempts()
        cell = next(r for r in candidate['cells'] if r['host'] == host and r['architecture'] == arch)
        installed = load(packet / 'private-install/provisional-v1' / (host + '-' + arch) / 'installation.json')
        require(frozen['runner_sha256'] == installed['binary_sha256'] == cell['binary_sha256']
                and frozen['provisional_archive_sha256'] == installed['archive_sha256'] == cell['archive_sha256']
                and frozen['normal_scenarios'] == 8 and frozen['edge_scenarios'] == 12
                and len(frozen['contracts']) == 20, 'wrong native candidate/scenario scope')
        require(frozen['target_build_sha256'] == sha256(target / 'retained-source/build.json'), 'different actual target build')

        def witness(identity):
            event = attempts[identity]
            finished = event['finished']
            require('launched' in event and event['started']['expected_exit'] == 0
                    and finished['category'] == 'passed' and finished['exit_code'] == 0
                    and finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'],
                    'actual command outcome/cleanup differs')
            reference = event['identified']['identity']
            manifest = packet_file(packet, reference['manifest'], 1024**2)
            require(sha256(manifest) == reference['sha256'], 'prelaunch source manifest changed')
            inputs = load(manifest)
            require(inputs['runtime_executables']['node'] == runtime['node_sha256'], 'actual Node interpreter differs')
            for name, digest in source_review['reviewed_inputs'].items():
                if name.startswith('dist/') and name.endswith('.js'):
                    require(inputs['files']['artifacts/runner-readiness-ten-project-pass/active/hygen/src/' + name] == digest,
                            'actual interpreted target source changed')
            require(inputs['files'][installed['binary']] == cell['binary_sha256'], 'actual native runner changed')
            console = packet / event['started']['project'] / identity / 'console.log'
            require(sha256(console) == finished['console_sha256'], 'actual command console changed')
            return inputs['files']

        def passed_report(report):
            require(report['runner_version'] == candidate['version'], 'wrong report candidate version')
            for result in report['results']:
                require(result['status'] == 'passed' and result['cleanup']['confirmed_exited']
                        and result['workspace']['cleaned'], 'result/workspace cleanup unconfirmed')
                for step in result['steps']:
                    require(step['status'] == 'passed', 'ordinary public step not passed')
                    if 'state' in step:
                        require(step['state']['invocation_id'] == result['invocation_id']
                                and step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')

        for name, digest in frozen['all_package_inputs'].items():
            require(sha256(packet_file(package, name, 1024**2)) == digest, 'frozen payload changed')
        require({p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
                == set(frozen['all_package_inputs']), 'missing or extra native package payload')
        for row in rows():
            approval_path = target / 'approved' / (row['id'] + '.json')
            approval = load(approval_path)
            require(approval['plan_sha256'] == plan_hash(row), 'actual approved plan differs')
            bound = [r for r in frozen['approvals'] if r['id'] == row['id']]
            require(len(bound) == 1 and bound[0]['approval_sha256'] == sha256(approval_path)
                    and bound[0]['plan_sha256'] == plan_hash(row), 'frozen approval identity differs')
            exported_path = packet_file(packet, approval['spec'].removeprefix('artifacts/runner-readiness-ten-project-pass/'), 1024**2)
            require(sha256(exported_path) == approval['spec_sha256'], 'actual public export changed')
            original = load(exported_path)
            contract_path = package / (row['id'] + '.json')
            contract = load(contract_path)
            require(sha256(contract_path) == frozen['contracts'][row['id'] + '.json']
                    and contract['command'] == ['hygen', 'work', 'new', *row['args']], 'wrong executed contract/command')
            actions = copy.deepcopy(contract['steps'])
            for step in actions:
                if 'snapshot' in step:
                    require(step['snapshot'] == row['id'] + '-prompt.rows.json', 'unreviewed snapshot relocation')
                    step['snapshot'] = 'prompt.rows.json'
            require(actions == original['steps'], 'relocation changed public behavior or expectations')
            states = [s['state'] for s in contract['steps'] if 'state' in s]
            actual_files = {s['path']: base64.b64decode(s['bytes_base64']) for s in states if s['kind'] == 'file'}
            actual_entries = {s['path']: s['entries'] for s in states if s['kind'] == 'entries'}
            require(actual_files == row['expected']
                    and {s['path'] for s in states if s['kind'] == 'absent'} == set(row['missing'])
                    and {n: sorted(v) for n, v in actual_entries.items()} == row['entry_sets']
                    and all(len(v) == len(set(v)) for v in actual_entries.values()), 'independent saved-state oracle differs')
            for name, data in row['files'].items():
                require((package / 'fixtures' / row['id'] / name).read_bytes() == data, 'native fixture differs')
            selected = load(package / 'snapshots' / (row['id'] + '-prompt.rows.json'))
            require(selected['snapshot_version'] == 1 and selected['first_row'] == selected['last_row'] == 1
                    and selected['text'].count(row['actions'][0].removeprefix('/expect ')) == 1,
                    'unreviewed native selected prompt baseline')
            for identity in [approval['capture_attempt'], approval['ordinary_attempt']]:
                files = witness(identity)
                if identity == approval['ordinary_attempt']:
                    reference = 'artifacts/runner-readiness-ten-project-pass/' + exported_path.relative_to(packet).as_posix()
                    require(files[reference] == approval['spec_sha256'], 'actual individual ordinary contract not bound')
                    baseline = exported_path.parent / 'snapshots/prompt.rows.json'
                    reference = 'artifacts/runner-readiness-ten-project-pass/' + baseline.relative_to(packet).as_posix()
                    require(files[reference] == sha256(baseline), 'actual individual snapshot not bound')
                for name, data in row['files'].items():
                    reference = 'artifacts/runner-readiness-ten-project-pass/' + (exported_path.parent / 'fixture' / name).relative_to(packet).as_posix()
                    require(files[reference] == sha256(exported_path.parent / 'fixture' / name), 'actual fixture not bound')
            ordinary = exported_path.parent / 'ordinary-result.json'
            require(sha256(ordinary) == approval['report_sha256'], 'individual ordinary result changed')
            passed_report(load(ordinary))
        full = [p for p in (target / 'suites').glob('*/results.json') if sha256(p) == frozen['ordinary_report_sha256']]
        require(len(full) == 1, 'full ordinary suite report missing or ambiguous')
        report = load(full[0])
        require(report['summary'] == dict(total=20, passed=20, failed=0, cancelled=0, not_run=0)
                and {Path(r['spec_path']).name for r in report['results']} == set(frozen['contracts']), 'wrong full suite denominator')
        passed_report(report)
        parent = attempts[frozen['ordinary_parent']]
        require(parent['finished']['category'] == 'passed' and parent['finished']['exit_code'] == 0, 'full suite parent failed')
        full_calls = [identity for identity, event in attempts.items() if event['started']['label'] == 'public-recorded-suite']
        require(len(full_calls) == 1, 'ambiguous full public command')
        files = witness(full_calls[0])
        for name, digest in frozen['all_package_inputs'].items():
            require(files['artifacts/runner-readiness-ten-project-pass/hygen/contracts/' + name] == digest,
                    'actual full suite package inputs not bound')
        retained = target / 'retained-source'
        removed = load(retained / 'removed.json')
        require(removed['removed'] and removed['source_archive_sha256'] == source_review['archive_sha256']
                and load(retained / 'removal-prepared.json')['runtime_processes_verified'], 'source/runtime cleanup unconfirmed')
        index = load(retained / 'verified-index.json')
        for name in index['selected_restore']:
            require(sha256(retained / 'selected-restore' / name) == index['files'][name]['sha256'], 'selected restore changed')
        profiles.append(dict(host=host, arch=arch, suffix=suffix, package=package, frozen_path=frozen_path,
                             frozen=frozen, report_sha256=sha256(full[0]), cleanup_sha256=sha256(retained / 'removed.json')))
    # Publish nothing until all observed native evidence has passed independent checks.
    for profile in profiles:
        destination = docs / profile['suffix']
        destination.mkdir(parents=True, exist_ok=True)
        require(not (destination / 'contracts').exists() and not (destination / 'reviewed-contract-freeze.json').exists(),
                'refuse to overwrite a prior reviewed native freeze')
    cells = []
    for profile in profiles:
        destination = docs / profile['suffix']
        shutil.copytree(profile['package'], destination / 'contracts')
        shutil.copyfile(profile['frozen_path'], destination / 'reviewed-contract-freeze.json')
        cells.append(dict(host=profile['host'], architecture=profile['arch'],
                          freeze_sha256=sha256(destination / 'reviewed-contract-freeze.json'),
                          report_sha256=profile['report_sha256'], cleanup_sha256=profile['cleanup_sha256']))
    immutable_json(docs / 'native-authoring-review.json', dict(run=args.run, cells=cells,
                   unique_scenarios=20, normal=8, edge=12, source_faults_selected=False,
                   candidate_version=candidate['version'], final_archive_credit=0))
    print('Independently reviewed and curated both native twenty-case Hygen freezes before source fault selection.')


if __name__ == '__main__':
    main()
