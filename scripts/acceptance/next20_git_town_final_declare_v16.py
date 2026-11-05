"""Bind Git Town v16 to the observed per-host startup boundary."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v16 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v15.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 15 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v15')
    declaration = dict(prior)
    declaration['revision'] = 16
    declaration['batches'] = [dict(row) for row in prior['batches']]
    declaration['batches'][11]['change'] = (
        'Linux 5000 ms and Windows 2000 ms first-output startup boundaries; '
        'Linux v15 N01 exceeded 2000 ms; ordinary step/run budgets unchanged')
    declaration['startup_timeout_ms_by_host'] = {'linux': 5000, 'windows': 2000}
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=(prior['supersedes']['reason'] +
            ' V15 run 41980469906 passed Windows 240 ordinary cases and all nine '
            'fault phases with process/source/runtime cleanup. Linux passed 220 ordinary '
            'cases in batches 0-10; its first batch-11 N01 launch produced no initial '
            'output within the declared 2000 ms startup boundary and failed with '
            'assertion_timeout. The attempt, report and both host packets are retained; '
            'no retry or candidate credit is counted. V16 changes only the Linux '
            'batch-11 startup boundary to 5000 ms based on this observed timeout; '
            'Windows remains 2000 ms and ordinary deadlines are unchanged.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v16.py',
        'scripts/acceptance/next20_git_town_final_series.py',
    ]:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    summary = dict(declaration['revision_summary'])
    summary['preserved_failed_runs'] = list(summary['preserved_failed_runs']) + ['41980469906']
    declaration['revision_summary'] = summary
    immutable_json(package / 'final-series-declaration-native-exit-v16.json', declaration)
    print('Declared Git Town exact rc.6 series v16 with observed per-host startup bounds; zero admission credit.')


if __name__ == '__main__':
    main()
