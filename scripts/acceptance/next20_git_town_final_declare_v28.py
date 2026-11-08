"""Declare Git Town's frozen scenario bytes separately from its test-freeze receipt."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v28 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v27.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 27 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v27')
    declaration = dict(prior)
    declaration['revision'] = 28
    declaration['canonical_scenario_sha256'] = sha256(package / 'scenarios-native-exit-v6.json')
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V27 reached native execution but launched zero cases because its final-series declaration uses '
        'canonical_test_freeze_sha256 for the freeze receipt, while the shared helper interpreted that field '
        'as the scenario hash. V28 declares the immutable scenario digest independently; the V27 failure remains.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_git_town_final_declare_v28.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v28.json', declaration)
    print('Declared Git Town v28 with separate freeze and scenario identities; V27 remains zero-credit.')


if __name__ == '__main__':
    main()
