"""Bind Skim's v10 zero-launch plan to the staged cleanup-safe harness."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v10 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v4.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v10'
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V9 acquired and built the pinned target on both native hosts but executed zero '
            'candidate cases. Its wrapper rejected the 9600-second argument above the '
            '2400-second command cap; the Linux socket test inherited an overlong TMP path; '
            'and both hosts exceeded the generic cleanup inventory bound on compiler caches. '
            'V10 bounds the series call to 2400 seconds, creates the socket test under the '
            'short workspace root, hashes and removes only declared Skim-owned compiler '
            'cache roots after source/process checks, and independently rechecks the prepared '
            'target inventory before Unix removal. V9 artifacts remain preserved and uncredited.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness.update({
        'scripts/acceptance/next20_skim_final_declare_v5.py': 'staged-self-hash',
        'scripts/acceptance/next20_skim_cache_cleanup.py': 'staged-cache-cleanup-hash',
        'scripts/acceptance/next20_skim_target_remove.py': 'staged-target-removal-hash',
        'scripts/acceptance/test_next20_skim_cleanup.py': 'staged-cleanup-test-hash',
    })
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v5.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v5.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v5.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v5.json', declaration)
    print('Declared Skim v10 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
