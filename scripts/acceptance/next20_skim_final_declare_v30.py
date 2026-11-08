"""Bind Skim V30 exact-candidate execution to the public-route harness."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from next20_skim_final_series import BATCHES
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
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v29.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'V29 predates the public-route workflow integration and its final-workflow '
            'hash. V30 freezes the public authoring route, its prelaunch plan, and '
            'the exact current source-bound workflow before target execution.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v30.py'
    harness[name] = 'staged-self-hash'
    harness['scripts/acceptance/next20_skim_public_route.py'] = 'staged-public-route'
    for path in tuple(harness):
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v30.json', declaration)
    print('Declared Skim V30 against the staged public-route workflow and harness.')


if __name__ == '__main__':
    main()
