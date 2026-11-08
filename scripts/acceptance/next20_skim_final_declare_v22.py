"""Bind Skim's complete V22 declaration, planner, auditor, and workflow paths."""
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
        raise RuntimeError('v22 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v21.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v26'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V21 updated the declaration and planner packet paths, and its local Windows '
            'prepare/audit passed for all 240 cases. The hosted Linux job then exposed one '
            'remaining stale path in the workflow command that invoked the independent auditor '
            'with V23; it refused before target launch. V22 updates and hash-binds the workflow '
            'path to this declaration’s V26 packet, while preserving that zero-launch failure.'
        ),
    )
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v22.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path == name:
            continue
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v22.json', declaration)
    print('Declared Skim V22 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
