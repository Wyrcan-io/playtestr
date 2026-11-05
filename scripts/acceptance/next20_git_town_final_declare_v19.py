"""Bind Git Town v19 after bounding and retaining native fault evidence."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
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
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v18.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 18 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v18')
    declaration = dict(prior)
    declaration['revision'] = 19
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        prior['supersedes']['reason'] +
        ' V18 was generated before the final owned-directory retention helper was updated '
        'to copy the calibration reports, fault builds, fault binaries and fault events into '
        'the retained source packet before target removal. Its immutable declaration hash '
        'is preserved; the staged-hash generator refused to overwrite it. V19 binds the '
        'updated cleanup helper, bounded directory allowlist, regression test and workflow '
        'arguments. No v18 hosted job or target execution occurred.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v19.py',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_jrnl_final.py',
        'scripts/acceptance/next20_startup_profile.py',
        'scripts/acceptance/test_next20_startup_profile.py',
        'scripts/acceptance/next20_target_cleanup.py',
        'scripts/acceptance/test_next20_target_cleanup.py',
        '.github/workflows/runner-readiness-next20-git-town-final.yml',
    ]:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    immutable_json(package / 'final-series-declaration-native-exit-v19.json', declaration)
    print('Declared a fresh Git Town v19 series with measured startup and retained calibration evidence; zero admission credit.')


if __name__ == '__main__':
    main()
