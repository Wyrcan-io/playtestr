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
        raise RuntimeError('v19 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v18.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v23'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V18 completed the local Windows plan/audit with zero launches, but the focused '
            'test for the package-only Cargo clean command had a malformed TOML fixture and '
            'failed before native execution. V19 fixes the test fixture, binds the exact '
            'dual-binary and package-clean harness, and uses a fresh V23 plan namespace.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v19.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v19.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v19.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v19.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v19.json', declaration)
    print('Declared Skim V19 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
