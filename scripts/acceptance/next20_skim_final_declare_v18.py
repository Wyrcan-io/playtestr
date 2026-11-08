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
        raise RuntimeError('v18 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v17.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v22'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V17 was superseded before hosted execution after reviewing the complete V16 '
            'artifacts. The Windows mutation was detected with process cleanup confirmed, '
            'but restoring the source and invoking Cargo incrementally did not reproduce the '
            'pinned executable byte-for-byte. V18 adds an exact-package cargo clean before '
            'the restored rebuild, without clearing dependency caches, and retains the '
            'dual-path runtime/alias mutation fix. No V16/V17 new-project credit is claimed.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v18.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v18.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v18.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v18.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v18.json', declaration)
    print('Declared Skim V18 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
