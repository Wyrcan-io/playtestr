"""Bind the v6 exact-candidate run to staged harness blobs."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v6 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v5.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 5 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v5')
    declaration = dict(prior)
    declaration['revision'] = 6
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=('Hosted attempt 41960284415 installed the exact candidate and verified the '
                'pinned checkout but both hosts rejected the downloaded codeload archive '
                'digest before build or target launch. V6 creates a deterministic archive '
                'from the exact manifest-verified checkout and independently reopens and '
                'hashes every member. V1-v5 remain preserved failures.'))
    declaration['harness_hash_policy'] = (
        'Hash staged Git index blob bytes; for .py, .ps1, .yml and .yaml normalize CRLF to LF before SHA-256. Runtime worktree files are normalized identically before comparison.')
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest()
        for name in prior['harness_files']
    }
    declaration['harness_files']['scripts/acceptance/next20_git_town_final_declare_v6.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_git_town_final_declare_v6.py')).hexdigest()
    declaration['harness_files']['scripts/acceptance/test_next20_git_town_prepare.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/test_next20_git_town_prepare.py')).hexdigest()
    declaration['source_archive_policy'] = (
        'Generated locally as deterministic gzip/PAX from the verified pinned checkout; the archive is reopened and every member SHA-256 is checked against source-provenance.json before build. The generated archive digest and bytes are bound in acquisition.json and the execution plan.')
    declaration['revision_summary'] = dict(
        v5_scenario_catalog='scenario-catalog-v4.json',
        v5_contract_freeze='development-test-freeze-native-exit-v2.json',
        preserved_failed_runs=['41953084178', '41954388734', '41955366681', '41956408435', '41960284415'],
        candidate_ordinary_credit=0, candidate_calibration_credit=0, project_admissions=0)
    immutable_json(package / 'final-series-declaration-native-exit-v6.json', declaration)
    print('Declared Git Town exact rc.6 series v6 from staged blobs; zero admission credit.')


if __name__ == '__main__':
    main()
