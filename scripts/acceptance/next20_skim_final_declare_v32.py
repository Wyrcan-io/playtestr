"""Bind Skim V32 to explicit public-authoring evidence-phase support."""
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
        raise RuntimeError('v32 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v31.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'V31 reached exact native series and fault execution, but its public '
            'route refused the declared public-authoring evidence phase before '
            'target launch. V32 explicitly enables and tests that phase and binds '
            'the updated native workflow before the next exact-candidate attempt.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v32.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v32.json', declaration)
    print('Declared Skim V32 with tested public-authoring phase support.')


if __name__ == '__main__':
    main()
