"""Bind Skim's v13 plan, bounded cache inventory, and corrected workflow path."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v13 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v7.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v13'
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V12 acquired and built Skim on both native hosts but launched zero candidate '
            'cases. The workflow passed the stale v9 plan path to its independent auditor, '
            'and cache inventory safely refused 217 MiB/531 MiB Rust toolchain files above '
            'the 128 MiB single-file bound. V13 fixes the path, raises only the per-file '
            'bound to 1 GiB, and preserves the 4 GiB total and 250000-file bounds. It reuses '
            'local target copies only after exact build-SHA verification.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v8.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v8.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v8.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v8.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v8.json', declaration)
    print('Declared Skim v13 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
