"""Bind Skim V26 exact-candidate execution to current staged harness bytes."""
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
        raise RuntimeError('v26 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v25.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        'V25 was dispatched but the shared final-series helper changed for the Git Town canonical contract '
        'lookup before its integrity check completed. V26 binds the staged helper and Skim series bytes; '
        'the V25 attempt receives no scenario credit unless its retained evidence independently supports it.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v26.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v26.json', declaration)
    print('Declared Skim V26 against staged final-series harness; prior attempt remains preserved.')


if __name__ == '__main__':
    main()
