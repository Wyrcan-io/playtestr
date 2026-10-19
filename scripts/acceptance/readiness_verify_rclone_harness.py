"""Independently bind the three native compiled-provenance regression results."""
import argparse
import re
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',default='39274410205')
    parser.add_argument('--tests',type=int,default=37)
    parser.add_argument('--source',default='1f62fe835ba6178330859722e9db2d8cc5068afb')
    parser.add_argument('--output',default='native-harness.json')
    parser.add_argument('--windows-symlink-unavailable',action='store_true')
    args=parser.parse_args()
    if (not re.fullmatch(r'[0-9]{1,20}',args.run) or not re.fullmatch(r'[0-9a-f]{40}',args.source)
            or not 37<=args.tests<=1000 or not re.fullmatch(r'[a-z0-9-]+\.json',args.output)):
        raise RuntimeError('invalid native harness selection')
    run = args.run
    root = RAW / 'native' / run
    metadata = load(root / 'run-metadata.json')
    if (metadata['status'] != 'completed' or metadata['conclusion'] != 'success'
            or metadata['headSha'] != args.source):
        raise RuntimeError('native harness run identity/conclusion differs')
    hosts = {'ubuntu-24.04': 2, 'macos-15': 2, 'windows-2025': 1}
    if args.windows_symlink_unavailable:
        if args.tests<43:raise RuntimeError('storage link calibration is absent in this historical harness')
        hosts['windows-2025']=2
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
        if host=='windows-2025' and args.windows_symlink_unavailable:
            if 'test_directory_link_counts_only_its_metadata_without_traversal' not in text or 'Native directory symlink prerequisite unavailable' not in text:
                raise RuntimeError('declared Windows link prerequisite skip is not actually recorded')
        if (result['category'] != 'passed' or result['exit_code'] != 0
                or str(started['ci_run_id']) != run or sha256(log) != result['console_sha256']
                or 'Ran '+str(args.tests)+' tests in ' not in text or 'OK (skipped='+str(skipped)+')' not in text
                or 'test_compiled_app_source_lock_compiler_and_binary_are_bound (test_readiness_rclone_identity.RcloneIdentityTests.test_compiled_app_source_lock_compiler_and_binary_are_bound) ... ok' not in text):
            raise RuntimeError('actual native compiled provenance regression evidence differs')
        cells.append(dict(host=host, attempt=result['id'], log_sha256=sha256(log),
                          discovered_tests=args.tests, passed_tests=args.tests-skipped, platform_specific_skips=skipped))
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'/args.output,
        dict(run=run, source_commit=metadata['headSha'], metadata_sha256=sha256(root/'run-metadata.json'),
             cells=cells, product_control_credit=0, qualification='Harness only; no Rclone application or final archive admission.'))
    print('Verified actual compiled provenance regression on three native hosts.')


if __name__ == '__main__':
    main()
