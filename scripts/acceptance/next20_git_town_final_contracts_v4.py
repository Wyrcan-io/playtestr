"""Freeze Git Town v6 final cases after the v8 first-batch observations."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_sha(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('final contract input is not staged: ' + name)
    data = result.stdout
    if hashlib.sha256(data).hexdigest() != sha256(ROOT / name):
        raise ValueError('final contract worktree input differs from its staged blob: ' + name)
    return hashlib.sha256(data).hexdigest()


def freeze(path, value):
    if path.exists():
        if path.is_symlink() or json.loads(path.read_text(encoding='utf-8')) != value:
            raise ValueError('existing immutable contract differs; preserve it: ' + str(path))
        return
    immutable_json(path, value)


def main():
    package = DOC / 'git-town'
    previous_catalog_path = package / 'scenario-catalog-v5.json'
    catalog = json.loads(previous_catalog_path.read_text(encoding='utf-8'))
    catalog['revision'] = 6
    catalog['supersedes'] = previous_catalog_path.name
    catalog['previous_catalog'] = previous_catalog_path.name
    catalog['previous_catalog_sha256'] = sha256(previous_catalog_path)
    catalog['revision_reason'] = (
        'Final candidate attempt 41967210773 passed N01 and N02 on Linux, then N03 timed out at its implicit 3-second readiness bound. On Windows N15 was rejected as an invalid spec because Down is not a supported public key name, and checked deletion safely refused its unconfirmed cleanup. N03 now declares a 10-second bounded readiness checkpoint; N15 uses ArrowDown to select the visible Unicode row. The v8 attempt remains preserved with zero batch credit.')
    for row in catalog['scenarios']:
        row['spec_sha256'] = staged_sha('docs/validation/runner-readiness-next-twenty-project-pass/git-town/' + row['spec'])
    catalog_path = package / 'scenario-catalog-v6.json'
    freeze(catalog_path, catalog)

    cases = [dict(id=row['id'], spec=row['spec'], spec_sha256=row['spec_sha256'],
                  canonical_sha256=row['spec_sha256']) for row in catalog['scenarios']]
    scenarios_path = package / 'scenarios-native-exit-v4.json'
    freeze(scenarios_path, dict(schema_version=1, project='git-town',
        source_catalog=catalog_path.name, source_catalog_sha256=sha256(catalog_path),
        cases=cases))
    inputs = {row['spec']: row['spec_sha256'] for row in catalog['scenarios']}
    prior_freeze = json.loads((package / 'development-test-freeze-native-exit-v3.json').read_text(encoding='utf-8'))
    for name in ('fixtures/branch-repo/README.md', 'fixtures/branch-repo-unicode/README.md',
                 'source-fixture-recipe-v2.json'):
        digest = sha256(package / name)
        if name.startswith('fixtures/'):
            if prior_freeze['inputs'].get(name) != digest:
                raise ValueError('fixture seed differs from the prior immutable freeze: ' + name)
        else:
            staged_sha('docs/validation/runner-readiness-next-twenty-project-pass/git-town/' + name)
        inputs[name] = digest
    inputs[scenarios_path.name] = sha256(scenarios_path)
    freeze(package / 'development-test-freeze-native-exit-v4.json', dict(
        schema_version=1, project='git-town', status='frozen-for-private-candidate-series-v4',
        inputs=dict(sorted(inputs.items())),
        directories=['fixtures/branch-repo', 'fixtures/branch-repo-unicode'],
        scenarios_sha256=sha256(scenarios_path), scenario_catalog_sha256=sha256(catalog_path),
        fixture_manifest_sha256=sha256(package / 'source-fixture-recipe-v2.json'),
        positive_development_summary=dict(
            source_development_run='41947116665', independent_audit_run='41949100190',
            source_pin='8d039892574d4852e1843020c31d423234042e78', source_files=4533,
            unchanged_case_specs=17, revised_final_specs=3,
            scope='Historical source-development evidence applies to earlier contracts only; the v6 N02/N03 readiness and N15 key-name corrections require exact-candidate execution.'),
        final_ordinary_credit=0))

    prior_fault_path = package / 'fault-declaration-v6.json'
    fault = json.loads(prior_fault_path.read_text(encoding='utf-8'))
    fault['supersedes_for_future_execution'] = prior_fault_path.name
    fault['scenario_catalog'] = catalog_path.name
    for item in fault.get('declared_faults', []):
        spec = item.get('unchanged_spec')
        if spec:
            item['spec_sha256'] = staged_sha(
                'docs/validation/runner-readiness-next-twenty-project-pass/git-town/' + spec)
    fault['revision_reason'] = (
        'The exact-candidate case catalog advances to v6 for N03 readiness and Unicode key-name corrections. The three independent source faults still use the same reviewed public scenarios; their frozen spec hashes are updated to the exact new catalog bytes.')
    fault['execution_status'] = 'declaration only; hosted v6 final source-fault execution and independent audit pending'
    fault['admission_credit'] = 0
    freeze(package / 'fault-declaration-v7.json', fault)
    print('Frozen Git Town catalog v6, final input freeze v4, and fault declaration v7; zero admission credit.')


if __name__ == '__main__':
    main()
