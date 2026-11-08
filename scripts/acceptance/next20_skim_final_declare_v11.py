"""Bind Skim's V16 fault-record and case-aware cleanup harness."""
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
    prior_path = package / 'final-series-declaration-native-exit-v10.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v16'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V15 completed all 240 ordinary cases on each native host. Each host passed a '
            'baseline control and built its first source mutant, then correctly refused to '
            'launch because the harness changed build.json but left runtime.json pinned to '
            'the original binary provenance. The mutant target was never executed; exact '
            'source/runtime restoration and bounded target cleanup passed. V16 updates the '
            'runtime identity in lockstep with each mutant build and restores the original '
            'runtime bytes before the recovery control and in finally cleanup.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v11.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v11.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v11.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v11.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v11.json', declaration)
    print('Declared Skim v16 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
