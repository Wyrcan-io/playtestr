"""Freeze Git Town v7 final cases after the v9 observations."""
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
    previous_catalog_path = package / 'scenario-catalog-v6.json'
    catalog = json.loads(previous_catalog_path.read_text(encoding='utf-8'))
    catalog['revision'] = 7
    catalog['supersedes'] = previous_catalog_path.name
    catalog['previous_catalog'] = previous_catalog_path.name
    catalog['previous_catalog_sha256'] = sha256(previous_catalog_path)
    catalog['revision_reason'] = (
        'Final candidate attempt 41968702601 passed the v8 N03 and N15 corrections. Linux then timed out on N04 at the implicit 3-second bound; Windows passed 80 cases in four complete batches before the v3 viewport transform raised KeyError because width and height were omitted and should default to 80x24. All twenty frozen cases now declare a bounded 10-second step timeout, and the batch viewport transform uses public defaults. The v9 attempt remains preserved with zero candidate credit.')
    for row in catalog['scenarios']:
        row['spec_sha256'] = staged_sha('docs/validation/runner-readiness-next-twenty-project-pass/git-town/' + row['spec'])
    catalog_path = package / 'scenario-catalog-v7.json'
    freeze(catalog_path, catalog)

    cases = [dict(id=row['id'], spec=row['spec'], spec_sha256=row['spec_sha256'],
                  canonical_sha256=row['spec_sha256']) for row in catalog['scenarios']]
    scenarios_path = package / 'scenarios-native-exit-v5.json'
    freeze(scenarios_path, dict(schema_version=1, project='git-town',
        source_catalog=catalog_path.name, source_catalog_sha256=sha256(catalog_path),
        cases=cases))
    inputs = {row['spec']: row['spec_sha256'] for row in catalog['scenarios']}
    prior_freeze = json.loads((package / 'development-test-freeze-native-exit-v4.json').read_text(encoding='utf-8'))
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
    freeze(package / 'development-test-freeze-native-exit-v5.json', dict(
        schema_version=1, project='git-town', status='frozen-for-private-candidate-series-v5',
        inputs=dict(sorted(inputs.items())),
        directories=['fixtures/branch-repo', 'fixtures/branch-repo-unicode'],
        scenarios_sha256=sha256(scenarios_path), scenario_catalog_sha256=sha256(catalog_path),
        fixture_manifest_sha256=sha256(package / 'source-fixture-recipe-v2.json'),
        positive_development_summary=dict(
            source_development_run='41947116665', independent_audit_run='41949100190',
            source_pin='8d039892574d4852e1843020c31d423234042e78', source_files=4533,
            unchanged_case_specs=0, revised_final_specs=20,
            scope='Historical source-development evidence applies to earlier contracts only; the v7 10-second readiness bounds and viewport-transform compatibility require exact-candidate execution.'),
        final_ordinary_credit=0))

    prior_fault_path = package / 'fault-declaration-v7.json'
    fault = json.loads(prior_fault_path.read_text(encoding='utf-8'))
    fault['supersedes_for_future_execution'] = prior_fault_path.name
    fault['scenario_catalog'] = catalog_path.name
    for item in fault.get('declared_faults', []):
        spec = item.get('unchanged_spec')
        if spec:
            item['spec_sha256'] = staged_sha(
                'docs/validation/runner-readiness-next-twenty-project-pass/git-town/' + spec)
    fault['revision_reason'] = (
        'The exact-candidate case catalog advances to v7 for bounded readiness and viewport-transform compatibility. The three independent source faults still use the same reviewed public scenarios; their frozen spec hashes are updated to the exact new catalog bytes.')
    fault['execution_status'] = 'declaration only; hosted v7 final source-fault execution and independent audit pending'
    fault['admission_credit'] = 0
    freeze(package / 'fault-declaration-v8.json', fault)
    print('Frozen Git Town catalog v7, final input freeze v5, and fault declaration v8; zero admission credit.')


if __name__ == '__main__':
    main()
