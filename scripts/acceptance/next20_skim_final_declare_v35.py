"""Rebind Skim V35 after a prelaunch shared-helper identity refusal."""
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
        raise RuntimeError('v35 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v34.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v29'
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'Run 42533986434 was refused before target execution on both hosts because '
            'next20_jrnl_final.py changed after the V34 helper freeze. V35 binds the current '
            'shared runner helper, Skim final-series launcher, regression source, and declaration '
            'generator under a fresh plan namespace. Candidate, contracts, case semantics, '
            'batches, fault phases, and expected outcomes are unchanged; V34 remains a zero-launch '
            'failed attempt.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v35.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v35.json', declaration)
    print('Declared Skim V35 with current shared runner-helper and harness identities.')


if __name__ == '__main__':
    main()
