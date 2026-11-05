"""Freeze Git Town final-series v3 with line-ending-stable harness hashes."""
import hashlib
import json
from pathlib import Path

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def harness_sha(path):
    data = path.read_bytes()
    if path.suffix.lower() in {'.py', '.ps1', '.yml', '.yaml'}:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v2.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 2 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not the preserved v2')
    declaration = dict(prior)
    declaration['revision'] = 3
    declaration['supersedes'] = dict(
        path='final-series-declaration-native-exit-v2.json',
        sha256=sha256(prior_path),
        reason='Hosted attempt 41954388734 proved raw harness hashes differed across Linux LF and Windows CRLF checkouts; v3 hashes normalized text bytes so the same tracked harness is verified identically on both hosts.')
    declaration['harness_hash_policy'] = 'For .py, .ps1, .yml and .yaml harness files, normalize CRLF to LF before SHA-256; all other harness bytes remain exact.'
    declaration['harness_files'] = {
        name: harness_sha(ROOT / name) for name in prior['harness_files']
    }
    declaration['harness_files']['scripts/acceptance/next20_git_town_final_declare_v3.py'] = harness_sha(
        ROOT / 'scripts/acceptance/next20_git_town_final_declare_v3.py')
    destination = package / 'final-series-declaration-native-exit-v3.json'
    immutable_json(destination, declaration)
    print('Declared Git Town exact rc.6 series v3 with line-ending-stable harness hashes; zero admission credit.')


if __name__ == '__main__':
    main()
