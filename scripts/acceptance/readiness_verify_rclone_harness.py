"""Independently bind the three native compiled-provenance regression results."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    run = '39274410205'
    root = RAW / 'native' / run
    metadata = load(root / 'run-metadata.json')
    if (metadata['status'] != 'completed' or metadata['conclusion'] != 'success'
            or metadata['headSha'] != '1f62fe835ba6178330859722e9db2d8cc5068afb'):
        raise RuntimeError('native harness run identity/conclusion differs')
    hosts = {'ubuntu-24.04': 2, 'macos-15': 2, 'windows-2025': 1}
    jobs = metadata['jobs']
    if len(jobs) != 3 or {j['name'] for j in jobs} != {'native-harness ('+h+')' for h in hosts}:
        raise RuntimeError('partial or unexpected native host matrix')
    if any(j['status'] != 'completed' or j['conclusion'] != 'success' for j in jobs):
        raise RuntimeError('native host did not succeed')
    cells = []
    for host, skipped in hosts.items():
        packet = root / ('runner-readiness-harness-' + host)
        finished = [load(p) for p in (packet/'events').glob('*-finished.json')
                    if load(p)['label'] == 'native-harness-controls']
        if len(finished) != 1:
            raise RuntimeError('missing or duplicate native harness result')
        result = finished[0]
        started = load(packet/'events'/(result['id']+'-started.json'))
        log = packet/'core'/result['id']/'console.log'
        text = log.read_text(encoding='utf-8')
        if (result['category'] != 'passed' or result['exit_code'] != 0
                or str(started['ci_run_id']) != run or sha256(log) != result['console_sha256']
                or 'Ran 37 tests in ' not in text or 'OK (skipped='+str(skipped)+')' not in text
                or 'test_compiled_app_source_lock_compiler_and_binary_are_bound (test_readiness_rclone_identity.RcloneIdentityTests.test_compiled_app_source_lock_compiler_and_binary_are_bound) ... ok' not in text):
            raise RuntimeError('actual native compiled provenance regression evidence differs')
        cells.append(dict(host=host, attempt=result['id'], log_sha256=sha256(log),
                          discovered_tests=37, passed_tests=37-skipped, platform_specific_skips=skipped))
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/native-harness.json',
        dict(run=run, source_commit=metadata['headSha'], metadata_sha256=sha256(root/'run-metadata.json'),
             cells=cells, product_control_credit=0, qualification='Harness only; no Rclone application or final archive admission.'))
    print('Verified actual compiled provenance regression on three native hosts.')


if __name__ == '__main__':
    main()
