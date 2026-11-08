"""Bind Git Town V29 after native-series runtime-lock path correction."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v29 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v28.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 28 or prior.get('canonical_scenario_sha256') != sha256(
            package / 'scenarios-native-exit-v6.json'):
        raise ValueError('prior Git Town declaration is not preserved v28')
    declaration = dict(prior)
    declaration['revision'] = 29
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V28 reached native execution but credited zero cases because Git Town uses its canonical '
        'native-runtime-lock.json while the shared helper required a series-suffixed filename. V29 binds '
        'the helper fallback to the exact canonical lock; the V28 failure remains zero-credit.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_git_town_final_declare_v29.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v29.json', declaration)
    print('Declared Git Town v29 with the canonical runtime-lock path bound.')


if __name__ == '__main__':
    main()
