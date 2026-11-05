"""Bind Git Town v15 to the adapter's validated 2400-second deadline."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v15 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v14.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 14 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v14')
    declaration = dict(prior)
    declaration['revision'] = 15
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=(prior['supersedes']['reason'] +
            ' V14 workflow 41978773971 requested a 2400-second command deadline, but '
            'the next20_check adapter rejected it at its 1200-second parser cap before '
            'any target launch on either host. Both refusal packets and zero-launch '
            'cleanup refusals are preserved; target case counters do not change. V15 '
            'raises the adapter cap with numeric argument validation and boundary coverage.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v15.py',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_check.py',
        'scripts/acceptance/test_next20_campaign.py',
    ]:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    summary = dict(declaration['revision_summary'])
    summary['preserved_failed_runs'] = list(summary['preserved_failed_runs']) + ['41978773971']
    declaration['revision_summary'] = summary
    immutable_json(package / 'final-series-declaration-native-exit-v15.json', declaration)
    print('Declared Git Town exact rc.6 series v15 from staged blobs; zero admission credit.')


if __name__ == '__main__':
    main()
