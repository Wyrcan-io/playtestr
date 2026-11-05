"""Bind Git Town v20 to complete pre-removal source-fault evidence retention."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
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
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v19.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 19 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v19')
    declaration = dict(prior)
    declaration['revision'] = 20
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        prior['supersedes']['reason'] +
        ' V19 retained all four owned evidence directories before removal but did not copy '
        'the root-level fault-matrix-started receipt that the final fault matrix hashes. '
        'V20 includes that receipt whenever owned evidence directories are selected and '
        'binds the updated cleanup helper. V18 and v19 remain immutable unused declarations; '
        'no workflow run or target execution occurred under either declaration.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v20.py',
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
    immutable_json(package / 'final-series-declaration-native-exit-v20.json', declaration)
    print('Declared a fresh Git Town v20 series with complete bounded native fault evidence retention; zero admission credit.')


if __name__ == '__main__':
    main()
