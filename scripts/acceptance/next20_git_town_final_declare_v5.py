"""Freeze Git Town's v5 final contract and staged harness blobs."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def freeze_json(path, value):
    path = path.resolve()
    expected = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode()
    if path.exists():
        if path.is_symlink() or path.read_bytes() != expected:
            raise ValueError('existing v5 intermediate freeze differs; preserve it: ' + str(path))
        return
    immutable_json(path, value)


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v5 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    old_catalog = json.loads((package / 'scenario-catalog-v3.json').read_text(encoding='utf-8'))
    catalog = dict(old_catalog)
    catalog['revision'] = 4
    catalog['supersedes'] = 'scenario-catalog-v3.json'
    catalog['revision_reason'] = (
        'Exact RC6 attempt 41956408435 exposed a 3-second cold-start timeout on Linux '
        'and a Windows Unicode command-line conversion boundary. N01 now declares a '
        '10-second bounded checkpoint. N15 preserves the first creation failure and '
        'tests selection of a host-seeded Unicode branch through the public TUI.')
    recipe_path = package / 'source-fixture-recipe-v2.json'
    freeze_json(recipe_path, dict(schema_version=1, project='git-town',
        source_pin='8d039892574d4852e1843020c31d423234042e78',
        base_fixture='fixtures/branch-repo',
        unicode_fixture='fixtures/branch-repo-unicode',
        unicode_branch='feat-\u00e9', initial_branch='main', remote_count=0,
        generated_by='next20_git_town_final_contracts.py',
        policy='Copy the exact host-generated synthetic repository and create one Unicode branch with local Git; no remote, credential, or user Git configuration.'))
    catalog['fixture_manifest_sha256'] = sha256(recipe_path)
    for row in catalog['scenarios']:
        if row['id'] == 'N15-create-unicode-branch':
            row['id'] = 'N15-select-unicode-branch'
            row['spec'] = 'N15-select-unicode-branch.json'
            row['user_task'] = 'Select a Unicode feature branch from the full-screen switcher.'
            row['precondition'] = ('Fresh copy of a pinned synthetic local repository with a '
                                   'host-generated Unicode feature branch; no remote or credentials.')
        row['spec_sha256'] = sha256(package / row['spec'])
    catalog_path = package / 'scenario-catalog-v4.json'
    freeze_json(catalog_path, catalog)

    cases = [dict(id=row['id'], spec=row['spec'], spec_sha256=row['spec_sha256'],
                  canonical_sha256=row['spec_sha256']) for row in catalog['scenarios']]
    scenarios_path = package / 'scenarios-native-exit-v2.json'
    freeze_json(scenarios_path, dict(schema_version=1, project='git-town',
        source_catalog='scenario-catalog-v4.json', source_catalog_sha256=sha256(catalog_path),
        cases=cases))
    inputs = {row['spec']: row['spec_sha256'] for row in catalog['scenarios']}
    inputs.update({
        'fixtures/branch-repo/README.md': sha256(package / 'fixtures/branch-repo/README.md'),
        'fixtures/branch-repo-unicode/README.md': sha256(package / 'fixtures/branch-repo-unicode/README.md'),
        'source-fixture-recipe-v2.json': sha256(recipe_path),
        'scenarios-native-exit-v2.json': sha256(scenarios_path),
    })
    freeze_path = package / 'development-test-freeze-native-exit-v2.json'
    freeze_json(freeze_path, dict(schema_version=1, project='git-town',
        status='frozen-for-private-candidate-series-v2', inputs=dict(sorted(inputs.items())),
        directories=['fixtures/branch-repo', 'fixtures/branch-repo-unicode'],
        scenarios_sha256=sha256(scenarios_path), scenario_catalog_sha256=sha256(catalog_path),
        fixture_manifest_sha256=sha256(recipe_path),
        positive_development_summary=dict(
            source_development_run='41947116665', independent_audit_run='41949100190',
            source_pin='8d039892574d4852e1843020c31d423234042e78', source_files=4533,
            unchanged_case_specs=18, revised_final_specs=2,
            scope='Historical source-development evidence applies to the prior v3 test contract only; both v4 revised contracts await exact-candidate execution.'),
        final_ordinary_credit=0))

    prior_path = package / 'final-series-declaration-native-exit-v4.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 4 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior final declaration is not preserved v4')
    declaration = dict(prior)
    declaration['revision'] = 5
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path),
        reason=('Attempt 41956408435 passed the hash gate and reached real candidate cases. '
                'Linux N01 exhausted its default 3-second checkpoint before output; Windows '
                'N15 exposed the target GitTown/Git argument Unicode conversion limit. V5 '
                'uses a bounded 10-second N01 checkpoint and replaces N15 with public TUI '
                'selection of a pre-seeded Unicode branch. The failed attempt remains zero-credit.'))
    declaration['canonical_test_freeze_sha256'] = sha256(freeze_path)
    declaration['scenario_catalog_sha256'] = sha256(catalog_path)
    declaration['scenario_catalog'] = catalog_path.name
    declaration['freeze_path'] = freeze_path.name
    declaration['harness_hash_policy'] = (
        'Hash staged Git index blob bytes; for .py, .ps1, .yml and .yaml normalize CRLF to LF before SHA-256. Runtime worktree files are normalized identically before comparison.')
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest()
        for name in prior['harness_files']
    }
    generator_name = 'scripts/acceptance/next20_git_town_final_declare_v5.py'
    declaration['harness_files'][generator_name] = hashlib.sha256(staged_bytes(generator_name)).hexdigest()
    declaration['revision_summary'] = dict(
        v5_catalog=catalog_path.name, v5_freeze=freeze_path.name,
        preserved_attempt='41956408435', candidate_ordinary_credit=0,
        candidate_calibration_credit=0, project_admissions=0)
    immutable_json(package / 'final-series-declaration-native-exit-v5.json', declaration)
    print('Declared Git Town exact rc.6 series v5 from staged harness blobs; zero admission credit.')


if __name__ == '__main__':
    main()
