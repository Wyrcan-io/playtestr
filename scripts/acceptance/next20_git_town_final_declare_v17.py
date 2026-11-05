"""Bind Git Town v17 to the exact candidate startup profile it executes."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v17 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v16.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 16 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v16')
    declaration = dict(prior)
    declaration['revision'] = 17
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=(prior['supersedes']['reason'] +
            ' V16 run 41984301547 confirmed Linux again materialized N01 with a 2000 ms '
            'startup deadline despite its declared 5000 ms value. The shared batch runner '
            'read its legacy v1 declaration because Git Town had validated v16 only in '
            'the top-level wrapper. Windows completed its full 240-case/nine-phase series '
            'and checked cleanup; Linux passed 220 cases before the same first-output '
            'timeout. Preserve the attempt without retry credit. V17 threads the selected '
            'candidate host profile explicitly into the shared batch runner, with a '
            'regression proving the explicit value overrides the legacy profile.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v17.py',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_jrnl_final.py',
        'scripts/acceptance/next20_startup_profile.py',
        'scripts/acceptance/test_next20_startup_profile.py',
    ]:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    summary = dict(declaration['revision_summary'])
    summary['preserved_failed_runs'] = list(summary['preserved_failed_runs']) + ['41984301547']
    declaration['revision_summary'] = summary
    immutable_json(package / 'final-series-declaration-native-exit-v17.json', declaration)
    print('Declared Git Town exact rc.6 series v17 with the explicit candidate startup profile bound; zero admission credit.')


if __name__ == '__main__':
    main()
