"""Freeze Git Town final-series v4 from staged Git blobs, not a dirty worktree."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def index_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('harness file is not present in the Git index: ' + name)
    return result.stdout


def harness_sha(name):
    data = index_bytes(name)
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v3.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 3 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not the preserved v3')
    declaration = dict(prior)
    declaration['revision'] = 4
    declaration['supersedes'] = dict(
        path='final-series-declaration-native-exit-v3.json',
        sha256=sha256(prior_path),
        reason='Hosted attempt 41955366681 found that v3 was generated from a modified local readiness_evidence.py not present in the pushed commit. V4 hashes the staged Git index blobs, normalizing CRLF/LF only for text harness files, so the declaration binds the exact source CI checks out.')
    declaration['harness_hash_policy'] = 'Hash staged Git index blob bytes; for .py, .ps1, .yml and .yaml normalize CRLF to LF before SHA-256. Runtime worktree files are normalized identically before comparison.'
    declaration['harness_files'] = {
        name: harness_sha(name) for name in prior['harness_files']
    }
    name = 'scripts/acceptance/next20_git_town_final_declare_v4.py'
    declaration['harness_files'][name] = harness_sha(name)
    immutable_json(package / 'final-series-declaration-native-exit-v4.json', declaration)
    print('Declared Git Town exact rc.6 series v4 from staged Git blobs; zero admission credit.')


if __name__ == '__main__':
    main()
