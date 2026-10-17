"""Inspect native fff first-use events, exact-byte outcomes and source cleanup."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_build_fff import PIN
ARCHIVE_SHA256 = '9411c915529860e0134907fdb5b54282cdd191be202436a6d3df9ed32d175e6f'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--source-revision',default='e7b5f29e575e44babe7fdaa2e83e55b62d318305')
    args = parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(), 'invalid native run')
    root = RAW/'native'/args.run
    metadata = load(root/'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success', 'unsuccessful native run')
    source = args.source_revision
    require(len(source)==40 and all(c in '0123456789abcdef' for c in source),'invalid source revision')
    cells = []
    for host in ['Linux', 'macOS']:
        packet = root/('playtestr-'+host)
        ledger = object.__new__(Campaign)
        ledger.raw = packet
        attempts = ledger.attempts()
        runner = load(packet/'fff-native-runner.json')
        require(runner['source_revision'] == source and runner['candidate_sha256'] == runner['copied_sha256'], 'wrong candidate')
        journeys = list((packet/'fff/first-use').glob('*/journey.json'))
        require(len(journeys) == 1, 'ambiguous first-use journey')
        journey = load(journeys[0])
        require(journey['shell_invocations'] == 3 and journey['recorder_controls'] == 17 and
                not journey['handwritten_playtestr_json'], 'wrong first-use count')
        build = load(packet/'fff/retained-source/build.json')
        require(build['pin'] == PIN and build['archive_sha256'] == ARCHIVE_SHA256, 'wrong target source')
        require(journey['target_build_sha256'] == sha256(packet/'fff/retained-source/build.json'), 'changed target build receipt')
        for identity in [*journey['attempts'], build['syntax_attempt'], build['version_attempt'], load(packet/'fff/retained-source/runtime.json')['version_attempt']]:
            events = attempts[identity]
            require('launched' in events and events['started']['expected_exit'] == 0, 'missing launch')
            finished = events['finished']
            require(finished['category'] == 'passed' and finished['exit_code'] == 0 and
                    finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'], 'command failure or cleanup')
            reference = events['identified']['identity']
            manifest = packet_file(packet, reference['manifest'], 1024**2)
            require(sha256(manifest) == reference['sha256'], 'changed prelaunch identity')
            console = packet_file(packet, events['started']['project']+'/'+identity+'/console.log', 4*1024**2)
            require(sha256(console) == finished['console_sha256'], 'changed console')
            if identity in journey['attempts']:
                files = load(manifest)['files']
                require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'] == runner['copied_sha256'], 'wrong launched runner')
                require(files['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff'] == build['binary_sha256'], 'wrong launched target')
        spec = journeys[0].parent/'spec.json'
        require(sha256(spec) == journey['spec_sha256'], 'changed public export')
        contract = load(spec)
        files = {s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
                 if s.get('state', {}).get('kind') == 'file'}
        require(files == {'starter.txt':b'reviewed seed\n','sentinel.txt':b'preserve existing work\n','new note.txt':b''}, 'wrong independent byte oracle')
        snapshot = next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        scope = load(spec.parent/'snapshots'/snapshot)
        require(scope['snapshot_version']==1 and scope['first_row']==1 and scope['last_row']==24, 'unreviewed row scope')
        report = load(journeys[0].parent/'ordinary-results.json')
        require(report['runner_version'] == 'source-'+source and report['summary']['passed'] == 1, 'wrong ordinary result')
        result = report['results'][0]
        require(result['status'] == 'passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'], 'unconfirmed ordinary cleanup')
        for step in result['steps']:
            if 'state' in step:
                require(step['state']['invocation_id'] == result['invocation_id'] and
                        step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')
        retained = packet/'fff/retained-source'
        removed = load(retained/'removed.json')
        prepared = load(retained/'removal-prepared.json')
        index = load(retained/'verified-index.json')
        require(removed['removed'] and removed['owned_relative_path'] == 'active/fff' and
                removed['source_archive_sha256'] == ARCHIVE_SHA256 == index['archive_sha256'], 'unconfirmed source cleanup')
        require(prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'], 'unconfirmed runtime termination')
        for name in index['selected_restore']:
            require(sha256(retained/'selected-restore'/name) == index['files'][name]['sha256'], 'changed selected restoration')
        cells.append(dict(host=host, runner_sha256=runner['copied_sha256'], target_sha256=build['binary_sha256'],
                          journey_sha256=sha256(journeys[0]), spec_sha256=sha256(spec),
                          cleanup_sha256=sha256(retained/'removed.json')))
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'/('first-use-native-'+args.run+'.json'),
                   dict(run=args.run, cells=cells, source_revision=source, development_admission=False,
                        human_usability='unmeasured', claim='First route only; twenty scenarios and fault gates remain open.'))
    print('Verified native fff first-use source, binary, public commands, saved bytes, replay and cleanup on both hosts.')


if __name__ == '__main__':
    main()
