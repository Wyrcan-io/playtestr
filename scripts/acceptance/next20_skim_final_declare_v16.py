"""Bind Skim's V17 fault-record and case-aware cleanup harness."""
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
        raise RuntimeError('v16 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v13.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v20'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V15 was superseded before local plan generation because its planner still used '
            'the occupied V18 contracts directory; no V19 contracts or target cases were '
            'created under that declaration. V16 binds a fresh V20 namespace and the corrected '
            'planner/auditor paths. The V17 fault fix updates both the native runtime binary '
            'and the byte-identical case alias during mutation, then restores both exact bytes.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v16.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v16.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v16.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v16.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v16.json', declaration)
    print('Declared Skim V17 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
