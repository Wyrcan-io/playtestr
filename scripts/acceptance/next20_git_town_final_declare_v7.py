"""Bind the v7 exact-candidate run to staged harness blobs and frozen v4 cases."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v7 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v6.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 6 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v6')
    fault_path = package / 'fault-declaration-v5.json'
    catalog_path = package / 'scenario-catalog-v4.json'
    declaration = dict(prior)
    declaration['revision'] = 7
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=('Hosted run 41962045773 built the pinned source and installed the exact candidate, '
                'then the final journal refused before any target case because its generic '
                'scenarios.json alias was not materialized. V7 creates and hashes the alias from '
                'the frozen scenarios-native-exit-v2.json input, binds source-fault calibration '
                'to the revised v5 declaration and v4 scenario catalog. The stale automatic source '
                'matrix push trigger is disabled until its historical v3 contracts are re-versioned.'))
    declaration['scenario_catalog'] = catalog_path.name
    declaration['scenario_catalog_sha256'] = sha256(catalog_path)
    declaration['fault_declaration_sha256'] = sha256(fault_path)
    declaration['harness_hash_policy'] = (
        'Hash staged Git index blob bytes; for .py, .ps1, .yml and .yaml normalize CRLF to LF before SHA-256. Runtime worktree files are normalized identically before comparison.')
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest()
        for name in prior['harness_files']
    }
    declaration['harness_files']['scripts/acceptance/next20_git_town_final_declare_v7.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_git_town_final_declare_v7.py')).hexdigest()
    declaration['harness_files']['scripts/acceptance/test_next20_git_town_final_contracts.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/test_next20_git_town_final_contracts.py')).hexdigest()
    declaration['harness_files']['.github/workflows/runner-readiness-next20-git-town.yml'] = hashlib.sha256(
        staged_bytes('.github/workflows/runner-readiness-next20-git-town.yml')).hexdigest()
    declaration['scenario_alias_policy'] = (
        'Materialize host-contracts/scenarios.json as an exact byte copy of frozen scenarios-native-exit-v2.json, verify its SHA-256, and record the alias digest in the host contract freeze before the final journal reads it.')
    declaration['revision_summary'] = dict(
        v5_scenario_catalog='scenario-catalog-v4.json',
        v5_contract_freeze='development-test-freeze-native-exit-v2.json',
        preserved_failed_runs=['41953084178', '41954388734', '41955366681', '41956408435',
                               '41960284415', '41962045773'],
        candidate_ordinary_credit=0, candidate_calibration_credit=0, project_admissions=0)
    immutable_json(package / 'final-series-declaration-native-exit-v7.json', declaration)
    print('Declared Git Town exact rc.6 series v7 from staged blobs; zero admission credit.')


if __name__ == '__main__':
    main()
