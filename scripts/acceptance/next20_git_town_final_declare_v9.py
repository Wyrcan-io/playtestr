"""Bind final Git Town v9 to the corrected frozen v6 scenarios and staged harness."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v9 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v8.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 8 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v8')
    catalog_path = package / 'scenario-catalog-v6.json'
    fault_path = package / 'fault-declaration-v7.json'
    freeze_path = package / 'development-test-freeze-native-exit-v4.json'
    declaration = dict(prior)
    declaration['revision'] = 9
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=('Run 41967210773 launched 17 target cases: Linux N03 exceeded its implicit 3-second readiness timeout; Windows N15 was rejected before target launch because Down is not a public key name. The Windows cleanup verifier correctly refused deletion because the invalid-spec report could not confirm workspace cleanup. N03 now declares a 10-second bound and N15 uses ArrowDown. The attempt remains zero-credit.'))
    declaration['scenario_catalog'] = catalog_path.name
    declaration['scenario_catalog_sha256'] = sha256(catalog_path)
    declaration['fault_declaration_sha256'] = sha256(fault_path)
    declaration['canonical_test_freeze_sha256'] = sha256(freeze_path)
    declaration['freeze_path'] = freeze_path.name
    declaration['harness_hash_policy'] = (
        'Hash staged Git index blob bytes; for .py, .ps1, .yml and .yaml normalize CRLF to LF before SHA-256. Runtime worktree files are normalized identically before comparison.')
    harness = dict(prior['harness_files'])
    additions = [
        'scripts/acceptance/next20_git_town_final_declare_v9.py',
        'scripts/acceptance/next20_git_town_final_contracts_v4.py',
    ]
    for name in additions:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    declaration['scenario_alias_policy'] = (
        'Materialize host-contracts/scenarios.json as an exact byte copy of frozen scenarios-native-exit-v4.json, verify its SHA-256, and record the alias digest in the host contract freeze before the final journal reads it.')
    declaration['revision_summary'] = dict(
        v6_scenario_catalog='scenario-catalog-v6.json',
        v6_contract_freeze='development-test-freeze-native-exit-v4.json',
        preserved_failed_runs=['41953084178', '41954388734', '41955366681', '41956408435',
                               '41960284415', '41962045773', '41964820652', '41967210773'],
        candidate_ordinary_credit=0, candidate_calibration_credit=0, project_admissions=0)
    immutable_json(package / 'final-series-declaration-native-exit-v9.json', declaration)
    print('Declared Git Town exact rc.6 series v9 from staged blobs; zero admission credit.')


if __name__ == '__main__':
    main()
