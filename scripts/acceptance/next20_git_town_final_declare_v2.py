"""Freeze the corrected bounded-wrapper invocation as Git Town declaration v2."""
import json

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v1.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 1 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not the preserved v1')
    declaration = dict(prior)
    declaration['revision'] = 2
    declaration['supersedes'] = dict(
        path='final-series-declaration-native-exit-v1.json',
        sha256=sha256(prior_path),
        reason='Hosted attempt 41953084178 exposed that the declared 3300-second wrapper limit exceeded next20_check.py maximum 1200 seconds; the command was refused before target tests launched.')
    declaration['wrapper_timeout_seconds'] = 1200
    declaration['harness_files'] = dict(prior['harness_files'])
    harness_paths = [
        '.github/workflows/runner-readiness-next20-git-town-final.yml',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_git_town_final_declare_v2.py',
    ]
    for name in harness_paths:
        declaration['harness_files'][name] = sha256(ROOT / name)
    destination = package / 'final-series-declaration-native-exit-v2.json'
    immutable_json(destination, declaration)
    print('Declared Git Town exact rc.6 series v2 with a bounded 1200-second wrapper; zero admission credit.')


if __name__ == '__main__':
    main()
