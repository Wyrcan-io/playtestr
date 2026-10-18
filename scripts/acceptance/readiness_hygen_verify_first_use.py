"""Independently verify actual native exact-archive prompt/file first use."""
import argparse
import base64
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import fixture_files
from readiness_new_control_matrix import packet_file, read_json as load


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(), 'invalid native run')
    run = RAW / 'native' / args.run
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and len(metadata['jobs']) == 2 and all(j['conclusion'] == 'success' for j in metadata['jobs']),
            'missing two successful native first-use jobs')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    frozen = load(docs / 'provisional-candidate-freeze.json')
    review = load(docs / 'hygen/source-review.json')
    expected = {**fixture_files(), 'generated/hello.txt': b'Hello, reviewed!\n'}
    expected_entries = {'.': {'.hygen.js', '_templates', 'sentinel.bin', 'generated'},
                        'generated': {'hello.txt'}, '_templates': {'welcome'},
                        '_templates/welcome': {'new'}, '_templates/welcome/new': {'prompt.js', 'hello.ejs.t'}}
    cells = []
    for artifact, host, arch in [('Linux', 'linux', 'amd64'), ('macOS', 'darwin', 'arm64')]:
        packet = run / ('playtestr-' + artifact)
        ledger = object.__new__(Campaign)
        ledger.raw = packet
        attempts = ledger.attempts()
        cell = next(row for row in frozen['cells'] if row['host'] == host and row['architecture'] == arch)
        installed = load(packet / 'private-install/provisional-v1' / (host + '-' + arch) / 'installation.json')
        require(installed['archive_sha256'] == cell['archive_sha256']
                and installed['binary_sha256'] == cell['binary_sha256']
                and installed['version'] == frozen['version'], 'different actual archive installation')
        retained = packet / 'hygen/retained-source'
        index = load(retained / 'verified-index.json')
        build = load(retained / 'build.json')
        runtime = load(retained / 'runtime.json')
        require(index['archive_sha256'] == review['archive_sha256'] and build['pin'] == review['pin']
                and build['tracked_upstream_dist'] and not build['typescript_rebuilt']
                and build['scripts_disabled'], 'wrong target pin, build tree or hooks policy')
        journeys = list((packet / 'hygen/first-use').glob('*/journey.json'))
        require(len(journeys) == 1, 'ambiguous successful first-use journey')
        path = journeys[0]
        journey = load(path)
        package = path.parent
        require(journey['shell_invocations'] == 3 and journey['recorder_controls'] == 20
                and not journey['handwritten_playtestr_json']
                and journey['runner_sha256'] == cell['binary_sha256']
                and journey['provisional_archive_sha256'] == cell['archive_sha256']
                and journey['target_build_sha256'] == sha256(retained / 'build.json'), 'wrong route budget/identity')

        def witness(identity, first_use=False):
            event = attempts[identity]
            finished = event['finished']
            require('launched' in event and event['started']['expected_exit'] == 0
                    and finished['category'] == 'passed' and finished['exit_code'] == 0
                    and finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'],
                    'command outcome or cleanup unconfirmed')
            ref = event['identified']['identity']
            manifest = packet_file(packet, ref['manifest'], 1024**2)
            require(sha256(manifest) == ref['sha256'], 'changed prelaunch identity')
            identity_value = load(manifest)
            files = identity_value['files']
            for name, digest in review['reviewed_inputs'].items():
                if name.startswith('dist/') and name.endswith('.js') or name.startswith('src/templates/'):
                    require(files['artifacts/runner-readiness-ten-project-pass/active/hygen/src/' + name] == digest,
                            'actual executed target source differs')
            require(identity_value['runtime_executables']['node'] == runtime['node_sha256'],
                    'actual native Node bytes differ')
            console = packet / event['started']['project'] / identity / 'console.log'
            require(sha256(console) == finished['console_sha256'], 'actual command output changed')
            output = console.read_text(encoding='utf-8-sig')
            if first_use:
                require(files[installed['binary']] == cell['binary_sha256'], 'actual first-use binary changed')
            return files, output

        for identity in journey['attempts']:
            files, output = witness(identity, first_use=True)
            if identity == journey['capture_attempt']:
                require('Exported ' in output and 'unresolved control failures' not in output,
                        'public review/replay/export refused')
            if identity in {journey['capture_attempt'], journey['ordinary_attempt']}:
                for name in fixture_files():
                    key = 'artifacts/runner-readiness-ten-project-pass/' + (package / 'fixture' / name).relative_to(packet).as_posix()
                    require(files[key] == sha256(package / 'fixture' / name), 'actual fixture inputs not bound')
        witness(build['help_attempt'])
        spec = package / 'spec.json'
        contract = load(spec)
        require(sha256(spec) == journey['spec_sha256'] and contract['command'] == ['hygen', 'welcome', 'new'],
                'wrong exported spec or target invocation')
        actual = {s['state']['path']: base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
                  if s.get('state', {}).get('kind') == 'file'}
        require(actual == expected, 'independent generated/preserved file oracle differs')
        entries = {s['state']['path']: s['state']['entries'] for s in contract['steps']
                   if s.get('state', {}).get('kind') == 'entries'}
        require(set(entries) == set(expected_entries)
                and all(set(values) == expected_entries[name] and len(values) == len(set(values))
                        for name, values in entries.items()), 'public full directory sets differ')
        for name, value in fixture_files().items():
            require((package / 'fixture' / name).read_bytes() == value, 'retained input fixture differs')
        snapshot = next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        selected = load(package / 'snapshots' / snapshot)
        require(selected['snapshot_version'] == 1 and selected['first_row'] == selected['last_row'] == 1
                and selected['text'].count('Message for file?') == 1 and selected['text'].count('reviewed') == 1,
                'wrong selected live prompt frame')
        report = load(package / 'ordinary-results.json')
        require(report['runner_version'] == frozen['version']
                and report['summary'] == dict(total=1, passed=1, failed=0, cancelled=0, not_run=0),
                'wrong exact-archive ordinary result')
        result = report['results'][0]
        require(result['status'] == 'passed' and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'], 'ordinary target/workspace cleanup unconfirmed')
        for step in result['steps']:
            require(step['status'] == 'passed', 'ordinary step incomplete')
            if 'state' in step:
                require(step['state']['invocation_id'] == result['invocation_id']
                        and step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state proof')
        removed = load(retained / 'removed.json')
        require(removed['removed'] and removed['owned_relative_path'] == 'active/hygen'
                and removed['source_archive_sha256'] == review['archive_sha256']
                and load(retained / 'removal-prepared.json')['runtime_processes_verified'],
                'source/runtime cleanup unconfirmed')
        for name in index['selected_restore']:
            require(sha256(retained / 'selected-restore' / name) == index['files'][name]['sha256'],
                    'selected source restore changed')
        cells.append(dict(host=host, architecture=arch, runner_sha256=cell['binary_sha256'],
                          archive_sha256=cell['archive_sha256'], journey_sha256=sha256(path),
                          spec_sha256=sha256(spec), cleanup_sha256=sha256(retained / 'removed.json')))
    immutable_json(docs / 'hygen' / ('first-use-native-' + args.run + '.json'),
                   dict(run=args.run, cells=cells, shell_invocations=3, recorder_controls=20,
                        human_usability='unmeasured', development_admission=False, final_archive_credit=0))
    print('Verified actual exact-archive Hygen first use, generated/preserved bytes and cleanup on Linux/macOS.')


if __name__ == '__main__':
    main()
