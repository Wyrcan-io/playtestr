"""Independently review both native public authoring packets before fault selection."""
import argparse
import base64
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_vis_cases import rows, plan_hash
from readiness_vis_source import ARCHIVE_SHA256, PIN


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(), 'invalid native run')
    run = RAW/'native'/args.run
    metadata = load(run/'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success', 'native freeze run not successful')
    reviewed = ROOT/'docs/validation/runner-readiness-ten-project-pass/vis'
    cells = []
    linux = run/'playtestr-Linux/vis/contracts'
    for host in ['Linux', 'macOS']:
        packet = run/('playtestr-'+host)
        ledger = object.__new__(Campaign)
        ledger.raw = packet
        attempts = ledger.attempts()
        freeze = load(packet/'vis/reviewed-contract-freeze.json')
        package = packet/'vis/contracts'
        require(freeze['normal_scenarios'] == 8 and freeze['edge_scenarios'] == 12 and len(freeze['contracts']) == 20,
                'incomplete declared breadth')
        require(set(freeze['contracts']) == {r['id']+'.json' for r in rows()}, 'wrong scenario identities')
        runner = load(packet/'vis-native-runner.json')
        build = load(packet/'vis/retained-source/build.json')
        require(runner['source_revision'] == 'e7b5f29e575e44babe7fdaa2e83e55b62d318305' and
                runner['candidate_sha256'] == runner['copied_sha256'] == freeze['runner_sha256'], 'wrong frozen runner')
        require(build['pin'] == PIN and build['archive_sha256'] == ARCHIVE_SHA256, 'wrong source build')
        require(freeze['target_build_sha256'] == sha256(packet/'vis/retained-source/build.json'), 'changed build receipt')
        for name, digest in freeze['all_package_inputs'].items():
            require(sha256(package/name) == digest, 'frozen package changed')
            if name not in freeze['contracts']:
                require(sha256(package/name) == sha256(linux/name), 'native fixture or screen differs')

        def witness(identity):
            events = attempts[identity]
            require('launched' in events and events['started']['expected_exit'] == 0, 'missing successful launch')
            finished = events['finished']
            require(finished['category'] == 'passed' and finished['exit_code'] == 0 and
                    finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'], 'unconfirmed command')
            ref = events['identified']['identity']
            manifest = packet_file(packet, ref['manifest'], 1024**2)
            require(sha256(manifest) == ref['sha256'], 'changed manifest')
            console = packet_file(packet, events['started']['project']+'/'+identity+'/console.log', 4*1024**2)
            require(sha256(console) == finished['console_sha256'], 'changed console')
            return load(manifest)['files']

        def result_ok(result):
            require(result['status'] == 'passed' and result['cleanup']['confirmed_exited'] and
                    result['workspace']['cleaned'], 'scenario or cleanup not passing')
            for step in result['steps']:
                if 'state' in step:
                    require(step['state']['invocation_id'] == result['invocation_id'] and
                            step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')

        for row in rows():
            approval = load(packet/'vis/approved'/(row['id']+'.json'))
            require(approval['plan_sha256'] == plan_hash(row), 'authoring plan changed')
            relative = Path(approval['spec']).relative_to('artifacts/runner-readiness-ten-project-pass').as_posix()
            spec = packet_file(packet, relative, 1024**2)
            require(sha256(spec) == approval['spec_sha256'], 'public export changed')
            contract = load(spec)
            states = {s['state']['path']:base64.b64decode(s['state']['bytes_base64'])
                      for s in contract['steps'] if s.get('state', {}).get('kind') == 'file'}
            require(states == row['expected'], 'independent exact-byte oracle differs')
            require({s['state']['path'] for s in contract['steps'] if s.get('state', {}).get('kind') == 'absent'} == set(row['missing']),
                    'absence contract differs')
            for identity in [approval['capture_attempt'], approval['ordinary_attempt']]:
                files = witness(identity)
                require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'] == runner['copied_sha256'] and
                        files['artifacts/runner-readiness-ten-project-pass/active/vis/src/vis'] == build['binary_sha256'], 'actual binary differs')
            ordinary = spec.parent/'ordinary-result.json'
            require(sha256(ordinary) == approval['report_sha256'], 'authoring result changed')
            result_ok(load(ordinary)['results'][0])
            canonical = load(linux/(row['id']+'.json'))
            native = load(package/(row['id']+'.json'))
            if host == 'macOS':
                require(native['env']['LC_ALL'] == 'en_US.UTF-8', 'unexpected macOS locale')
                native['env']['LC_ALL'] = 'C.UTF-8'
            # Public `entries` asserts an exact set, with duplicate names rejected.
            # Independently captured enumeration order may differ; frozen bytes stay untouched.
            for comparison in [native, canonical]:
                for step in comparison['steps']:
                    if step.get('state', {}).get('kind') == 'entries':
                        names = step['state']['entries']
                        require(len(names) == len(set(names)), 'duplicate entry-set name')
                        require(set(names) == {Path(name).parts[0] for name in row['expected']}, 'unexpected directory side effect')
                        step['state']['entries'] = sorted(names)
            require(native == canonical, 'unreviewed native contract difference')
        witness(freeze['ordinary_parent'])
        reports = list((packet/'vis/suites').glob('*/results.json'))
        require(len(reports) == 1 and sha256(reports[0]) == freeze['ordinary_report_sha256'], 'changed frozen suite result')
        full = load(reports[0])
        require(full['summary'] == dict(total=20, passed=20, failed=0, cancelled=0, not_run=0), 'ordinary suite incomplete')
        for result in full['results']:
            result_ok(result)
        removal = load(packet/'vis/retained-source/removed.json')
        require(removal['removed'] and removal['source_archive_sha256'] == ARCHIVE_SHA256, 'source cleanup missing')
        cells.append(dict(host=host, freeze_sha256=sha256(packet/'vis/reviewed-contract-freeze.json'),
                          suite_report_sha256=sha256(reports[0]), runner_sha256=runner['copied_sha256']))
    # Publish exact reviewed exports only after both independent packet reviews.
    require(not (reviewed/'contracts').exists() and not (reviewed/'reviewed-contract-freeze.json').exists(), 'freeze already published')
    shutil.copytree(linux, reviewed/'contracts')
    shutil.copyfile(run/'playtestr-Linux/vis/reviewed-contract-freeze.json', reviewed/'reviewed-contract-freeze.json')
    immutable_json(reviewed/'native-authoring-review.json', dict(run=args.run, cells=cells,
                   public_contract_freeze_sha256=sha256(reviewed/'reviewed-contract-freeze.json'),
                   fault_selection='No source fault selected before this independently verified twenty-case freeze.',
                   development_admission=False, final_archive_credit=False))
    print('Reviewed all twenty public recordings, ordinary tests, unchanged native byte/screen oracles and frozen suites before fault selection.')


if __name__ == '__main__':
    main()
