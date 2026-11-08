"""Bind Git Town v27 to the corrected campaign-owned contract lookup."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v27 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v26.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 26 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v26')
    declaration = dict(prior)
    declaration['revision'] = 27
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V26 reached native final execution but credited zero scenarios: the shared final-series helper '
        'looked for scenarios under docs although this campaign materializes the exact frozen contracts '
        'under RAW. V27 binds the corrected canonical-package lookup; the failed V26 attempt is preserved.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_git_town_final_declare_v27.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v27.json', declaration)
    print('Declared Git Town v27 against staged final-series harness; failed V26 remains zero-credit.')


if __name__ == '__main__':
    main()
