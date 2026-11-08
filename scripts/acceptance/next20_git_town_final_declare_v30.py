"""Bind Git Town V30 to its reviewed native executable launcher."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v30 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v29.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 29:
        raise ValueError('prior Git Town declaration is not preserved v29')
    declaration = dict(prior)
    declaration['revision'] = 30
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V29 passed contract setup through the exact candidate runtime but the shared series runner '
        'incorrectly restricted native launchers to Taskell. V30 binds the corrected project-aware launcher '
        'validation; the V29 zero-launch attempt remains preserved.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_git_town_final_declare_v30.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v30.json', declaration)
    print('Declared Git Town v30 with the runtime-bound native launcher check.')


if __name__ == '__main__':
    main()
