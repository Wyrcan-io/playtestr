"""Bind Skim V34 to matching public query and result assertion maintenance."""
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
        raise RuntimeError('v34 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v33.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v28'
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'V33 passed all 240 ordinary cases and nine fault phases on both '
            'hosts, then reached public maintenance. It changed the target query '
            'but preserved the recorded expect cedar assertion, so Playtestr '
            'correctly failed before the selected snapshot could be updated. V34 changes the matching '
            'approved result assertion to amber alongside the query, preserves the '
            'first-use export, and binds a regression for exact/missing/ambiguous '
            'maintenance fields under a new plan namespace.'))
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v34.py'] = 'staged-self-hash'
    for path in tuple(harness):
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v34.json', declaration)
    print('Declared Skim V34 with matching query and result assertion maintenance.')


if __name__ == '__main__':
    main()
