"""Bind Git Town v22 to current campaign helpers and safe no-case cleanup."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v22 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v21.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 21 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v21')
    declaration = dict(prior)
    declaration['revision'] = 22
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V21 was dispatched with the checked no-case cleanup helper before the additional '
        'in-target junction inventory and escape-rejection controls were added. V22 binds '
        'the expanded cleanup helper and tests. Prior V21 run artifacts and outcomes remain '
        'immutable; V22 requires a fresh complete two-host series before current evidence '
        'can be closed.'))
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_git_town_final_declare_v22.py'] = 'staged-self-hash'
    for name in harness:
        if name == 'scripts/acceptance/next20_git_town_final_declare_v22.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_git_town_final_declare_v22.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_git_town_final_declare_v22.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v22.json', declaration)
    print('Declared Git Town v22 current-harness and in-root junction cleanup; zero new admission credit.')


if __name__ == '__main__':
    main()
