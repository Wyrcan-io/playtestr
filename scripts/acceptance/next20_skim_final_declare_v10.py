"""Bind Skim's V15 fault-record and case-aware cleanup harness."""
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
        raise RuntimeError('v15 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v9.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v15'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V14 independently audited and completed 240 ordinary cases on each host. Both '
            'fault-calibration commands then failed while serializing a pathlib.Path in the '
            'mutant build record, after one baseline control and one mutant build per host; '
            'source and executable restoration verified. Cache removal passed on both hosts. '
            'Target cleanup refused its no-case mode because the newly retained active '
            'case-evidence contains ordinary reports. V15 serializes build argv as strings and '
            'lets cleanup inspect a bounded set of exact active case report.json files before '
            'retaining and removing the owned target.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v10.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v10.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v10.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v10.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v10.json', declaration)
    print('Declared Skim v15 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
