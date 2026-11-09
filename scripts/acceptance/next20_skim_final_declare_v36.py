"""Bind Skim V36 to the corrected independent declaration audit."""
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
        raise RuntimeError('v36 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v35.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['batches'] = BATCHES
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v30'
    declaration['supersedes'] = dict(
        path=prior_path.name, sha256=sha256(prior_path), reason=(
            'Run 42537098520 froze contracts but its independent Linux audit '
            'still loaded the V34 declaration while the plan bound V35. V36 '
            'corrects that audit input and binds the updated series/audit sources '
            'under a fresh plan namespace. Scenarios, assertions, batches, faults, '
            'candidate and expected outcomes are unchanged; the V35 run grants '
            'zero execution credit.'))
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v36.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path != name:
            harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v36.json', declaration)
    print('Declared Skim V36 with the corrected independent audit and current harness identities.')


if __name__ == '__main__':
    main()
