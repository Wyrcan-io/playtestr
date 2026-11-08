"""Bind Skim V33 to non-overwriting public maintenance evidence."""
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
        raise RuntimeError('v33 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v32.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v27'
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'V32 passed all 240 exact-archive cases, nine source-fault phases, '
            'and checked cleanup on Linux, but its public maintenance route tried '
            'to overwrite the immutable first-use selection.json and stopped. '
            'V33 preserves that original export and writes the approved changed '
            'query to a distinct selection-maintenance.json, with a focused '
            'immutability regression and updated native plan namespace.'))
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v33.py'] = 'staged-self-hash'
    harness['scripts/acceptance/test_next20_skim_public_route.py'] = 'staged-self-hash'
    for path in tuple(harness):
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v33.json', declaration)
    print('Declared Skim V33 with preserved first-use and distinct maintenance specs.')


if __name__ == '__main__':
    main()
