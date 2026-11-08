"""Rebind Git Town V31 after a prelaunch shared-helper identity refusal."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v31 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v30.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 30:
        raise ValueError('prior Git Town declaration is not preserved v30')
    declaration = dict(prior)
    declaration['revision'] = 31
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'Run 42533986432 reached the exact candidate installation on both hosts, then '
            'refused final-series launch because the shared next20_jrnl_final.py helper had '
            'changed after V30 was frozen. The failed prelaunch attempt and its provider packets '
            'remain preserved. V31 rebinds the current helper and declaration-generator bytes; '
            'candidate, contracts, batches, faults and expected outcomes remain unchanged.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_git_town_final_declare_v31.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v31.json', declaration)
    print('Declared Git Town V31 with current shared runner-helper and harness identities.')


if __name__ == '__main__':
    main()
