"""Bind Skim's restored-binary evidence and recovery harness without reproducibility claims."""
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
        raise RuntimeError('v20 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v19.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v24'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V19 passed all 240 ordinary cases on both hosts and completed all three '
            'baseline/corrupted/restored calibrations on Linux. Windows detected its first '
            'mutant and restored the exact pinned source and executable in finally, but its '
            'normal restored-source rebuild differed bytewise and the harness stopped before '
            'the restored recovery invocation. The campaign protocol explicitly says not to '
            'claim native binary reproducibility when rebuilds differ. V20 retains and hashes '
            'that actual restored-source rebuild, restores the verified pinned executable and '
            'runtime identity, and runs the restored recovery contract without equating the '
            'two binaries.'
        ),
    )
    harness = dict(prior['harness_files'])
    name = 'scripts/acceptance/next20_skim_final_declare_v20.py'
    harness[name] = 'staged-self-hash'
    for path in tuple(harness):
        if path == name:
            continue
        harness[path] = hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v20.json', declaration)
    print('Declared Skim V20 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
