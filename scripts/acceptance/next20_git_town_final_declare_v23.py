"""Bind Git Town v23 to the latest cleanup evidence helper."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v23 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v22.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 22 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v22')
    declaration = dict(prior)
    declaration['revision'] = 23
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'The V22 supplemental Git Town final workflow was triggered by the Skim case-evidence '
        'cleanup helper update and correctly stopped before any candidate case because its '
        'declaration still bound the previous next20_target_cleanup.py bytes. Both native '
        'preflights preserved source/runtime and produced zero launches. V23 binds the current '
        'shared cleanup helper and its regression test; the existing Git Town admission record '
        'remains governing, and this rerun remains supplemental.' ))
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_git_town_final_declare_v23.py'] = 'staged-self-hash'
    for name in harness:
        if name == 'scripts/acceptance/next20_git_town_final_declare_v23.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_git_town_final_declare_v23.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_git_town_final_declare_v23.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v23.json', declaration)
    print('Declared Git Town v23 against current shared cleanup helper; supplemental, zero new admission credit.')


if __name__ == '__main__':
    main()
