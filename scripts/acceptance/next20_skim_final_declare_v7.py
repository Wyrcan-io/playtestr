"""Bind Skim's v12 plan after correcting the declaration/contract namespace mismatch."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v12 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v6.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v12'
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V11 preparation stopped before producing a plan or launching a target because '
            'the series planner still referenced the V10 contract namespace while its '
            'independent auditor expected V11. V12 binds both planner and auditor to the '
            'same fresh contract namespace. V11 remains a zero-launch failed preflight; '
            'the timeout, cache cleanup and prepared-removal fixes remain in force.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v7.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v7.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v7.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v7.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v7.json', declaration)
    print('Declared Skim v12 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
