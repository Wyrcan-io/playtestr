"""Bind Git Town v21 to current campaign helpers and safe no-case cleanup."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v21 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v20.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 20 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v20')
    declaration = dict(prior)
    declaration['revision'] = 21
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V20 passed 480 ordinary candidate executions and 18 calibration phases on both '
        'hosts, but a later campaign harness change to readiness_evidence.py invalidated '
        'its current-source binding before case launch (run 42422136208). The no-case '
        'source cleanup then refused removal because zero case reports existed. V21 binds '
        'the current harness and uses a checked no-case cleanup path that requires an '
        'absent or empty case-evidence tree; v20 and its successful admission remain immutable.'))
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_git_town_final_declare_v21.py'] = 'staged-self-hash'
    for name in harness:
        if name == 'scripts/acceptance/next20_git_town_final_declare_v21.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_git_town_final_declare_v21.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_git_town_final_declare_v21.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v21.json', declaration)
    print('Declared Git Town v21 current-harness and no-case cleanup; zero new admission credit.')


if __name__ == '__main__':
    main()
