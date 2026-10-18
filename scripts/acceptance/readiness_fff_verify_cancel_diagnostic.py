"""Verify actual bounded observations without turning green retries into a fix."""
import json

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_fff_verify_native import SOURCE, require


def main():
    run = RAW / 'native/39147072326'
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and len(metadata['jobs']) == 1 and metadata['jobs'][0]['conclusion'] == 'success',
            'diagnostic native job incomplete')
    packet = run / 'playtestr-Linux'
    ledger = object.__new__(Campaign)
    ledger.raw = packet
    attempts = ledger.attempts()
    summaries = list((packet / 'fff/cancel-diagnostics').glob('*/summary.json'))
    require(len(summaries) == 1, 'ambiguous diagnostic')
    path = summaries[0]
    summary = load(path)
    intent = load(path.parent / 'intent.json')
    spec = packet / 'fff/host-contracts/E03.json'
    runner = load(packet / 'fff-native-runner.json')
    retained = packet / 'fff/retained-source'
    runtime = load(retained / 'runtime.json')
    source = load(retained / 'verified-index.json')['files']['fff']['sha256']
    require(runner['source_revision'] == SOURCE and runner['candidate_sha256'] == runner['copied_sha256'],
            'wrong diagnostic runner')
    require(intent['public_contract_sha256'] == sha256(spec)
            == sha256(ROOT / 'docs/validation/runner-readiness-ten-project-pass/fff/contracts/E03.json'),
            'diagnostic changed frozen E03')

    def witness(identity, diagnostic=False):
        events = attempts[identity]
        require('launched' in events and events['started']['expected_exit'] == 0,
                'missing actual diagnostic launch')
        finished = events['finished']
        require(finished['exit_code'] == 0 and finished['harness_cleanup'] == 'harness_process_reaped'
                and not finished['cleanup_errors']
                and finished['category'] == ('diagnostic_observation' if diagnostic else 'passed'),
                'diagnostic outcome or cleanup differs')
        ref = events['identified']['identity']
        manifest = packet_file(packet, ref['manifest'], 1024**2)
        require(sha256(manifest) == ref['sha256'], 'changed prelaunch diagnostic identity')
        files = load(manifest)['files']
        require(files['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff'] == source,
                'different actual interpreted source')
        if not diagnostic:
            require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'] == runner['copied_sha256']
                    and files['artifacts/runner-readiness-ten-project-pass/fff/host-contracts/E03.json'] == sha256(spec),
                    'different actual runner or public spec')
            console = packet_file(packet, 'fff/' + identity + '/console.log', 4*1024**2)
            require(sha256(console) == finished['console_sha256'], 'changed public diagnostic output')

    require(len(summary['public']) == 20 and len(summary['independent']) == 12,
            'incomplete declared diagnostic budget')
    for number, row in enumerate(summary['public']):
        require(row['number'] == number and row['status'] == 'passed', 'public diagnostic failure')
        matches = [key for key, event in attempts.items()
                   if event['started']['label'] == 'unchanged-current-E03-' + str(number)]
        require(len(matches) == 1, 'ambiguous public diagnostic attempt')
        witness(matches[0])
        report = path.parent / ('public-' + str(number) + '.json')
        value = load(report)
        require(sha256(report) == row['report_sha256'] and value['runner_version'] == 'source-' + SOURCE,
                'changed diagnostic report or source')
        result = value['results'][0]
        require(result['status'] == 'passed' and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'], 'public result or cleanup differs')
        for step in result['steps']:
            require(step['status'] == 'passed', 'incomplete public step')
            if 'state' in step:
                require(step['state']['invocation_id'] == result['invocation_id']
                        and step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')
    for number, row in enumerate(summary['independent']):
        witness(row['attempt'], diagnostic=True)
        folder = path.parent / ('backspace-batched-' + str(number))
        require(load(folder / 'observation.json') == row and not row['timed_out']
                and row['exit_code'] == 0 and not row['forced_shutdown']
                and row['source_sha256'] == source
                and row['interpreter_sha256'] == runtime['bash_sha256']
                and sha256(folder / 'raw-pty.bin') == row['raw_output_sha256']
                and row['fixture_files'] == {'source.txt': b'keep exact bytes\n'.hex()},
                'independent PTY/source/runtime/bytes differ')
    require(load(retained / 'removed.json')['removed']
            and load(retained / 'removal-prepared.json')['runtime_processes_verified'],
            'diagnostic runtime cleanup unconfirmed')
    immutable_json(ROOT / 'docs/validation/runner-readiness-ten-project-pass/fff/current-source-cancel-investigation.json',
                   dict(source_revision=SOURCE, first_failure_run='39146617427', diagnostic_run='39147072326',
                        summary_sha256=sha256(path), public_passes=20, independent_passes=12,
                        disposition='Unreproduced exit timeout. Cause unknown; no product, target or fixture repair demonstrated.',
                        qualification_credit=0, stable_qualification='open; first failure remains in denominator',
                        next='Separate full native requalification series; preserve all original actions and expectations.'))
    print('Verified 20 public and 12 independent green diagnostic observations; original timeout remains unresolved.')


if __name__ == '__main__':
    main()
