"""Bind Skim's restored-binary recovery harness after the V20 zero-launch audit failure."""
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
        raise RuntimeError('v21 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v20.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v25'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V20 correctly preserved the V19 Windows rebuild mismatch as a non-reproducible '
            'native build and added a retained rebuild plus exact pinned-binary recovery. Its '
            'local plan was refused before launch because the planner and independent auditor '
            'still selected the V19 declaration and V23 packet paths. V21 updates both readers '
            'to this declaration and a fresh V25 packet namespace, binds that exact harness, '
            'and preserves the V20 preflight refusal.'
        ),
    )
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v21.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path == name:
            continue
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v21.json', declaration)
    print('Declared Skim V21 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
